from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence

import numpy as np

from public_benchmark_experiment import (
    DEFAULT_PUBLIC_DATASET_ROOT,
    _scale_skab_sequence_windows,
    build_skab_causal_sequence_windows,
    load_skab_dataset,
    split_skab_runs,
)
from run_skab_dynamic_llm_graph_experiment import (
    _filter_edges_by_reliability,
    _fs_path,
    _load_dynamic_edges_file,
    _train_msfg_time_context_branch,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORTS_DIR = PROJECT_ROOT / "knowledge_exports"


def _write_text(path: Path | str, text: str) -> None:
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        handle.write(text)


def edge_label(edge: Mapping[str, Any]) -> str:
    return "{source}->{target}@{lag}".format(
        source=edge.get("source", ""),
        target=edge.get("target", ""),
        lag=int(edge.get("lag", 0) or 0),
    )


def enumerate_edge_subsets(
    edges: Sequence[Mapping[str, Any]],
    *,
    max_subset_size: int,
) -> list[list[dict[str, Any]]]:
    out: list[list[dict[str, Any]]] = []
    clean = [dict(edge) for edge in edges]
    for size in range(1, max(1, int(max_subset_size)) + 1):
        for combo in itertools.combinations(clean, size):
            out.append([dict(edge) for edge in combo])
    return out


def _candidate_cache_path(exports_dir: Path, seed: int) -> Path:
    return exports_dir / f"public_benchmark_skab_dynamic_llm_api_seed{seed}_e8_learned_reliability_probe2_t045_k4.json"


def _build_common(dataset_root: Path, *, seed: int, sequence_window_size: int) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    x_raw, y_raw, meta = load_skab_dataset(dataset_root)
    y = np.asarray(y_raw, dtype=np.int64)
    sequence_windows, sequence_feature_cols = build_skab_causal_sequence_windows(
        x_raw,
        meta,
        window_size=int(sequence_window_size),
        include_valid_mask=True,
    )
    train_runs, val_runs, test_runs = split_skab_runs(meta, seed=int(seed), test_size=0.30, val_fraction=0.25)
    train_mask = meta["run_id"].astype(str).isin(train_runs).to_numpy(dtype=bool)
    val_mask = meta["run_id"].astype(str).isin(val_runs).to_numpy(dtype=bool)
    test_mask = meta["run_id"].astype(str).isin(test_runs).to_numpy(dtype=bool)
    common = {
        "x_raw": x_raw,
        "y": y,
        "meta": meta,
        "train_mask": train_mask,
        "val_mask": val_mask,
        "test_mask": test_mask,
        "sequence_windows": sequence_windows,
        "sequence_feature_cols": list(sequence_feature_cols),
        "sequence_window_size": int(sequence_window_size),
    }
    return common, train_mask, val_mask, test_mask


def sweep_edge_subsets(
    *,
    dataset_root: Path = DEFAULT_PUBLIC_DATASET_ROOT,
    candidate_file: Path,
    seed: int,
    sequence_epochs: int = 1,
    hidden_dim: int = 32,
    batch_size: int = 512,
    sequence_window_size: int = 32,
    reliability_threshold: float = 0.45,
    max_subset_size: int = 2,
    max_edges: int = 8,
) -> dict[str, Any]:
    raw_edges, load_diag = _load_dynamic_edges_file(Path(candidate_file), max_edges=int(max_edges))
    edges, reliability_diag = _filter_edges_by_reliability(raw_edges, threshold=float(reliability_threshold))
    common, _train_mask, _val_mask, _test_mask = _build_common(
        Path(dataset_root),
        seed=int(seed),
        sequence_window_size=int(sequence_window_size),
    )
    common.update({"epochs": int(sequence_epochs), "hidden_dim": int(hidden_dim), "batch_size": int(batch_size)})
    baseline = _train_msfg_time_context_branch(
        **common,
        dynamic_llm_edges=None,
        seed=int(seed) + 8200,
    )
    baseline_val = float(baseline["validation_metrics"]["macro_f1"])
    baseline_test = float(baseline["metrics"]["macro_f1"])
    rows: list[dict[str, Any]] = []
    for index, subset in enumerate(enumerate_edge_subsets(edges, max_subset_size=int(max_subset_size))):
        branch = _train_msfg_time_context_branch(
            **common,
            dynamic_llm_edges=subset,
            seed=int(seed) + 8200,
        )
        val_macro = float(branch["validation_metrics"]["macro_f1"])
        test_macro = float(branch["metrics"]["macro_f1"])
        rows.append(
            {
                "subset_index": int(index),
                "subset_size": int(len(subset)),
                "edge_labels": [edge_label(edge) for edge in subset],
                "edges": subset,
                "validation_macro_f1": val_macro,
                "validation_gain": float(val_macro - baseline_val),
                "test_macro_f1": test_macro,
                "test_gain": float(test_macro - baseline_test),
                "sequence_n_features": int(branch.get("sequence_n_features", 0)),
            }
        )
    rows.sort(key=lambda row: (float(row["validation_gain"]), float(row["test_gain"])), reverse=True)
    positive = [row for row in rows if float(row["validation_gain"]) >= 0.0]
    best = rows[0] if rows else None
    return {
        "status": "ok" if rows else "no_candidate_subsets",
        "schema": "skab_dynamic_edge_subset_sweep_v1",
        "seed": int(seed),
        "candidate_file": str(candidate_file),
        "load": load_diag,
        "reliability": reliability_diag,
        "sequence_epochs": int(sequence_epochs),
        "max_subset_size": int(max_subset_size),
        "baseline_validation_macro_f1": baseline_val,
        "baseline_test_macro_f1": baseline_test,
        "n_subsets": int(len(rows)),
        "n_positive_validation_subsets": int(len(positive)),
        "best": best,
        "top_rows": rows[: min(20, len(rows))],
        "validation_gain_mean": float(mean([float(row["validation_gain"]) for row in rows])) if rows else 0.0,
        "validation_gain_std": float(pstdev([float(row["validation_gain"]) for row in rows])) if len(rows) > 1 else 0.0,
    }


def write_best_candidate_cache(report: Mapping[str, Any], output_path: Path | str) -> bool:
    best = report.get("best") if isinstance(report, Mapping) else None
    if not isinstance(best, Mapping) or float(best.get("validation_gain", -1.0)) < 0.0:
        return False
    payload = {
        "status": "ok",
        "schema": "skab_cf_validated_candidate_subset_v1",
        "seed": int(report.get("seed", 0)),
        "source_sweep": str(report.get("candidate_file", "")),
        "dynamic_edges": [dict(edge) for edge in best.get("edges", [])],
        "candidate_edges": [dict(edge) for edge in best.get("edges", [])],
        "diagnostics": {
            "validation_macro_f1": float(best.get("validation_macro_f1", 0.0)),
            "validation_gain": float(best.get("validation_gain", 0.0)),
            "test_macro_f1": float(best.get("test_macro_f1", 0.0)),
            "test_gain": float(best.get("test_gain", 0.0)),
            "edge_labels": list(best.get("edge_labels", [])),
            "note": "Best validation-positive subset from frozen candidate sweep; intended for matched CF/no-CF execution.",
        },
    }
    path = Path(output_path)
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    _write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return True


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# SKAB Dynamic Edge Subset Sweep",
        "",
        f"- Status: {report.get('status')}",
        f"- Seed: {report.get('seed')}",
        f"- Epochs: {report.get('sequence_epochs')}",
        f"- Baseline validation Macro-F1: {float(report.get('baseline_validation_macro_f1', 0.0)):.4f}",
        f"- Baseline test Macro-F1: {float(report.get('baseline_test_macro_f1', 0.0)):.4f}",
        f"- Candidate subsets: {report.get('n_subsets')}",
        f"- Validation-positive subsets: {report.get('n_positive_validation_subsets')}",
        "",
        "| Rank | Subset | Val Macro-F1 | Val Gain | Test Macro-F1 | Test Gain |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(list(report.get("top_rows", []) or [])[:10], start=1):
        lines.append(
            "| {rank} | {labels} | {val:.4f} | {vgain:+.4f} | {test:.4f} | {tgain:+.4f} |".format(
                rank=rank,
                labels=", ".join(row.get("edge_labels", [])),
                val=float(row.get("validation_macro_f1", 0.0)),
                vgain=float(row.get("validation_gain", 0.0)),
                test=float(row.get("test_macro_f1", 0.0)),
                tgain=float(row.get("test_gain", 0.0)),
            )
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sweep SKAB dynamic edge subsets before CF/no-CF admission.")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_PUBLIC_DATASET_ROOT)
    parser.add_argument("--exports-dir", type=Path, default=DEFAULT_EXPORTS_DIR)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--candidate-file", type=Path, default=None)
    parser.add_argument("--sequence-epochs", type=int, default=1)
    parser.add_argument("--sequence-hidden-dim", type=int, default=32)
    parser.add_argument("--sequence-batch-size", type=int, default=512)
    parser.add_argument("--sequence-window-size", type=int, default=32)
    parser.add_argument("--edge-reliability-threshold", type=float, default=0.45)
    parser.add_argument("--max-subset-size", type=int, default=2)
    parser.add_argument("--max-edges", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_EXPORTS_DIR / "aaai_missing_ablation_runs" / "skab_edge_subset_sweep")
    parser.add_argument("--write-best-cache", action="store_true")
    args = parser.parse_args(argv)
    candidate_file = args.candidate_file or _candidate_cache_path(Path(args.exports_dir), int(args.seed))
    report = sweep_edge_subsets(
        dataset_root=args.dataset_root,
        candidate_file=Path(candidate_file),
        seed=int(args.seed),
        sequence_epochs=int(args.sequence_epochs),
        hidden_dim=int(args.sequence_hidden_dim),
        batch_size=int(args.sequence_batch_size),
        sequence_window_size=int(args.sequence_window_size),
        reliability_threshold=float(args.edge_reliability_threshold),
        max_subset_size=int(args.max_subset_size),
        max_edges=int(args.max_edges),
    )
    output_dir = Path(args.output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    json_path = output_dir / f"seed{int(args.seed)}_edge_subset_sweep.json"
    md_path = output_dir / f"seed{int(args.seed)}_edge_subset_sweep.md"
    _write_text(json_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    _write_text(md_path, render_markdown(report))
    print(json_path)
    print(md_path)
    if args.write_best_cache:
        cache_path = output_dir / f"seed{int(args.seed)}_best_validated_edges.json"
        if write_best_candidate_cache(report, cache_path):
            print(cache_path)
        else:
            print("no_validation_positive_subset")


if __name__ == "__main__":
    main()
