from __future__ import annotations

import argparse
import json
import math
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from public_benchmark_knowledge_model import build_mechanism_edge_features, build_public_benchmark_knowledge_model


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PUBLIC_DATASET_ROOT = PROJECT_ROOT / "knowledge_exports" / "public_datasets"
DEFAULT_READY_DATASET_ROOT = PROJECT_ROOT / "knowledge_exports" / "public_benchmark_ready"
DEFAULT_TEP_LEGACY_DIR = (
    PROJECT_ROOT
    / "\u6570\u636e\u96c6"
    / "\u6d41\u7a0b\u5de5\u4e1a\u7530\u7eb3\u897f\u5316\u5de5\u8fc7\u7a0b\u6545\u969c\u8bca\u65ad\u4e0e\u5206\u6790\u6570\u636e\u96c6"
)


SKAB_LAGGED_MECHANISM_EDGES: list[dict[str, Any]] = [
    {"source": "Current", "target": "Temperature", "lag": 2, "relation": "motor_load_heating", "reliability": 0.45},
    {"source": "Voltage", "target": "Current", "lag": 1, "relation": "drive_electrical_response", "reliability": 0.35},
    {"source": "Volume Flow RateRMS", "target": "Pressure", "lag": 1, "relation": "flow_pressure_coupling", "reliability": 0.45},
    {"source": "Pressure", "target": "Volume Flow RateRMS", "lag": 1, "relation": "hydraulic_feedback", "reliability": 0.35},
    {"source": "Accelerometer1RMS", "target": "Volume Flow RateRMS", "lag": 2, "relation": "mechanical_vibration_flow", "reliability": 0.30},
]

SKAB_LLM_MECHANISM_EDGE_CANDIDATES: list[dict[str, Any]] = [
    {"source": "Current", "target": "Volume Flow RateRMS", "lag": 2, "relation": "pump_load_flow_response", "reliability": 0.25},
    {"source": "Temperature", "target": "Thermocouple", "lag": 3, "relation": "thermal_transfer", "reliability": 0.25},
    {"source": "Pressure", "target": "Accelerometer1RMS", "lag": 2, "relation": "hydraulic_vibration_response", "reliability": 0.20},
]


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _rglob_files(path: Path, pattern: str) -> list[Path]:
    """Return recursive matches without dropping deep Windows paths."""
    root = Path(path)
    search_root = Path(_fs_path(root)) if os.name == "nt" else root
    files = list(search_root.rglob(pattern))
    if os.name != "nt":
        return files
    normal_prefix = "\\\\?\\"
    return [Path(str(file)[len(normal_prefix) :]) if str(file).startswith(normal_prefix) else file for file in files]


def _softmax_logits(logits: np.ndarray) -> np.ndarray:
    z = np.asarray(logits, dtype=float)
    z = z - np.max(z, axis=1, keepdims=True)
    exp_z = np.exp(np.clip(z, -60.0, 60.0))
    denom = np.sum(exp_z, axis=1, keepdims=True)
    return exp_z / np.where(denom > 0.0, denom, 1.0)


def apply_plain_logit_fusion(
    base_proba: Sequence[Sequence[float]] | np.ndarray,
    evidence_proba: Sequence[Sequence[float]] | np.ndarray,
    *,
    weight: float,
) -> np.ndarray:
    base = np.asarray(base_proba, dtype=float)
    evidence = np.asarray(evidence_proba, dtype=float)
    if base.shape != evidence.shape or base.ndim != 2:
        raise ValueError("base_proba and evidence_proba must be same-shaped 2-D arrays")
    logits = np.log(np.clip(base, 1e-8, 1.0)) + float(weight) * np.log(np.clip(evidence, 1e-8, 1.0))
    return _softmax_logits(logits)


def apply_selective_logit_correction(
    base_proba: Sequence[Sequence[float]] | np.ndarray,
    evidence_proba: Sequence[Sequence[float]] | np.ndarray,
    *,
    weight: float,
    confidence_threshold: float = 0.7,
    top_k: int = 2,
) -> np.ndarray:
    base = np.asarray(base_proba, dtype=float)
    evidence = np.asarray(evidence_proba, dtype=float)
    if base.shape != evidence.shape or base.ndim != 2:
        raise ValueError("base_proba and evidence_proba must be same-shaped 2-D arrays")
    if float(weight) <= 0.0:
        return base.copy()
    base_conf = np.max(base, axis=1)
    base_pred = np.argmax(base, axis=1)
    evidence_pred = np.argmax(evidence, axis=1)
    k = max(1, min(int(top_k), base.shape[1]))
    topk = np.argpartition(-base, kth=k - 1, axis=1)[:, :k]
    candidate_match = np.any(topk == evidence_pred[:, None], axis=1)
    agrees = evidence_pred == base_pred
    gate = ((base_conf < float(confidence_threshold)) & candidate_match) | agrees
    logits = np.log(np.clip(base, 1e-8, 1.0))
    if np.any(gate):
        logits[gate] += float(weight) * np.log(np.clip(evidence[gate], 1e-8, 1.0))
    return _softmax_logits(logits)


def summarize_classification(
    y_true: Sequence[int] | np.ndarray,
    proba: np.ndarray,
    *,
    positive_threshold: float | None = None,
) -> dict[str, float]:
    y = np.asarray(y_true, dtype=int).reshape(-1)
    p = np.asarray(proba, dtype=float)
    if p.ndim == 1:
        p = np.vstack([1.0 - p, p]).T
    if positive_threshold is not None and p.shape[1] == 2:
        pred = (p[:, 1] >= float(positive_threshold)).astype(int)
    else:
        pred = np.argmax(p, axis=1)
    average = "binary" if len(np.unique(y)) <= 2 and set(np.unique(y)).issubset({0, 1}) else "macro"
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "macro_precision": float(precision_score(y, pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y, pred, average="macro", zero_division=0)),
        "positive_f1": float(f1_score(y, pred, average=average, zero_division=0)),
        "positive_precision": float(precision_score(y, pred, average=average, zero_division=0)),
        "positive_recall": float(recall_score(y, pred, average=average, zero_division=0)),
    }


def _score_for_tuning(y: np.ndarray, proba: np.ndarray) -> float:
    metrics = summarize_classification(y, proba)
    return float(metrics["macro_f1"] + 0.5 * metrics["positive_recall"])


