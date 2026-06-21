from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from hierarchical_edge_probe_admission import (
    THRESHOLDS,
    admit_edges_from_probe_results,
    build_frozen_tep_candidate_pool,
    build_probe_plan,
    evaluate_probe_row,
)
from public_benchmark_experiment import _fit_extra_trees, _predict_proba_aligned, _stratified_val_split


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEP_DATASET_DIR = PROJECT_ROOT / "knowledge_exports" / "tep_fault_diagnosis_dataset"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "hierarchical_edge_probe_admission"


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _load_tep_frames(dataset_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    x = pd.read_csv(_fs_path(Path(dataset_dir) / "X_process_features.csv"), low_memory=False)
    y = pd.read_csv(_fs_path(Path(dataset_dir) / "y_quality_label.csv"), low_memory=False)
    n = min(len(x), len(y))
    labels = pd.to_numeric(y.iloc[:n]["event_quality_class_id"], errors="coerce").fillna(0).astype(int).to_numpy()
    numeric_cols = []
    for col in x.columns:
        if str(col) == "record_id":
            continue
        values = pd.to_numeric(x.iloc[:n][col], errors="coerce")
        if values.notna().any() and values.nunique(dropna=True) > 1:
            numeric_cols.append(str(col))
    return x.iloc[:n][numeric_cols].reset_index(drop=True), y.iloc[:n].reset_index(drop=True), labels


def _subsample_stratified(indices: np.ndarray, labels: np.ndarray, *, max_rows: int | None, seed: int) -> np.ndarray:
    idx = np.asarray(indices, dtype=np.int64)
    if max_rows is None or int(max_rows) <= 0 or len(idx) <= int(max_rows):
        return idx
    rng = np.random.default_rng(int(seed))
    selected: list[int] = []
    classes = sorted(np.unique(labels[idx]).tolist())
    per_class = max(1, int(max_rows) // max(1, len(classes)))
    for cls in classes:
        cls_idx = idx[labels[idx] == int(cls)]
        take = min(len(cls_idx), per_class)
        if take:
            selected.extend(rng.choice(cls_idx, size=take, replace=False).tolist())
    if len(selected) < int(max_rows):
        rest = np.setdiff1d(idx, np.asarray(selected, dtype=np.int64), assume_unique=False)
        take = min(len(rest), int(max_rows) - len(selected))
        if take:
            selected.extend(rng.choice(rest, size=take, replace=False).tolist())
    return np.asarray(sorted(selected[: int(max_rows)]), dtype=np.int64)


def _group_indices(meta: pd.DataFrame) -> list[np.ndarray]:
    keys = [col for col in ("source_split", "source_file") if col in meta.columns]
    if not keys:
        return [np.arange(len(meta), dtype=np.int64)]
    groups: list[np.ndarray] = []
    for _name, group in meta.reset_index().groupby(keys, sort=False):
        idx = group["index"].to_numpy(dtype=np.int64)
        if "sample_index" in meta.columns:
            order = pd.to_numeric(meta.iloc[idx]["sample_index"], errors="coerce").fillna(0).to_numpy()
            idx = idx[np.argsort(order, kind="stable")]
        groups.append(idx)
    return groups


def lagged_series_by_run(values: Sequence[float] | np.ndarray, meta: pd.DataFrame, *, lag: int) -> np.ndarray:
    arr = np.asarray(values, dtype=float).reshape(-1)
    lag_int = max(0, int(lag))
    out = np.zeros(len(arr), dtype=float)
    for idx in _group_indices(meta):
        if len(idx) == 0:
            continue
        if lag_int <= 0:
            out[idx] = arr[idx]
        else:
            out[idx[:lag_int]] = arr[idx[0]]
            out[idx[lag_int:]] = arr[idx[:-lag_int]]
    return out


def build_single_edge_features(
    x: pd.DataFrame,
    meta: pd.DataFrame,
    edge: Mapping[str, Any],
) -> pd.DataFrame:
    src = str(edge.get("source", ""))
    dst = str(edge.get("target", ""))
    if src not in x.columns or dst not in x.columns:
        raise KeyError(f"Edge features require columns {src!r} and {dst!r}")
    lag = max(0, int(edge.get("lag", 0) or 0))
    source_lag = lagged_series_by_run(pd.to_numeric(x[src], errors="coerce").fillna(0.0).to_numpy(), meta, lag=lag)
    target = pd.to_numeric(x[dst], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    delta = target - source_lag
    abs_delta = np.abs(delta)
    product = target * source_lag
    return pd.DataFrame(
        {
            f"{edge['edge_id']}__src_lag": source_lag,
            f"{edge['edge_id']}__target": target,
            f"{edge['edge_id']}__delta": delta,
            f"{edge['edge_id']}__abs_delta": abs_delta,
            f"{edge['edge_id']}__product": product,
        },
        index=x.index,
    )


def build_probe_feature_block(
    x: pd.DataFrame,
    meta: pd.DataFrame,
    edges: Sequence[Mapping[str, Any]],
    *,
    max_edges_per_probe: int | None = None,
) -> pd.DataFrame:
    selected = list(edges)
    if max_edges_per_probe is not None and int(max_edges_per_probe) > 0:
        selected = selected[: int(max_edges_per_probe)]
    if not selected:
        return pd.DataFrame(index=x.index)
    blocks = [build_single_edge_features(x, meta, edge) for edge in selected]
    return pd.concat(blocks, axis=1)


def _target_defect_macro_f1(y_true: np.ndarray, proba: np.ndarray, *, normal_class_id: int = 0) -> float:
    pred = np.argmax(np.asarray(proba, dtype=float), axis=1)
    labels = sorted(int(v) for v in np.unique(y_true) if int(v) != int(normal_class_id))
    if not labels:
        return 0.0
    return float(f1_score(y_true, pred, labels=labels, average="macro", zero_division=0))


def _low_tail_f1(y_true: np.ndarray, proba: np.ndarray, *, normal_class_id: int = 0) -> float:
    pred = np.argmax(np.asarray(proba, dtype=float), axis=1)
    vals: list[float] = []
    for cls in sorted(int(v) for v in np.unique(y_true) if int(v) != int(normal_class_id)):
        mask_true = y_true == cls
        if not np.any(mask_true):
            continue
        vals.append(float(f1_score(mask_true.astype(int), (pred == cls).astype(int), zero_division=0)))
    return float(min(vals)) if vals else 0.0


def _far_mar(y_true: np.ndarray, proba: np.ndarray, *, normal_class_id: int = 0) -> tuple[float, float]:
    pred = np.argmax(np.asarray(proba, dtype=float), axis=1)
    normal = y_true == int(normal_class_id)
    abnormal = ~normal
    far = float(np.mean(pred[normal] != int(normal_class_id))) if np.any(normal) else 0.0
    mar = float(np.mean(pred[abnormal] == int(normal_class_id))) if np.any(abnormal) else 0.0
    return far, mar


def _validation_metrics(y_true: np.ndarray, proba: np.ndarray) -> dict[str, float]:
    far, mar = _far_mar(y_true, proba)
    return {
        "target_defect_macro_f1": _target_defect_macro_f1(y_true, proba),
        "low_tail_f1": _low_tail_f1(y_true, proba),
        "far": far,
        "mar": mar,
    }


def _mean_std(values: Sequence[float]) -> tuple[float | None, float | None]:
    vals = [float(v) for v in values if v is not None and np.isfinite(float(v))]
    if not vals:
        return None, None
    return float(mean(vals)), float(pstdev(vals))


def _aggregate_probe_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_probe: dict[str, list[Mapping[str, Any]]] = {}
    for row in records:
        probe_id = str(row.get("probe_id") or f"single_edge:{row['edge_id']}")
        by_probe.setdefault(probe_id, []).append(row)
    out: list[dict[str, Any]] = []
    for probe_id, rows in sorted(by_probe.items()):
        first = dict(rows[0])
        edge_ids = [str(edge_id) for edge_id in (first.get("edge_ids") or [first.get("edge_id")]) if edge_id is not None]
        probe_level = str(first.get("probe_level") or "single_edge")
        probe_key = str(first.get("probe_key") or (edge_ids[0] if edge_ids else probe_id))
        agg: dict[str, Any] = {
            "probe_id": probe_id,
            "probe_level": probe_level,
            "probe_key": probe_key,
            "edge_ids": edge_ids,
            "n_edges": int(first.get("n_edges") or len(edge_ids)),
            "edge_id": edge_ids[0] if probe_level == "single_edge" and edge_ids else None,
            "source_family": first.get("source_family"),
            "target_group": first.get("target_group"),
            "lag_group": first.get("lag_group"),
            "n_seed_records": int(len(rows)),
        }
        for key in ["validation_gain", "low_tail_delta", "far_delta", "mar_delta", "cf_sensitivity"]:
            vals = [row.get(key) for row in rows if row.get(key) is not None]
            m, s = _mean_std(vals)
            agg[key] = m
            agg[f"{key}_std"] = s
        out.append(agg)
    return out


def _passes_pre_cf(row: Mapping[str, Any], thresholds: Mapping[str, float]) -> bool:
    return (
        row.get("validation_gain") is not None
        and float(row["validation_gain"]) > float(thresholds["min_validation_gain"])
        and row.get("low_tail_delta") is not None
        and float(row["low_tail_delta"]) >= float(thresholds["min_low_tail_delta"])
        and row.get("far_delta") is not None
        and float(row["far_delta"]) <= float(thresholds["max_far_delta"])
        and row.get("mar_delta") is not None
        and float(row["mar_delta"]) <= float(thresholds["max_mar_delta"])
    )


def _parse_probe_levels(raw: str | Sequence[str] | None) -> list[str]:
    if raw is None:
        return ["single_edge"]
    if isinstance(raw, str):
        levels = [part.strip() for part in raw.split(",") if part.strip()]
    else:
        levels = [str(part).strip() for part in raw if str(part).strip()]
    allowed = {"source_family", "target_group", "lag_group", "single_edge"}
    bad = [level for level in levels if level not in allowed]
    if bad:
        raise ValueError(f"Unsupported probe levels: {bad}")
    return levels or ["single_edge"]


def build_measured_probe_plan(
    edges: Sequence[Mapping[str, Any]],
    *,
    probe_levels: Sequence[str],
    max_single_edge_probes: int | None = None,
) -> list[dict[str, Any]]:
    selected_levels = set(_parse_probe_levels(probe_levels))
    rows: list[dict[str, Any]] = []
    single_count = 0
    for row in build_probe_plan(edges):
        level = str(row.get("probe_level"))
        if level not in selected_levels:
            continue
        if level == "single_edge":
            if max_single_edge_probes is not None and int(max_single_edge_probes) > 0 and single_count >= int(max_single_edge_probes):
                continue
            single_count += 1
        rows.append(dict(row))
    return rows


def run_tep_single_edge_validation_probe(
    *,
    dataset_dir: Path,
    output_path: Path,
    seeds: Sequence[int],
    max_rows: int | None,
    max_edges: int | None,
    probe_levels: Sequence[str] | None = None,
    max_single_edge_probes: int | None = None,
    max_edges_per_probe: int | None = None,
    n_estimators: int,
    max_depth: int | None,
    thresholds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    thresholds = {**THRESHOLDS, **dict(thresholds or {})}
    parsed_probe_levels = _parse_probe_levels(probe_levels)
    x, meta, labels = _load_tep_frames(dataset_dir)
    train_all = np.flatnonzero(meta["split_role"].astype(str).str.lower().eq("train").to_numpy())
    classes = [int(c) for c in sorted(np.unique(labels))]
    edges = build_frozen_tep_candidate_pool()
    edges = [edge for edge in edges if edge["source"] in x.columns and edge["target"] in x.columns]
    if max_edges is not None and int(max_edges) > 0:
        edges = edges[: int(max_edges)]
    edge_by_id = {str(edge["edge_id"]): edge for edge in edges}
    probe_plan = build_measured_probe_plan(
        edges,
        probe_levels=parsed_probe_levels,
        max_single_edge_probes=max_single_edge_probes,
    )
    seed_records: list[dict[str, Any]] = []
    anchor_records: list[dict[str, Any]] = []
    for seed in seeds:
        pool = _subsample_stratified(train_all, labels, max_rows=max_rows, seed=int(seed))
        train_idx, val_idx = _stratified_val_split(pool, labels, seed=int(seed), val_fraction=0.25)
        x_train = x.iloc[train_idx].reset_index(drop=True)
        x_val = x.iloc[val_idx].reset_index(drop=True)
        y_train = labels[train_idx]
        y_val = labels[val_idx]
        anchor = _fit_extra_trees(
            x_train,
            y_train,
            seed=int(seed),
            n_estimators=int(n_estimators),
            max_depth=max_depth,
        )
        anchor_val = _predict_proba_aligned(anchor, x_val, classes)
        anchor_metrics = _validation_metrics(y_val, anchor_val)
        anchor_records.append({"seed": int(seed), "metrics": anchor_metrics, "train_rows": int(len(train_idx)), "val_rows": int(len(val_idx))})
        for probe in probe_plan:
            probe_edges = [edge_by_id[str(edge_id)] for edge_id in probe.get("edge_ids", []) if str(edge_id) in edge_by_id]
            feature_edges = probe_edges
            if max_edges_per_probe is not None and int(max_edges_per_probe) > 0:
                feature_edges = feature_edges[: int(max_edges_per_probe)]
            edge_features = build_probe_feature_block(
                x,
                meta,
                feature_edges,
            )
            train_probe = edge_features.iloc[train_idx].reset_index(drop=True)
            val_probe = edge_features.iloc[val_idx].reset_index(drop=True)
            challenger_train = pd.concat([x_train.reset_index(drop=True), train_probe], axis=1)
            challenger_val = pd.concat([x_val.reset_index(drop=True), val_probe], axis=1)
            challenger = _fit_extra_trees(
                challenger_train,
                y_train,
                seed=int(seed) + 7919,
                n_estimators=max(20, int(n_estimators)),
                max_depth=max_depth,
            )
            challenger_proba = _predict_proba_aligned(challenger, challenger_val, classes)
            challenger_metrics = _validation_metrics(y_val, challenger_proba)
            single_edge = probe_edges[0] if len(probe_edges) == 1 else {}
            row: dict[str, Any] = {
                "seed": int(seed),
                "edge_id": single_edge.get("edge_id") if probe.get("probe_level") == "single_edge" else None,
                "edge_ids": [str(edge_id) for edge_id in probe.get("edge_ids", [])],
                "probe_id": probe["probe_id"],
                "probe_level": probe["probe_level"],
                "probe_key": probe["probe_key"],
                "n_edges": int(probe.get("n_edges", len(probe_edges))),
                "n_feature_edges": int(len(feature_edges)),
                "source_family": probe["probe_key"] if probe.get("probe_level") == "source_family" else single_edge.get("source_family"),
                "target_group": probe["probe_key"] if probe.get("probe_level") == "target_group" else single_edge.get("target_group"),
                "lag_group": probe["probe_key"] if probe.get("probe_level") == "lag_group" else single_edge.get("lag_group"),
                "validation_gain": float(challenger_metrics["target_defect_macro_f1"] - anchor_metrics["target_defect_macro_f1"]),
                "low_tail_delta": float(challenger_metrics["low_tail_f1"] - anchor_metrics["low_tail_f1"]),
                "far_delta": float(challenger_metrics["far"] - anchor_metrics["far"]),
                "mar_delta": float(challenger_metrics["mar"] - anchor_metrics["mar"]),
                "anchor_metrics": anchor_metrics,
                "challenger_metrics": challenger_metrics,
                "cf_sensitivity": None,
            }
            if _passes_pre_cf(row, thresholds):
                cf_val = challenger_val.copy()
                for col in train_probe.columns:
                    cf_val[col] = 0.0
                cf_proba = _predict_proba_aligned(challenger, cf_val, classes)
                row["cf_sensitivity"] = float(np.mean(np.abs(challenger_proba - cf_proba)))
            row.update(evaluate_probe_row(row, thresholds=thresholds))
            seed_records.append(row)

    aggregated = _aggregate_probe_records(seed_records)
    admitted_payload = admit_edges_from_probe_results(edges, aggregated, thresholds=thresholds)
    payload = {
        "status": "ok",
        "dataset": "TEP",
        "protocol": "hierarchical_validation_gain_then_safety_then_cf",
        "seeds": [int(s) for s in seeds],
        "max_rows": int(max_rows) if max_rows is not None and int(max_rows) > 0 else None,
        "max_edges": int(max_edges) if max_edges is not None and int(max_edges) > 0 else None,
        "probe_levels": parsed_probe_levels,
        "max_single_edge_probes": int(max_single_edge_probes) if max_single_edge_probes is not None and int(max_single_edge_probes) > 0 else None,
        "max_edges_per_probe": int(max_edges_per_probe) if max_edges_per_probe is not None and int(max_edges_per_probe) > 0 else None,
        "n_estimators": int(n_estimators),
        "max_depth": max_depth,
        "thresholds": thresholds,
        "candidate_edges": edges,
        "probe_plan": probe_plan,
        "anchor_records": anchor_records,
        "seed_records": seed_records,
        "aggregated_probe_results": aggregated,
        "admission": admitted_payload,
    }
    os.makedirs(_fs_path(Path(output_path).parent), exist_ok=True)
    with open(_fs_path(output_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    with open(_fs_path(Path(output_path).with_suffix(".md")), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(payload))
    return payload


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.4f}"
    except Exception:
        return str(value)


def render_markdown(payload: Mapping[str, Any]) -> str:
    admission = payload.get("admission", {}) or {}
    rows = sorted(
        list(payload.get("aggregated_probe_results", []) or []),
        key=lambda row: float(row.get("validation_gain") or -999.0),
        reverse=True,
    )
    level_counts: dict[str, int] = {}
    for row in rows:
        level = str(row.get("probe_level", "unknown"))
        level_counts[level] = level_counts.get(level, 0) + 1
    lines = [
        "# TEP Hierarchical Edge Validation Probe",
        "",
        f"- Protocol: {payload.get('protocol')}",
        f"- Seeds: {payload.get('seeds')}",
        f"- Candidate edges tested: {len(payload.get('candidate_edges', []) or [])}",
        f"- Probe levels: {payload.get('probe_levels')}",
        f"- Probe rows: {len(rows)}",
        f"- Validation-admitted edges: {admission.get('n_validation_admitted_edges', 0)}",
        f"- Gate order: {', '.join(admission.get('gate_order', []))}",
        f"- Admission rule: only `single_edge` probes can materialize `validation_admitted_edges`; group probes are screening diagnostics.",
        "",
        "## Probe Level Counts",
        "",
        "| Level | Measured probes |",
        "|---|---:|",
    ]
    for level, count in sorted(level_counts.items()):
        lines.append(f"| {level} | {count} |")
    lines.extend(
        [
            "",
        "## Top Aggregated Edge Probes",
        "",
            "| Probe | Level | Family | Target group | Lag group | Edges | Val gain | Low-tail delta | FAR delta | MAR delta | CF sensitivity | Gate passed | Reject reasons |",
            "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    evaluated = {str(row["probe_key"]): row for row in admission.get("probe_results", []) or []}
    for row in rows[:30]:
        gate = evaluated.get(str(row.get("probe_key")), {})
        lines.append(
            "| {probe} | {level} | {family} | {target_group} | {lag_group} | {n_edges} | {gain} | {lowtail} | {far} | {mar} | {cf} | {admitted} | {reasons} |".format(
                probe=row.get("probe_key"),
                level=row.get("probe_level"),
                family=row.get("source_family"),
                target_group=row.get("target_group"),
                lag_group=row.get("lag_group"),
                n_edges=row.get("n_edges"),
                gain=_fmt(row.get("validation_gain")),
                lowtail=_fmt(row.get("low_tail_delta")),
                far=_fmt(row.get("far_delta")),
                mar=_fmt(row.get("mar_delta")),
                cf=_fmt(row.get("cf_sensitivity")),
                admitted=bool(gate.get("admitted", False)),
                reasons=", ".join(gate.get("reject_reasons", []) or []),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This measured probe enforces the fixed order: validation gain first, low-tail/FAR/MAR safety second, and CF only for candidates that pass those guards. A candidate with strong counterfactual sensitivity but negative validation gain or safety harm is rejected before deployment.",
            "",
        ]
    )
    return "\n".join(lines)


def _parse_seeds(raw: str) -> list[int]:
    seeds = [int(part.strip()) for part in str(raw).split(",") if part.strip()]
    if not seeds:
        raise ValueError("At least one seed is required")
    return seeds


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run TEP measured single-edge validation-gain probes.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_TEP_DATASET_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR / "tep_single_edge_validation_probe.json")
    parser.add_argument("--seeds", type=str, default="42")
    parser.add_argument("--max-rows", type=int, default=3000)
    parser.add_argument("--max-edges", type=int, default=0)
    parser.add_argument("--probe-levels", type=str, default="single_edge")
    parser.add_argument("--max-single-edge-probes", type=int, default=12)
    parser.add_argument("--max-edges-per-probe", type=int, default=0)
    parser.add_argument("--n-estimators", type=int, default=80)
    parser.add_argument("--max-depth", type=int, default=10)
    args = parser.parse_args(argv)
    payload = run_tep_single_edge_validation_probe(
        dataset_dir=Path(args.dataset_dir),
        output_path=Path(args.output),
        seeds=_parse_seeds(args.seeds),
        max_rows=int(args.max_rows) if int(args.max_rows) > 0 else None,
        max_edges=int(args.max_edges) if int(args.max_edges) > 0 else None,
        probe_levels=_parse_probe_levels(args.probe_levels),
        max_single_edge_probes=int(args.max_single_edge_probes) if int(args.max_single_edge_probes) > 0 else None,
        max_edges_per_probe=int(args.max_edges_per_probe) if int(args.max_edges_per_probe) > 0 else None,
        n_estimators=int(args.n_estimators),
        max_depth=int(args.max_depth) if int(args.max_depth) > 0 else None,
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
