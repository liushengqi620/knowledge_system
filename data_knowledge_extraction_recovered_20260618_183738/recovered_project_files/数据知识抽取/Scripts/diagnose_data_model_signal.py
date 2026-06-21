from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import CONFIG
from data_processing import load_and_process_data
from feature_extraction import base_feature_columns
from paper_defect_pipeline import (
    _binary_classification_diagnostics,
    _build_split_aware_event_supervision,
    _maybe_align_probability_direction,
    _select_threshold_val,
)
from temporal_encoder import encode_temporal_features_from_df


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _safe_auc(y: np.ndarray, proba: np.ndarray) -> float | None:
    if len(np.unique(y)) < 2:
        return None
    try:
        return float(roc_auc_score(y, proba))
    except ValueError:
        return None


def _time_split_indices(n: int, train_fraction: float = 0.60, val_fraction: float = 0.20) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n_train = max(1, int(round(n * train_fraction)))
    n_val = max(1, int(round(n * val_fraction)))
    if n_train + n_val >= n:
        n_train = max(1, int(n * 0.60))
        n_val = max(1, int(n * 0.20))
    idx = np.arange(n, dtype=np.int64)
    return idx[:n_train], idx[n_train:n_train + n_val], idx[n_train + n_val:]


def _build_feature_matrix(
    df: pd.DataFrame,
    feature_cols: list[str],
    cfg: dict[str, Any],
    feature_mode: str,
) -> np.ndarray:
    if feature_mode == "raw":
        return df[feature_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
    embedding = encode_temporal_features_from_df(df, feature_cols, cfg)
    return embedding.values.astype(np.float64)


def _models(seed: int, trees: int) -> dict[str, Any]:
    return {
        "logistic_balanced": Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        solver="lbfgs",
                        random_state=seed,
                    ),
                ),
            ]
        ),
        "random_forest_balanced": Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=trees,
                        max_depth=8,
                        min_samples_leaf=8,
                        class_weight="balanced_subsample",
                        random_state=seed,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "extra_trees_balanced": Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                (
                    "model",
                    ExtraTreesClassifier(
                        n_estimators=trees,
                        max_depth=8,
                        min_samples_leaf=8,
                        class_weight="balanced",
                        random_state=seed,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def _evaluate_one(
    *,
    df: pd.DataFrame,
    y: np.ndarray,
    idx_train: np.ndarray,
    idx_val: np.ndarray,
    idx_test: np.ndarray,
    feature_cols: list[str],
    cfg: dict[str, Any],
    feature_mode: str,
    label_mode: str,
    model_name: str,
    model: Any,
) -> dict[str, Any]:
    X = _build_feature_matrix(df, feature_cols, cfg, feature_mode)
    model.fit(X[idx_train], y[idx_train])
    proba_val = model.predict_proba(X[idx_val])[:, 1]
    proba_test = model.predict_proba(X[idx_test])[:, 1]
    proba_val, proba_test, direction_tag = _maybe_align_probability_direction(
        y[idx_val],
        proba_val,
        proba_test,
        "uncalibrated",
    )
    threshold, threshold_tag = _select_threshold_val(y[idx_val], proba_val, cfg)
    pred_test = (proba_test >= threshold).astype(np.int64)
    diag = _binary_classification_diagnostics(y[idx_test], pred_test, proba_test, threshold=threshold)
    return {
        "label_mode": label_mode,
        "feature_mode": feature_mode,
        "model": model_name,
        "train_size": int(len(idx_train)),
        "val_size": int(len(idx_val)),
        "test_size": int(len(idx_test)),
        "train_pos_rate": float(np.mean(y[idx_train] == 1)),
        "val_pos_rate": float(np.mean(y[idx_val] == 1)),
        "test_pos_rate": float(np.mean(y[idx_test] == 1)),
        "pr_auc_val": float(average_precision_score(y[idx_val], proba_val)),
        "pr_auc_test": float(average_precision_score(y[idx_test], proba_test)),
        "roc_auc_val": _safe_auc(y[idx_val], proba_val),
        "roc_auc_test": _safe_auc(y[idx_test], proba_test),
        "f1_test": float(f1_score(y[idx_test], pred_test, pos_label=1, zero_division=0)),
        "precision_test": float(diag["all_positive_baseline"]["precision"]) if False else None,
        "recall_test": float(diag["confusion_matrix"]["tp"] / max(diag["confusion_matrix"]["tp"] + diag["confusion_matrix"]["fn"], 1)),
        "specificity_test": diag.get("specificity"),
        "false_positive_rate_test": diag.get("false_positive_rate"),
        "balanced_accuracy_test": diag.get("balanced_accuracy"),
        "mcc_test": diag.get("mcc"),
        "predicted_positive_rate": diag.get("predicted_positive_rate"),
        "threshold": float(threshold),
        "threshold_tuning": threshold_tag,
        "direction": direction_tag,
        "confusion_matrix": diag.get("confusion_matrix"),
    }


def _prepare_label_view(
    df: pd.DataFrame,
    y_raw: np.ndarray,
    cfg: dict[str, Any],
    label_mode: str,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    idx_train_raw, idx_val_raw, idx_test_raw = _time_split_indices(len(df))
    if label_mode == "point":
        return df, y_raw, idx_train_raw, idx_val_raw, idx_test_raw, {"mode": "point_label"}
    out_df, out_y, idx_train, idx_val, idx_test, meta = _build_split_aware_event_supervision(
        df,
        y_raw,
        idx_train_raw,
        idx_val_raw,
        idx_test_raw,
        cfg,
    )
    return out_df, out_y, idx_train, idx_val, idx_test, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Fast data/model signal diagnostics for defect labels.")
    parser.add_argument("--max-rows", type=int, default=8000)
    parser.add_argument("--trees", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--label-modes", type=str, default="point,event")
    parser.add_argument("--feature-modes", type=str, default="raw,temporal")
    parser.add_argument("--threshold-objective", type=str, default="balanced_mcc")
    parser.add_argument("--enable-temporal-rolling", action="store_true")
    parser.add_argument("--enable-frequency", action="store_true")
    parser.add_argument("--output", type=str, default="knowledge_exports/signal_diagnostic.json")
    args = parser.parse_args()

    try:
        stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
        if callable(stdout_reconfigure):
            stdout_reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    cfg = dict(CONFIG)
    cfg["defect_threshold_objective"] = str(args.threshold_objective)
    cfg["paper_disable_temporal_rolling"] = not bool(args.enable_temporal_rolling)
    cfg["paper_disable_frequency_temporal"] = not bool(args.enable_frequency)
    cfg["llm_topology_enabled"] = False
    cfg["paper_method_enable_llm_prior"] = False
    cfg["training_visualization_enabled"] = False
    cfg["knowledge_state_enabled"] = False

    df = load_and_process_data(str(cfg.get("file_path")))
    if args.max_rows and args.max_rows > 0:
        df = df.head(int(args.max_rows)).copy()
    feature_cols = base_feature_columns(df)
    y_raw = pd.to_numeric(df["defect_label"], errors="coerce").fillna(0).astype(int).to_numpy()

    label_modes = [x.strip() for x in str(args.label_modes).split(",") if x.strip()]
    feature_modes = [x.strip() for x in str(args.feature_modes).split(",") if x.strip()]
    results: list[dict[str, Any]] = []
    label_meta: dict[str, Any] = {}
    for label_mode in label_modes:
        view_df, y, idx_train, idx_val, idx_test, meta = _prepare_label_view(df, y_raw, cfg, label_mode)
        label_meta[label_mode] = meta
        view_features = base_feature_columns(view_df)
        for feature_mode in feature_modes:
            for model_name, model in _models(seed=int(args.seed), trees=int(args.trees)).items():
                row = _evaluate_one(
                    df=view_df,
                    y=y,
                    idx_train=idx_train,
                    idx_val=idx_val,
                    idx_test=idx_test,
                    feature_cols=view_features,
                    cfg=cfg,
                    feature_mode=feature_mode,
                    label_mode=label_mode,
                    model_name=model_name,
                    model=model,
                )
                results.append(row)
                print(
                    f"{label_mode:5s} | {feature_mode:8s} | {model_name:22s} | "
                    f"PR-AUC={row['pr_auc_test']:.4f} ROC-AUC={row['roc_auc_test']:.4f} "
                    f"F1={row['f1_test']:.4f} MCC={row['mcc_test']:.4f} "
                    f"pred_pos={row['predicted_positive_rate']:.3f}"
                )

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": {
            "preferred_label_column": cfg.get("preferred_label_column"),
            "threshold_objective": cfg.get("defect_threshold_objective"),
            "max_rows": int(args.max_rows),
            "enable_temporal_rolling": bool(args.enable_temporal_rolling),
            "enable_frequency": bool(args.enable_frequency),
        },
        "label_meta": label_meta,
        "results": results,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = out_path.with_suffix(".summary.csv")
    pd.DataFrame(results).drop(columns=["confusion_matrix"], errors="ignore").to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"saved_to={out_path}")
    print(f"summary_saved_to={csv_path}")


if __name__ == "__main__":
    main()