def tune_selective_correction(
    y_val: Sequence[int] | np.ndarray,
    base_proba: Sequence[Sequence[float]] | np.ndarray,
    evidence_proba: Sequence[Sequence[float]] | np.ndarray,
    *,
    weight_grid: Sequence[float] | None = None,
    confidence_threshold_grid: Sequence[float] | None = None,
    top_k_grid: Sequence[int] | None = None,
    allow_plain: bool = True,
    prefer_gated_on_tie: bool = True,
) -> dict[str, Any]:
    y = np.asarray(y_val, dtype=int).reshape(-1)
    base = np.asarray(base_proba, dtype=float)
    evidence = np.asarray(evidence_proba, dtype=float)
    weight_grid = list(weight_grid or [0.0, 0.1, 0.25, 0.5, 1.0])
    confidence_threshold_grid = list(confidence_threshold_grid or [0.55, 0.65, 0.75, 0.85])
    top_k_grid = list(top_k_grid or [1, 2])
    baseline_score = _score_for_tuning(y, base)
    best: dict[str, Any] = {"mode": "none", "weight": 0.0, "score": float(baseline_score)}
    rows: list[dict[str, Any]] = []
    for raw_weight in weight_grid:
        weight = float(raw_weight)
        if bool(allow_plain):
            candidate = apply_plain_logit_fusion(base, evidence, weight=weight)
            score = _score_for_tuning(y, candidate)
            row = {"mode": "plain", "weight": weight, "score": float(score)}
            rows.append(row)
            if score > float(best["score"]):
                best = row
        for raw_threshold in confidence_threshold_grid:
            for raw_topk in top_k_grid:
                threshold = float(raw_threshold)
                topk = int(raw_topk)
                candidate = apply_selective_logit_correction(base, evidence, weight=weight, confidence_threshold=threshold, top_k=topk)
                score = _score_for_tuning(y, candidate)
                row = {"mode": "gated", "weight": weight, "confidence_threshold": threshold, "top_k": topk, "score": float(score)}
                rows.append(row)
                tie = abs(score - float(best["score"])) <= 1e-12
                if score > float(best["score"]) or (tie and bool(prefer_gated_on_tie) and weight > 0.0 and best.get("mode") != "gated"):
                    best = row
    rows.sort(key=lambda item: -float(item["score"]))
    return {**best, "baseline_score": float(baseline_score), "top_candidates": rows[:12]}


def tune_binary_threshold(
    y_true: Sequence[int] | np.ndarray,
    proba_or_scores: np.ndarray,
    *,
    positive_recall_weight: float = 0.0,
) -> float:
    y = np.asarray(y_true, dtype=int).reshape(-1)
    arr = np.asarray(proba_or_scores, dtype=float)
    scores = arr[:, 1] if arr.ndim == 2 else arr.reshape(-1)
    best_threshold = 0.5
    best_score = -1.0
    for threshold in np.linspace(0.05, 0.95, 91):
        pred = (scores >= threshold).astype(int)
        f1 = f1_score(y, pred, zero_division=0)
        rec = recall_score(y, pred, zero_division=0)
        score = float(f1 + float(positive_recall_weight) * rec)
        if score > best_score:
            best_score = score
            best_threshold = float(threshold)
    return float(best_threshold)


def _fit_extra_trees(
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    *,
    seed: int,
    n_estimators: int,
    max_depth: int | None,
) -> Any:
    clf = ExtraTreesClassifier(
        n_estimators=int(n_estimators),
        max_depth=max_depth,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=int(seed),
        n_jobs=-1,
    )
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), clf).fit(x_train, y_train)


def _predict_proba_aligned(model: Any, x: pd.DataFrame, classes: Sequence[int]) -> np.ndarray:
    raw = np.asarray(model.predict_proba(x), dtype=float)
    last_step = model.steps[-1][1] if hasattr(model, "steps") else model
    model_classes = np.asarray(getattr(last_step, "classes_", np.arange(raw.shape[1])), dtype=int)
    out = np.zeros((len(x), len(classes)), dtype=float)
    class_to_idx = {int(c): i for i, c in enumerate(classes)}
    for raw_idx, cls in enumerate(model_classes):
        if int(cls) in class_to_idx:
            out[:, class_to_idx[int(cls)]] = raw[:, raw_idx]
    row_sum = out.sum(axis=1, keepdims=True)
    return out / np.where(row_sum > 0.0, row_sum, 1.0)


def _normal_residual_features(
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    x_other: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_train_imp = imputer.fit_transform(x_train)
    scaler.fit(x_train_imp)
    train_scaled = scaler.transform(x_train_imp)
    other_scaled = scaler.transform(imputer.transform(x_other))
    normal_mask = np.asarray(y_train, dtype=int) == 0
    center = np.nanmedian(train_scaled[normal_mask], axis=0) if np.any(normal_mask) else np.nanmedian(train_scaled, axis=0)
    train_resid = np.abs(train_scaled - center)
    other_resid = np.abs(other_scaled - center)
    missing_train = x_train.isna().astype(float).to_numpy()
    missing_other = x_other.isna().astype(float).to_numpy()
    cols = [f"resid_{c}" for c in x_train.columns] + [f"miss_{c}" for c in x_train.columns]
    return pd.DataFrame(np.hstack([train_resid, missing_train]), columns=cols), pd.DataFrame(np.hstack([other_resid, missing_other]), columns=cols)


def _numeric_feature_frame(df: pd.DataFrame, exclude: set[str]) -> pd.DataFrame:
    cols: list[str] = []
    out = pd.DataFrame(index=df.index)
    for col in df.columns:
        if col in exclude:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        if s.notna().mean() == 0.0 or s.nunique(dropna=True) <= 1:
            continue
        out[str(col)] = s
        cols.append(str(col))
    if not cols:
        raise ValueError("No numeric feature columns were found.")
    return out


def _stratified_val_split(indices: np.ndarray, y: np.ndarray, *, seed: int, val_fraction: float = 0.25) -> tuple[np.ndarray, np.ndarray]:
    idx = np.asarray(indices, dtype=np.int64)
    labels = np.asarray(y, dtype=int)[idx]
    stratify = labels if len(np.unique(labels)) > 1 and np.min(np.bincount(pd.factorize(labels)[0])) >= 2 else None
    train_idx, val_idx = train_test_split(idx, test_size=float(val_fraction), random_state=int(seed), stratify=stratify)
    return np.asarray(train_idx, dtype=np.int64), np.asarray(val_idx, dtype=np.int64)


def _run_anchor_residual_experiment(
    dataset: str,
    x: pd.DataFrame,
    y: np.ndarray,
    split: tuple[np.ndarray, np.ndarray, np.ndarray],
    *,
    seed: int,
    n_estimators: int,
    max_depth: int | None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    kg_feature_diagnostics: dict[str, Any] = {"status": "not_available", "generated_features": 0}
    y_original = np.asarray(y, dtype=int)
    original_classes = [int(c) for c in sorted(np.unique(y_original))]
    class_to_internal = {cls: i for i, cls in enumerate(original_classes)}
    y_arr = np.asarray([class_to_internal[int(value)] for value in y_original], dtype=int)
    train_idx, val_idx, test_idx = [np.asarray(part, dtype=np.int64) for part in split]
    classes = [int(c) for c in sorted(np.unique(y_arr))]
    x_train, y_train = x.iloc[train_idx].reset_index(drop=True), y_arr[train_idx]
    x_val, y_val = x.iloc[val_idx].reset_index(drop=True), y_arr[val_idx]
    x_test, y_test = x.iloc[test_idx].reset_index(drop=True), y_arr[test_idx]
    main = _fit_extra_trees(x_train, y_train, seed=int(seed), n_estimators=n_estimators, max_depth=max_depth)
    base_val = _predict_proba_aligned(main, x_val, classes)
    base_test = _predict_proba_aligned(main, x_test, classes)
    resid_train, resid_val = _normal_residual_features(x_train, y_train, x_val)
    _resid_train_again, resid_test = _normal_residual_features(x_train, y_train, x_test)
    evidence_train = resid_train
    evidence_val_features = resid_val
    evidence_test_features = resid_test
    try:
        kg_features, kg_feature_diagnostics = build_mechanism_edge_features(dataset, x)
        if not kg_features.empty:
            evidence_train = pd.concat([resid_train.reset_index(drop=True), kg_features.iloc[train_idx].reset_index(drop=True)], axis=1)
            evidence_val_features = pd.concat([resid_val.reset_index(drop=True), kg_features.iloc[val_idx].reset_index(drop=True)], axis=1)
            evidence_test_features = pd.concat([resid_test.reset_index(drop=True), kg_features.iloc[test_idx].reset_index(drop=True)], axis=1)
            kg_feature_diagnostics = {**kg_feature_diagnostics, "status": "evidence_added"}
        else:
            kg_feature_diagnostics = {**kg_feature_diagnostics, "status": "empty"}
    except Exception as exc:
        kg_feature_diagnostics = {"status": "skipped", "reason": str(exc), "generated_features": 0}
    residual_head = _fit_extra_trees(evidence_train, y_train, seed=int(seed) + 101, n_estimators=max(80, n_estimators // 2), max_depth=8)
    evidence_val = _predict_proba_aligned(residual_head, evidence_val_features, classes)
    evidence_test = _predict_proba_aligned(residual_head, evidence_test_features, classes)
    tuning = tune_selective_correction(y_val, base_val, evidence_val)
    plain_test = apply_plain_logit_fusion(base_test, evidence_test, weight=float(tuning.get("weight", 0.0)))
    if tuning.get("mode") == "gated":
        final_test = apply_selective_logit_correction(
            base_test,
            evidence_test,
            weight=float(tuning.get("weight", 0.0)),
            confidence_threshold=float(tuning.get("confidence_threshold", 0.7) or 0.7),
            top_k=int(tuning.get("top_k", 2) or 2),
        )
    elif tuning.get("mode") == "plain":
        final_test = plain_test
    else:
        final_test = base_test
    run = {
        "dataset": dataset,
        "seed": int(seed),
        "n_samples": int(len(y_arr)),
        "n_features": int(x.shape[1]),
        "n_evidence_features": int(evidence_train.shape[1]),
        "n_classes": int(len(classes)),
        "knowledge_feature_diagnostics": kg_feature_diagnostics,
        "class_id_mapping": {str(internal): int(original) for internal, original in enumerate(original_classes)},
        "train_size": int(len(train_idx)),
        "val_size": int(len(val_idx)),
        "test_size": int(len(test_idx)),
        "class_distribution": {str(int(k)): int(v) for k, v in pd.Series(y_original).value_counts().sort_index().items()},
        "main": summarize_classification(y_test, base_test),
        "plain_residual_fusion": summarize_classification(y_test, plain_test),
        "ugmc_selective_correction": summarize_classification(y_test, final_test),
        "tuning": tuning,
    }
    if extra:
        run.update(dict(extra))
    return run


def _write_ready_dataset(
    name: str,
    x: pd.DataFrame,
    y: pd.DataFrame,
    *,
    output_dir: Path,
    summary: Mapping[str, Any],
) -> None:
    out = Path(output_dir) / name
    out.mkdir(parents=True, exist_ok=True)
    x.to_csv(_fs_path(out / "X_process_features.csv"), index=False, encoding="utf-8-sig")
    y.to_csv(_fs_path(out / "y_labels.csv"), index=False, encoding="utf-8-sig")
    key_cols = [col for col in ("record_id", "run_id", "subset", "unit", "cycle") if col in x.columns and col in y.columns]
    if key_cols:
        xy = y.merge(x, on=key_cols, how="left")
    else:
        xy = pd.concat([y.reset_index(drop=True), x.reset_index(drop=True)], axis=1)
    xy.to_csv(_fs_path(out / "xy_public_benchmark.csv"), index=False, encoding="utf-8-sig")
    with open(_fs_path(out / "dataset_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(summary), fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    try:
        build_public_benchmark_knowledge_model(
            name,
            x,
            y,
            output_dir=out / "knowledge_model",
            summary=summary,
        )
    except Exception as exc:
        with open(_fs_path(out / "knowledge_model_error.json"), "w", encoding="utf-8") as fh:
            json.dump({"status": "error", "message": str(exc)}, fh, ensure_ascii=False, indent=2)
            fh.write("\n")


def _find_file(root: Path, filename: str) -> Path:
    hits = sorted(Path(root).rglob(filename))
    if not hits:
        raise FileNotFoundError(f"{filename} not found under {root}")
    return hits[0]


def _find_files(root: Path, pattern: str) -> list[Path]:
    return sorted(Path(root).rglob(pattern))


def load_secom_dataset(dataset_root: Path) -> tuple[pd.DataFrame, np.ndarray]:
    root = Path(dataset_root)
    data_path = root / "secom" / "raw" / "secom.data"
    label_path = root / "secom" / "raw" / "secom_labels.data"
    if not data_path.exists() or not label_path.exists():
        raise FileNotFoundError(f"SECOM files not found under {root}")
    x = pd.read_csv(data_path, sep=r"\s+", header=None, na_values=["NaN", "nan", "?"])
    labels = pd.read_csv(label_path, sep=r"\s+", header=None)
    y_raw = labels.iloc[:, 0].to_numpy(dtype=int)
    y = (y_raw == 1).astype(np.int64)
    x.columns = [f"s{i:03d}" for i in range(x.shape[1])]
    return x, y


def _load_tep_ready(dataset_root: Path, ready_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    from build_tep_fault_dataset import build_tep_fault_dataset

    dataset_dir = PROJECT_ROOT / "knowledge_exports" / "tep_fault_diagnosis_dataset"
    xy_path = dataset_dir / "xy_quality_traceability.csv"
    if not xy_path.exists():
        input_dir = DEFAULT_TEP_LEGACY_DIR
        if not input_dir.exists():
            input_dir = Path(dataset_root) / "tep" / "raw" / "extracted"
        build_tep_fault_dataset(input_dir=input_dir, output_dir=dataset_dir)
    x = pd.read_csv(dataset_dir / "X_process_features.csv", low_memory=False)
    y = pd.read_csv(dataset_dir / "y_quality_label.csv", low_memory=False)
    features = _numeric_feature_frame(x, exclude={"record_id"})
    labels = pd.to_numeric(y["event_quality_class_id"], errors="coerce").fillna(0).astype(int).to_numpy()
    _write_ready_dataset(
        "tep",
        pd.concat([x[["record_id"]], features], axis=1),
        y,
        output_dir=ready_root,
        summary={"source": str(dataset_dir), "task": "tep_22_class_fault_diagnosis", "n_rows": int(len(y)), "n_features": int(features.shape[1])},
    )
    return features, y, labels


def _run_tep(dataset_root: Path, ready_root: Path, output_path: Path, *, seeds: Sequence[int], n_estimators: int, max_depth: int | None) -> dict[str, Any]:
    x, meta, y = _load_tep_ready(dataset_root, ready_root)
    train_all = np.flatnonzero(meta["split_role"].astype(str).eq("train").to_numpy())
    test_idx = np.flatnonzero(meta["split_role"].astype(str).eq("test").to_numpy())
    runs = []
    for seed in seeds:
        train_idx, val_idx = _stratified_val_split(train_all, y, seed=int(seed), val_fraction=0.2)
        runs.append(_run_anchor_residual_experiment("tep", x, y, (train_idx, val_idx, test_idx), seed=int(seed), n_estimators=n_estimators, max_depth=max_depth))
    result = {"status": "ok", "task": "public_benchmark_tep", "runs": runs}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def _read_hydraulic_matrix(path: Path) -> pd.DataFrame:
    return pd.read_csv(_fs_path(path), sep=r"\s+", header=None)


def _load_hydraulic_ready(dataset_root: Path, ready_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = Path(dataset_root) / "hydraulic" / "raw" / "extracted"
    profile_path = _find_file(root, "profile.txt")
    profile = pd.read_csv(_fs_path(profile_path), sep=r"\s+", header=None)
    profile.columns = ["cooler", "valve", "internal_pump_leakage", "hydraulic_accumulator", "stable_flag"][: profile.shape[1]]
    sensor_files = [p for p in _find_files(root, "*.txt") if p.name.lower() not in {"profile.txt", "description.txt", "documentation.txt"}]
    feature_parts: list[pd.DataFrame] = []
    for path in sensor_files:
        matrix = _read_hydraulic_matrix(path)
        if len(matrix) != len(profile):
            continue
        prefix = path.stem.replace("-", "_")
        vals = matrix.apply(pd.to_numeric, errors="coerce")
        part = pd.DataFrame(
            {
                f"{prefix}_mean": vals.mean(axis=1),
                f"{prefix}_std": vals.std(axis=1),
                f"{prefix}_min": vals.min(axis=1),
                f"{prefix}_max": vals.max(axis=1),
                f"{prefix}_last_minus_first": vals.iloc[:, -1] - vals.iloc[:, 0],
            }
        )
        feature_parts.append(part)
    if not feature_parts:
        raise FileNotFoundError(f"No hydraulic sensor matrices found under {root}")
    x = pd.concat(feature_parts, axis=1)
    x.insert(0, "record_id", [f"hydraulic_cycle_{i:04d}" for i in range(len(x))])
    y = profile.copy()
    y.insert(0, "record_id", x["record_id"])
    _write_ready_dataset(
        "hydraulic",
        x,
        y,
        output_dir=ready_root,
        summary={"source": str(root), "task": "hydraulic_four_target_component_state", "n_rows": int(len(y)), "n_features": int(x.shape[1] - 1)},
    )
    return _numeric_feature_frame(x, exclude={"record_id"}), y


def _run_hydraulic(dataset_root: Path, ready_root: Path, output_path: Path, *, seeds: Sequence[int], n_estimators: int, max_depth: int | None) -> dict[str, Any]:
    x, y_df = _load_hydraulic_ready(dataset_root, ready_root)
    target_cols = [c for c in ["cooler", "valve", "internal_pump_leakage", "hydraulic_accumulator"] if c in y_df.columns]
    runs: list[dict[str, Any]] = []
    for target in target_cols:
        y = pd.to_numeric(y_df[target], errors="coerce").fillna(0).astype(int).to_numpy()
        all_idx = np.arange(len(y))
        for seed in seeds:
            train_val, test_idx = train_test_split(all_idx, test_size=0.25, random_state=int(seed), stratify=y if len(np.unique(y)) > 1 else None)
            train_idx, val_idx = _stratified_val_split(train_val, y, seed=int(seed) + 17, val_fraction=0.25)
            runs.append(
                _run_anchor_residual_experiment(
                    "hydraulic",
                    x,
                    y,
                    (train_idx, val_idx, test_idx),
                    seed=int(seed),
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    extra={"target": str(target)},
                )
            )
    result = {"status": "ok", "task": "public_benchmark_hydraulic", "targets": target_cols, "runs": runs}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def _rul_to_stage(rul: np.ndarray, *, degraded_threshold: int = 125, critical_threshold: int = 40) -> np.ndarray:
    out = np.zeros(len(rul), dtype=np.int64)
    out[np.asarray(rul) <= degraded_threshold] = 1
    out[np.asarray(rul) <= critical_threshold] = 2
    return out


def _read_cmapss_table(path: Path) -> pd.DataFrame:
    df = pd.read_csv(_fs_path(path), sep=r"\s+", header=None)
    n = df.shape[1]
    cols = ["unit", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"] + [f"sensor_{i:02d}" for i in range(1, n - 4)]
    df.columns = cols[:n]
    return df.apply(pd.to_numeric, errors="coerce")


def _load_cmapss_ready(dataset_root: Path, ready_root: Path, subsets: Sequence[str]) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    root = Path(dataset_root) / "cmapss" / "raw" / "extracted"
    x_parts: list[pd.DataFrame] = []
    y_parts: list[pd.DataFrame] = []
    subset_to_id = {str(s): i for i, s in enumerate(subsets)}
    for subset in subsets:
        train_path = _find_file(root, f"train_{subset}.txt")
        test_path = _find_file(root, f"test_{subset}.txt")
        rul_path = _find_file(root, f"RUL_{subset}.txt")
        train = _read_cmapss_table(train_path)
        test = _read_cmapss_table(test_path)
        train_max = train.groupby("unit")["cycle"].transform("max")
        train_rul = train_max - train["cycle"]
        test_tail_rul = pd.read_csv(_fs_path(rul_path), sep=r"\s+", header=None).iloc[:, 0].to_numpy(dtype=float)
        test_max = test.groupby("unit")["cycle"].transform("max")
        unit_tail = {unit: test_tail_rul[i] for i, unit in enumerate(sorted(test["unit"].unique())) if i < len(test_tail_rul)}
        test_rul = (test_max - test["cycle"]) + test["unit"].map(unit_tail).astype(float)
        for split_role, df, rul in [("train", train, train_rul), ("test", test, test_rul)]:
            rows = df.copy()
            rows.insert(0, "subset_id", subset_to_id[str(subset)])
            rows.insert(0, "record_id", [f"{subset}_{split_role}_{int(u):03d}_{int(c):04d}" for u, c in zip(rows["unit"], rows["cycle"])])
            labels = pd.DataFrame(
                {
                    "record_id": rows["record_id"],
                    "subset": str(subset),
                    "split_role": split_role,
                    "unit": rows["unit"].astype(int),
                    "cycle": rows["cycle"].astype(int),
                    "rul": np.asarray(rul, dtype=float),
                    "degradation_stage_id": _rul_to_stage(np.asarray(rul, dtype=float)),
                }
            )
            x_parts.append(rows)
            y_parts.append(labels)
    x_all = pd.concat(x_parts, ignore_index=True)
    y_all = pd.concat(y_parts, ignore_index=True)
    features = _numeric_feature_frame(x_all, exclude={"record_id"})
    _write_ready_dataset(
        "cmapss",
        pd.concat([x_all[["record_id"]], features], axis=1),
        y_all,
        output_dir=ready_root,
        summary={"source": str(root), "task": "cmapss_degradation_stage_classification", "subsets": list(subsets), "n_rows": int(len(y_all)), "n_features": int(features.shape[1])},
    )
    return features, y_all, y_all["degradation_stage_id"].astype(int).to_numpy()


def _run_cmapss(dataset_root: Path, ready_root: Path, output_path: Path, *, seeds: Sequence[int], n_estimators: int, max_depth: int | None, subsets: Sequence[str]) -> dict[str, Any]:
    x, meta, y = _load_cmapss_ready(dataset_root, ready_root, subsets)
    train_all = np.flatnonzero(meta["split_role"].astype(str).eq("train").to_numpy())
    test_idx = np.flatnonzero(meta["split_role"].astype(str).eq("test").to_numpy())
    runs = []
    for seed in seeds:
        train_idx, val_idx = _stratified_val_split(train_all, y, seed=int(seed), val_fraction=0.2)
        runs.append(_run_anchor_residual_experiment("cmapss", x, y, (train_idx, val_idx, test_idx), seed=int(seed), n_estimators=n_estimators, max_depth=max_depth, extra={"subsets": list(subsets)}))
    result = {"status": "ok", "task": "public_benchmark_cmapss", "runs": runs}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def load_skab_dataset(dataset_root: Path) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    root = Path(dataset_root)
    candidates = [
        root / "skab" / "raw" / "extracted",
        root,
    ]
    expected_groups = {"anomaly-free", "other", "valve1", "valve2"}
    csv_files: list[Path] = []
    for candidate in candidates:
        if candidate.exists():
            all_csv_files = _rglob_files(candidate, "*.csv")
            csv_files = [p for p in all_csv_files if p.parent.name.lower() in expected_groups]
            if csv_files:
                break
    if not csv_files:
        raise FileNotFoundError(f"SKAB csv files not found under {root}")
    frames: list[pd.DataFrame] = []
    meta_parts: list[pd.DataFrame] = []
    for path in sorted(csv_files):
        try:
            df = pd.read_csv(_fs_path(path))
        except Exception:
            df = pd.read_csv(_fs_path(path), sep=";")
        if "anomaly" not in df.columns and len(df.columns) == 1:
            df = pd.read_csv(_fs_path(path), sep=";")
        rel = path.relative_to(root) if path.is_relative_to(root) else path.name
        run_group = str(path.parent.name)
        if "anomaly" not in df.columns:
            if run_group.lower() != "anomaly-free":
                continue
            df = df.copy()
            df["anomaly"] = 0
        if "changepoint" not in df.columns:
            df = df.copy()
            df["changepoint"] = 0
        run_id = f"{run_group}_{path.with_suffix('').name}"
        data = df.copy()
        data["sample_index"] = np.arange(len(data), dtype=np.int64)
        data["run_id"] = run_id
        data["run_group"] = run_group
        feature_cols = [
            col
            for col in data.columns
            if col not in {"datetime", "anomaly", "changepoint", "run_id", "run_group", "sample_index"}
            and pd.api.types.is_numeric_dtype(pd.to_numeric(data[col], errors="coerce"))
        ]
        features = data[feature_cols + ["run_id", "run_group", "sample_index"]].copy()
        for col in feature_cols:
            features[col] = pd.to_numeric(features[col], errors="coerce")
        frames.append(features)
        meta_parts.append(
            pd.DataFrame(
                {
                    "run_id": run_id,
                    "run_group": run_group,
                    "source_file": str(rel),
                    "sample_index": data["sample_index"].astype(int),
                    "anomaly": pd.to_numeric(data["anomaly"], errors="coerce").fillna(0).astype(int),
                    "changepoint": pd.to_numeric(data.get("changepoint", 0), errors="coerce").fillna(0).astype(int),
                }
            )
        )
    if not frames:
        raise FileNotFoundError(f"No valid SKAB files with anomaly column under {root}")
    x = pd.concat(frames, ignore_index=True)
    meta = pd.concat(meta_parts, ignore_index=True)
    y = meta["anomaly"].astype(int).to_numpy()
    return x, y, meta


def _load_skab_ready(dataset_root: Path, ready_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    x_raw, y, meta = load_skab_dataset(dataset_root)
    features = _numeric_feature_frame(x_raw, exclude={"run_id", "run_group", "sample_index"})
    x_out = pd.concat([meta[["run_id", "sample_index"]].reset_index(drop=True), features.reset_index(drop=True)], axis=1)
    y_out = meta.copy()
    y_out.insert(0, "record_id", [f"skab_{r}_{i:05d}" for r, i in zip(meta["run_id"], meta["sample_index"])])
    x_out.insert(0, "record_id", y_out["record_id"])
    _write_ready_dataset(
        "skab",
        x_out,
        y_out,
        output_dir=ready_root,
        summary={"source": str(dataset_root), "task": "skab_binary_anomaly_detection", "n_rows": int(len(y)), "n_features": int(features.shape[1])},
    )
    return features, meta, y


def split_skab_runs(meta: pd.DataFrame, *, seed: int, test_size: float = 0.30, val_fraction: float = 0.25) -> tuple[list[str], list[str], list[str]]:
    runs = np.array(sorted(meta["run_id"].astype(str).unique()), dtype=object)
    rng = np.random.default_rng(int(seed))
    rng.shuffle(runs)
    n_test = max(1, int(math.ceil(len(runs) * float(test_size))))
    test_runs = runs[:n_test]
    rest = runs[n_test:]
    n_val = max(1, int(math.ceil(len(rest) * float(val_fraction)))) if len(rest) > 1 else 0
    val_runs = rest[:n_val]
    train_runs = rest[n_val:]
    if len(train_runs) == 0 and len(rest) > 0:
        train_runs, val_runs = rest[:1], rest[1:]
    return list(map(str, train_runs)), list(map(str, val_runs)), list(map(str, test_runs))


def _run_skab(dataset_root: Path, ready_root: Path, output_path: Path, *, seeds: Sequence[int], n_estimators: int, max_depth: int | None) -> dict[str, Any]:
    x, meta, y = _load_skab_ready(dataset_root, ready_root)
    runs = []
    for seed in seeds:
        train_runs, val_runs, test_runs = split_skab_runs(meta, seed=int(seed), test_size=0.30, val_fraction=0.25)
        train_idx = np.flatnonzero(meta["run_id"].astype(str).isin(train_runs).to_numpy())
        val_idx = np.flatnonzero(meta["run_id"].astype(str).isin(val_runs).to_numpy())
        test_idx = np.flatnonzero(meta["run_id"].astype(str).isin(test_runs).to_numpy())
        runs.append(
            _run_anchor_residual_experiment(
                "skab",
                x,
                y,
                (train_idx, val_idx, test_idx),
                seed=int(seed),
                n_estimators=n_estimators,
                max_depth=max_depth,
                extra={"train_runs": train_runs, "val_runs": val_runs, "test_runs": test_runs},
            )
        )
    result = {"status": "ok", "task": "public_benchmark_skab", "runs": runs}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def build_skab_causal_sequence_windows(
    x_raw: pd.DataFrame,
    meta: pd.DataFrame | None = None,
    *,
    window_size: int = 32,
    include_valid_mask: bool = True,
) -> tuple[np.ndarray, list[str]]:
    feature_cols = [
        col
        for col in x_raw.columns
        if col not in {"run_id", "run_group", "sample_index"}
        and pd.api.types.is_numeric_dtype(pd.to_numeric(x_raw[col], errors="coerce"))
    ]
    values = x_raw[feature_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    w = max(2, int(window_size))
    n_channels = len(feature_cols) + (1 if include_valid_mask else 0)
    out = np.zeros((len(x_raw), w, n_channels), dtype=np.float32)
    group_meta = meta if meta is not None else x_raw
    for _run, group in pd.DataFrame({"idx": np.arange(len(x_raw)), "run_id": group_meta["run_id"].astype(str), "sample_index": group_meta["sample_index"]}).groupby("run_id", sort=False):
        idx = group.sort_values("sample_index")["idx"].to_numpy(dtype=np.int64)
        run_values = values[idx]
        for pos, row_idx in enumerate(idx):
            start = max(0, pos - w + 1)
            segment = run_values[start : pos + 1]
            valid = np.ones((len(segment), 1), dtype=np.float32)
            if len(segment) < w:
                pad_n = w - len(segment)
                pad = np.zeros((pad_n, len(feature_cols)), dtype=np.float32)
                segment = np.vstack([pad, segment])
                valid = np.vstack([np.zeros((pad_n, 1), dtype=np.float32), valid])
            if include_valid_mask:
                out[int(row_idx)] = np.hstack([segment[-w:], valid[-w:]])
            else:
                out[int(row_idx)] = segment[-w:]
    cols = list(map(str, feature_cols)) + (["valid_mask"] if include_valid_mask else [])
    return out, cols


def _scale_skab_sequence_windows(sequence_windows: np.ndarray, train_mask: np.ndarray, *, has_valid_mask: bool = True) -> np.ndarray:
    arr = np.asarray(sequence_windows, dtype=np.float32).copy()
    train = arr[np.asarray(train_mask, dtype=bool)]
    feature_end = arr.shape[2] - 1 if has_valid_mask else arr.shape[2]
    flat = train[:, :, :feature_end].reshape(-1, feature_end)
    scaler = StandardScaler().fit(flat)
    all_flat = arr[:, :, :feature_end].reshape(-1, feature_end)
    arr[:, :, :feature_end] = scaler.transform(all_flat).reshape(arr.shape[0], arr.shape[1], feature_end)
    return arr


def scale_skab_named_sequence_windows(
    windows: np.ndarray,
    feature_cols: Sequence[str],
    *,
    train_mask: np.ndarray,
    passthrough_cols: Sequence[str] = ("valid_mask",),
) -> np.ndarray:
    passthrough = set(map(str, passthrough_cols))
    scale_idx = [i for i, col in enumerate(feature_cols) if str(col) not in passthrough]
    if not scale_idx:
        return np.asarray(windows, dtype=np.float32)
    arr = np.asarray(windows, dtype=np.float32).copy()
    train = arr[np.asarray(train_mask, dtype=bool)][:, :, scale_idx].reshape(-1, len(scale_idx))
    scaler = StandardScaler().fit(train)
    flat = arr[:, :, scale_idx].reshape(-1, len(scale_idx))
    arr[:, :, scale_idx] = scaler.transform(flat).reshape(arr.shape[0], arr.shape[1], len(scale_idx))
    return arr


def build_skab_msfg_tcn_windows(
    base_windows: np.ndarray,
    feature_cols: Sequence[str],
    *_args: Any,
    fused_edges: Sequence[Mapping[str, Any]] | None = None,
    **_kwargs: Any,
) -> tuple[np.ndarray, list[str], dict[str, Any]]:
    base = np.asarray(base_windows, dtype=np.float32)
    cols = list(map(str, feature_cols))
    feature_index = {name: idx for idx, name in enumerate(cols)}
    edge_channels: list[np.ndarray] = []
    edge_cols: list[str] = []
    used_edges: list[dict[str, Any]] = []
    for raw_edge in list(fused_edges or []):
        edge = dict(raw_edge)
        source = str(edge.get("source", "")).strip()
        target = str(edge.get("target", "")).strip()
        if source not in feature_index or target not in feature_index or source == target:
            continue
        source_idx = int(feature_index[source])
        target_idx = int(feature_index[target])
        if cols[source_idx] == "valid_mask" or cols[target_idx] == "valid_mask":
            continue
        lag = max(0, int(edge.get("lag", 0) or 0))
        reliability = float(edge.get("reliability", 1.0) or 1.0)
        source_series = base[:, :, source_idx]
        if lag > 0:
            shifted_source = np.zeros_like(source_series)
            shifted_source[:, lag:] = source_series[:, :-lag]
        else:
            shifted_source = source_series
        target_series = base[:, :, target_idx]
        channel = (target_series - shifted_source) * np.float32(max(0.0, reliability))
        edge_channels.append(channel[:, :, None].astype(np.float32))
        safe_source = source.replace(" ", "_")
        safe_target = target.replace(" ", "_")
        edge_cols.append(f"edge_{safe_source}_to_{safe_target}_lag{lag}")
        used_edges.append(
            {
                "source": source,
                "target": target,
                "lag": lag,
                "reliability": reliability,
            }
        )
    if edge_channels:
        out = np.concatenate([base] + edge_channels, axis=2).astype(np.float32)
    else:
        out = base.astype(np.float32)
    return out, cols + edge_cols, {
        "n_fused_edges": len(list(fused_edges or [])),
        "n_used_edges": len(used_edges),
        "edge_feature_cols": edge_cols,
        "used_edges": used_edges,
    }


def build_skab_time_context_sequence_windows(
    _y_train: np.ndarray,
    _meta_train: pd.DataFrame,
    meta_all: pd.DataFrame,
    *,
    window_size: int = 32,
) -> tuple[np.ndarray, list[str], dict[str, Any]]:
    n = len(meta_all)
    arr = np.zeros((n, max(2, int(window_size)), 2), dtype=np.float32)
    idx = pd.to_numeric(meta_all["sample_index"], errors="coerce").fillna(0).to_numpy(dtype=float)
    if idx.max() > 0:
        idx = idx / max(1.0, float(idx.max()))
    arr[:, :, 0] = idx[:, None]
    arr[:, :, 1] = 1.0
    return arr, ["normalized_sample_index", "valid_mask"], {"mode": "time_context"}


def build_skab_data_lag_edges(
    x_raw: pd.DataFrame,
    _meta: pd.DataFrame,
    feature_cols: Sequence[str],
    *,
    train_mask: np.ndarray,
    max_lag: int = 8,
    top_k: int = 24,
    min_abs_correlation: float = 0.25,
    min_pairs: int = 8,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    train = x_raw.loc[np.asarray(train_mask, dtype=bool), list(feature_cols)].apply(pd.to_numeric, errors="coerce")
    corr = train.corr().fillna(0.0)
    edges: list[dict[str, Any]] = []
    for source in corr.columns:
        for target in corr.columns:
            if source == target:
                continue
            value = float(corr.loc[source, target])
            if abs(value) >= float(min_abs_correlation) and len(train) >= int(min_pairs):
                edges.append({"source": str(source), "target": str(target), "lag": min(1, int(max_lag)), "relation": "data_correlation", "reliability": min(0.9, abs(value)), "correlation": value})
    edges.sort(key=lambda item: -float(item["reliability"]))
    return edges[: int(top_k)], {"candidate_edges": len(edges), "selected_edges": min(len(edges), int(top_k))}


def build_skab_positive_expert_edges(edges: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    return [dict(edge) for edge in (edges or SKAB_LAGGED_MECHANISM_EDGES)]


def prune_skab_expert_edges(
    expert_edges: Sequence[Mapping[str, Any]],
    *,
    llm_edges: Sequence[Mapping[str, Any]] | None = None,
    data_edges: Sequence[Mapping[str, Any]] | None = None,
    min_support_score: float = 0.18,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    support_pairs = {(str(e.get("source")), str(e.get("target"))) for e in list(llm_edges or []) + list(data_edges or [])}
    kept = []
    for edge in expert_edges:
        pair = (str(edge.get("source")), str(edge.get("target")))
        reliability = float(edge.get("reliability", 0.0))
        if pair in support_pairs or reliability >= float(min_support_score):
            kept.append(dict(edge))
    return kept, {"input_edges": len(list(expert_edges)), "kept_edges": len(kept), "min_support_score": float(min_support_score)}


def fuse_skab_multisource_graph_edges(
    *,
    expert_edges: Sequence[Mapping[str, Any]],
    llm_edges: Sequence[Mapping[str, Any]],
    data_edges: Sequence[Mapping[str, Any]],
    min_reliability: float = 0.10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for source_name, edges in [("expert", expert_edges), ("llm", llm_edges), ("data", data_edges)]:
        for edge in edges:
            pair = (str(edge.get("source")), str(edge.get("target")))
            current = by_pair.setdefault(pair, {**dict(edge), "sources": [], "reliability": 0.0})
            current["sources"].append(source_name)
            current["reliability"] = max(float(current.get("reliability", 0.0)), float(edge.get("reliability", 0.0)))
    fused = [edge for edge in by_pair.values() if float(edge.get("reliability", 0.0)) >= float(min_reliability)]
    fused.sort(key=lambda item: -float(item.get("reliability", 0.0)))
    return fused, {"input_edges": int(len(expert_edges) + len(llm_edges) + len(data_edges)), "fused_edges": len(fused), "min_reliability": float(min_reliability)}


def merge_skab_dynamic_llm_edges(
    base_edges: Sequence[Mapping[str, Any]],
    dynamic_edges: Sequence[Mapping[str, Any]] | None,
    *,
    max_dynamic_edges: int = 8,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    merged = [dict(edge) for edge in base_edges]
    merged.extend(dict(edge) for edge in list(dynamic_edges or [])[: int(max_dynamic_edges)])
    return merged, {"base_edges": len(base_edges), "dynamic_edges": len(list(dynamic_edges or [])[: int(max_dynamic_edges)])}


def build_skab_llm_graph_update_prompt(
    *,
    allowed_features: Sequence[str] | None = None,
    error_summary: Mapping[str, Any] | None = None,
    existing_edges: Sequence[Mapping[str, Any]] | None = None,
    max_edges: int = 8,
) -> str:
    payload = {
        "task": "SKAB sensor anomaly detection candidate-edge verification",
        "role": (
            "Act as a conditional mechanism verifier. Propose only candidate sensor edges that could explain "
            "the observed residual/error pattern. These edges are not final graph edges; downstream data support, "
            "counterfactual sensitivity, validation gain, and reliability admission decide whether they are used."
        ),
        "allowed_features": list(map(str, allowed_features or [])),
        "error_summary": dict(error_summary or {}),
        "existing_expert_or_llm_candidates": [dict(edge) for edge in list(existing_edges or [])],
        "constraints": {
            "max_edges": int(max_edges),
            "allowed_lag_range": [0, 12],
            "reliability_range": [0.0, 1.0],
            "do_not_invent_features": True,
            "avoid_duplicate_source_target_pairs": True,
            "prefer_edges_with_mechanism_or_residual_explanation": True,
        },
        "required_output_schema": {
            "edges": [
                {
                    "source": "one allowed feature name",
                    "target": "one allowed feature name",
                    "lag": "integer time lag, 0-12",
                    "relation": "short mechanism label",
                    "reliability": "float confidence before data validation",
                    "condition": "class, regime, residual pattern, or temporal context where this edge should be active",
                    "rationale": "one short sentence",
                }
            ]
        },
    }
    return (
        "Return only valid JSON. Do not include markdown fences or commentary.\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def parse_skab_llm_edge_proposals(
    text: str,
    *,
    allowed_features: Sequence[str] | None = None,
    max_edges: int = 8,
    max_lag: int = 12,
    reliability_cap: float = 0.72,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        data = json.loads(text)
    except Exception:
        return [], {"status": "parse_error", "accepted_edges": 0}
    if isinstance(data, dict):
        data = data.get("edges", [])
    allowed = set(map(str, allowed_features or []))
    edges: list[dict[str, Any]] = []
    rejected = 0
    seen: set[tuple[str, str]] = set()
    for raw in list(data):
        if not isinstance(raw, Mapping):
            rejected += 1
            continue
        edge = dict(raw)
        source = str(edge.get("source", "")).strip()
        target = str(edge.get("target", "")).strip()
        if not source or not target or source == target:
            rejected += 1
            continue
        if allowed and (source not in allowed or target not in allowed):
            rejected += 1
            continue
        pair = (source, target)
        if pair in seen:
            rejected += 1
            continue
        seen.add(pair)
        edge["source"] = source
        edge["target"] = target
        edge["lag"] = min(max(0, int(edge.get("lag", 0) or 0)), int(max_lag))
        edge["reliability"] = min(float(reliability_cap), max(0.0, float(edge.get("reliability", 0.0) or 0.0)))
        edges.append(edge)
        if len(edges) >= int(max_edges):
            break
    return edges, {"status": "ok", "accepted_edges": len(edges), "rejected_edges": rejected}


def _first_env_value(*names: str) -> tuple[str, str | None]:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value, name
    return "", None


def call_openai_skab_graph_proposer(
    prompt: str,
    *,
    model: str = "gpt-5.5",
    timeout_seconds: float = 45.0,
    base_url: str | None = None,
    api_key: str | None = None,
) -> tuple[str, dict[str, Any]]:
    resolved_base_url = str(
        base_url
        or os.environ.get("OPENAI_BASE_URL", "")
        or os.environ.get("N1N_BASE_URL", "")
        or "https://api.n1n.ai/v1"
    ).rstrip("/")
    resolved_key = str(api_key or "").strip()
    key_source = "argument" if resolved_key else None
    if not resolved_key:
        resolved_key, key_source = _first_env_value("OPENAI_API_KEY", "N1N_API_KEY", "LLM_API_KEY")
    diag_base = {
        "model": str(model),
        "base_url": resolved_base_url,
        "endpoint": "/chat/completions",
        "api_key_source": key_source,
    }
    if not resolved_key:
        return "", {"status": "not_configured", "reason": "missing_api_key", **diag_base}
    payload = {
        "model": str(model),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are validating candidate mechanism edges for SKAB anomaly detection. "
                    "Return only a compact JSON object with an `edges` array. Each edge must contain "
                    "`source`, `target`, `lag`, `relation`, and `reliability`."
                ),
            },
            {"role": "user", "content": str(prompt)},
        ],
        "temperature": 0,
        "max_tokens": 1200,
    }
    request = urllib.request.Request(
        f"{resolved_base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resolved_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=float(timeout_seconds)) as response:
            status_code = int(getattr(response, "status", 200))
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        return "", {
            "status": "http_error",
            "status_code": int(getattr(exc, "code", 0) or 0),
            "error_excerpt": body,
            **diag_base,
        }
    except Exception as exc:
        return "", {"status": "error", "reason": type(exc).__name__, "message": str(exc), **diag_base}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return "", {
            "status": "parse_error",
            "reason": str(exc),
            "status_code": status_code,
            "response_chars": len(raw),
            **diag_base,
        }
    content = ""
    choices = data.get("choices", []) if isinstance(data, Mapping) else []
    if choices and isinstance(choices[0], Mapping):
        message = choices[0].get("message", {})
        if isinstance(message, Mapping):
            content = str(message.get("content", "") or "")
        elif choices[0].get("text") is not None:
            content = str(choices[0].get("text") or "")
    return content, {
        "status": "ok" if content else "empty_response",
        "status_code": status_code,
        "response_chars": len(content),
        **diag_base,
    }


def summarize_skab_protocol_detection(
    y_true: Sequence[int] | np.ndarray,
    proba: np.ndarray,
    meta: pd.DataFrame,
    *,
    positive_threshold: float = 0.5,
    changepoint_window_steps: int = 60,
) -> dict[str, Any]:
    y = np.asarray(y_true, dtype=int).reshape(-1)
    p = np.asarray(proba, dtype=float)
    scores = p[:, 1] if p.ndim == 2 else p.reshape(-1)
    pred = (scores >= float(positive_threshold)).astype(int)
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    negatives = int(np.sum(y == 0))
    positives = int(np.sum(y == 1))
    binary = {
        "f1": float(f1_score(y, pred, zero_division=0)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "far_percent": float(100.0 * fp / max(1, negatives)),
        "mar_percent": float(100.0 * fn / max(1, positives)),
    }
    detected_runs = 0
    anomalous_runs = 0
    for run_id, group in meta.assign(_y=y, _pred=pred).groupby("run_id", sort=False):
        if int(group["_y"].max()) <= 0:
            continue
        anomalous_runs += 1
        first_anomaly = int(group.loc[group["_y"].eq(1), "sample_index"].min())
        limit = first_anomaly + int(changepoint_window_steps)
        hit = group[group["sample_index"].between(first_anomaly, limit)]["_pred"].max() > 0
        detected_runs += int(hit)
    point_adjusted_f1 = binary["f1"] if anomalous_runs == 0 else float(detected_runs / max(1, anomalous_runs))
    return {
        "binary": binary,
        "point_adjusted": {"f1": point_adjusted_f1, "detected_runs": int(detected_runs), "anomalous_runs": int(anomalous_runs)},
        "right_window_changepoint": {"window_steps": int(changepoint_window_steps), "detected_runs": int(detected_runs), "anomalous_runs": int(anomalous_runs)},
    }


def _run_secom(dataset_root: Path, output_path: Path, *, seeds: Sequence[int], n_estimators: int, max_depth: int | None) -> dict[str, Any]:
    x, y = load_secom_dataset(dataset_root)
    runs = []
    all_idx = np.arange(len(y))
    for seed in seeds:
        train_val, test_idx = train_test_split(all_idx, test_size=0.25, stratify=y, random_state=int(seed))
        train_idx, val_idx = _stratified_val_split(train_val, y, seed=int(seed) + 17, val_fraction=0.25)
        runs.append(_run_anchor_residual_experiment("secom", x, y, (train_idx, val_idx, test_idx), seed=int(seed), n_estimators=n_estimators, max_depth=max_depth))
    result = {"status": "ok", "task": "public_benchmark_secom", "runs": runs}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def _split_csv_ints(text: str) -> list[int]:
    return [int(x.strip()) for x in str(text).split(",") if x.strip()]


def _split_csv(text: str) -> list[str]:
    return [x.strip() for x in str(text).split(",") if x.strip()]


def run_dataset(
    dataset: str,
    *,
    dataset_root: Path,
    ready_root: Path,
    output_path: Path,
    seeds: Sequence[int],
    n_estimators: int,
    max_depth: int | None,
    cmapss_subsets: Sequence[str],
) -> dict[str, Any]:
    name = str(dataset).strip().lower()
    if name == "tep":
        return _run_tep(dataset_root, ready_root, output_path, seeds=seeds, n_estimators=n_estimators, max_depth=max_depth)
    if name == "skab":
        return _run_skab(dataset_root, ready_root, output_path, seeds=seeds, n_estimators=n_estimators, max_depth=max_depth)
    if name == "hydraulic":
        return _run_hydraulic(dataset_root, ready_root, output_path, seeds=seeds, n_estimators=n_estimators, max_depth=max_depth)
    if name == "cmapss":
        return _run_cmapss(dataset_root, ready_root, output_path, seeds=seeds, n_estimators=n_estimators, max_depth=max_depth, subsets=cmapss_subsets)
    if name == "secom":
        return _run_secom(dataset_root, output_path, seeds=seeds, n_estimators=n_estimators, max_depth=max_depth)
    raise ValueError(f"Unknown dataset: {dataset}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run public benchmark experiments for AAAI evidence.")
    parser.add_argument("--dataset-root", type=str, default=str(DEFAULT_PUBLIC_DATASET_ROOT))
    parser.add_argument("--ready-root", type=str, default=str(DEFAULT_READY_DATASET_ROOT))
    parser.add_argument("--dataset", type=str, choices=["tep", "skab", "hydraulic", "cmapss", "secom", "all"], default="tep")
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--seeds", type=str, default="42,43,44")
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=0)
    parser.add_argument("--cmapss-subsets", type=str, default="FD001,FD002,FD003,FD004")
    args = parser.parse_args()
    dataset_root = Path(args.dataset_root)
    ready_root = Path(args.ready_root)
    seeds = _split_csv_ints(args.seeds)
    max_depth = int(args.max_depth) if int(args.max_depth) > 0 else None
    datasets = ["tep", "skab", "hydraulic", "cmapss"] if args.dataset == "all" else [args.dataset]
    results: dict[str, Any] = {}
    for dataset in datasets:
        output = Path(args.output) if args.output and len(datasets) == 1 else PROJECT_ROOT / "knowledge_exports" / f"public_benchmark_{dataset}.json"
        result = run_dataset(
            dataset,
            dataset_root=dataset_root,
            ready_root=ready_root,
            output_path=output,
            seeds=seeds,
            n_estimators=int(args.n_estimators),
            max_depth=max_depth,
            cmapss_subsets=_split_csv(args.cmapss_subsets),
        )
        results[dataset] = result
        for run in result.get("runs", [])[: min(4, len(result.get("runs", [])))]:
            main_metrics = run["main"]
            final_metrics = run["ugmc_selective_correction"]
            suffix = f" target={run.get('target')}" if "target" in run else ""
            print(
                f"{dataset}{suffix} seed={run['seed']} main_macro={main_metrics['macro_f1']:.4f} "
                f"ugmc_macro={final_metrics['macro_f1']:.4f} mode={run['tuning'].get('mode')}"
            )
    if len(results) > 1:
        combined = PROJECT_ROOT / "knowledge_exports" / "public_benchmark_all_summary.json"
        combined.write_text(json.dumps({"status": "ok", "datasets": results}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
