from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from public_benchmark_experiment import (
    DEFAULT_PUBLIC_DATASET_ROOT,
    PROJECT_ROOT,
    SKAB_LLM_MECHANISM_EDGE_CANDIDATES,
    _scale_skab_sequence_windows,
    build_skab_causal_sequence_windows,
    build_skab_data_lag_edges,
    build_skab_msfg_tcn_windows,
    build_skab_positive_expert_edges,
    fuse_skab_multisource_graph_edges,
    load_skab_dataset,
    merge_skab_dynamic_llm_edges,
    prune_skab_expert_edges,
    scale_skab_named_sequence_windows,
    split_skab_runs,
    summarize_classification,
    summarize_skab_protocol_detection,
    tune_binary_threshold,
)
from tep_sequence_heads import train_sequence_model


MODE_ORDER = [
    "original_full_msfg",
    "full_pruned_kg",
    "no_llm_pruned_kg",
    "expert_only_pruned_kg",
    "llm_only",
    "data_only",
]


def _fuse(
    *,
    expert_edges: Sequence[Mapping[str, Any]],
    llm_edges: Sequence[Mapping[str, Any]],
    data_edges: Sequence[Mapping[str, Any]],
    min_reliability: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return fuse_skab_multisource_graph_edges(
        expert_edges=list(expert_edges),
        llm_edges=list(llm_edges),
        data_edges=list(data_edges),
        min_reliability=float(min_reliability),
    )


def build_source_mode_edge_sets(
    *,
    expert_edges: Sequence[Mapping[str, Any]],
    llm_edges: Sequence[Mapping[str, Any]],
    data_edges: Sequence[Mapping[str, Any]],
    min_support_score: float = 0.18,
    min_reliability: float = 0.10,
) -> dict[str, dict[str, Any]]:
    expert_list = build_skab_positive_expert_edges(list(expert_edges))
    llm_list = [dict(edge) for edge in llm_edges]
    data_list = [dict(edge) for edge in data_edges]
    pruned_experts, expert_pruning = prune_skab_expert_edges(
        expert_list,
        llm_edges=llm_list,
        data_edges=data_list,
        min_support_score=float(min_support_score),
    )
    mode_inputs = {
        "original_full_msfg": (expert_list, llm_list, data_list),
        "full_pruned_kg": (pruned_experts, llm_list, data_list),
        "no_llm_pruned_kg": (pruned_experts, [], data_list),
        "expert_only_pruned_kg": (pruned_experts, [], []),
        "llm_only": ([], llm_list, []),
        "data_only": ([], [], data_list),
    }
    modes: dict[str, dict[str, Any]] = {}
    for name, (mode_expert, mode_llm, mode_data) in mode_inputs.items():
        fused_edges, fusion = _fuse(
            expert_edges=mode_expert,
            llm_edges=mode_llm,
            data_edges=mode_data,
            min_reliability=float(min_reliability),
        )
        modes[name] = {
            "mode": name,
            "expert_edges": [dict(edge) for edge in mode_expert],
            "llm_edges": [dict(edge) for edge in mode_llm],
            "data_edges": [dict(edge) for edge in mode_data],
            "fused_edges": [dict(edge) for edge in fused_edges],
            "fusion": fusion,
            "expert_pruning": expert_pruning,
        }
    return modes


def _split_csv_ints(text: str) -> list[int]:
    return [int(item.strip()) for item in str(text).split(",") if item.strip()]


def run_skab_msfg_pruning_ablation(
    dataset_root: Path,
    output_path: Path,
    *,
    seeds: Sequence[int],
    sequence_window_size: int = 32,
    sequence_epochs: int = 3,
    sequence_hidden_dim: int = 48,
    sequence_batch_size: int = 256,
    sequence_learning_rate: float = 0.001,
    min_support_score: float = 0.18,
    min_reliability: float = 0.10,
    modes: Sequence[str] = MODE_ORDER,
) -> dict[str, Any]:
    x_raw, y, meta = load_skab_dataset(dataset_root)
    y_arr = np.asarray(y, dtype=np.int64).reshape(-1)
    sequence_windows, sequence_feature_cols = build_skab_causal_sequence_windows(
        x_raw,
        meta,
        window_size=int(sequence_window_size),
        include_valid_mask=True,
    )
    base_cols = [str(col) for col in sequence_feature_cols if str(col) != "valid_mask"]
    runs: list[dict[str, Any]] = []
    for seed in seeds:
        train_runs, val_runs, test_runs = split_skab_runs(meta, seed=int(seed), test_size=0.30, val_fraction=0.25)
        train_mask = meta["run_id"].astype(str).isin(train_runs).to_numpy(dtype=bool)
        val_mask = meta["run_id"].astype(str).isin(val_runs).to_numpy(dtype=bool)
        test_mask = meta["run_id"].astype(str).isin(test_runs).to_numpy(dtype=bool)
        y_train = y_arr[train_mask]
        y_val = y_arr[val_mask]
        y_test = y_arr[test_mask]
        meta_test = meta.iloc[np.flatnonzero(test_mask)].reset_index(drop=True)
        scaled_sequence = _scale_skab_sequence_windows(
            sequence_windows,
            train_mask,
            has_valid_mask=True,
        )
        data_edges, data_diag = build_skab_data_lag_edges(
            x_raw.reset_index(drop=True),
            meta.reset_index(drop=True),
            base_cols,
            train_mask=train_mask,
            max_lag=8,
            top_k=24,
            min_abs_correlation=0.25,
            min_pairs=8,
        )
        llm_edges, dynamic_llm_diag = merge_skab_dynamic_llm_edges(
            list(SKAB_LLM_MECHANISM_EDGE_CANDIDATES),
            dynamic_edges=None,
            max_dynamic_edges=8,
        )
        mode_specs = build_source_mode_edge_sets(
            expert_edges=build_skab_positive_expert_edges(None),
            llm_edges=llm_edges,
            data_edges=data_edges,
            min_support_score=float(min_support_score),
            min_reliability=float(min_reliability),
        )
        for mode_index, mode in enumerate(modes):
            if mode not in mode_specs:
                raise ValueError(f"Unknown mode: {mode}")
            spec = mode_specs[mode]
            mode_windows, mode_cols, mode_input_diag = build_skab_msfg_tcn_windows(
                scaled_sequence,
                sequence_feature_cols,
                x_raw.reset_index(drop=True),
                meta.reset_index(drop=True),
                train_mask=train_mask,
                window_size=int(sequence_window_size),
                fused_edges=spec["fused_edges"],
                expert_edges=spec["expert_edges"],
                llm_edges=spec["llm_edges"],
                data_edges=spec["data_edges"],
            )
            mode_windows = scale_skab_named_sequence_windows(
                mode_windows,
                mode_cols,
                train_mask=train_mask,
                passthrough_cols=("valid_mask",),
            )
            valid_mask_index = mode_cols.index("valid_mask") if "valid_mask" in mode_cols else None
            val_proba, test_proba, model_diag = train_sequence_model(
                mode_windows[train_mask],
                y_train,
                mode_windows[val_mask],
                mode_windows[test_mask],
                model_name="masked_tcn",
                n_classes=2,
                hidden_dim=int(sequence_hidden_dim),
                epochs=int(sequence_epochs),
                batch_size=int(sequence_batch_size),
                learning_rate=float(sequence_learning_rate),
                seed=int(seed) + 3001 + mode_index * 101,
                valid_mask_index=valid_mask_index,
            )
            threshold = tune_binary_threshold(y_val, val_proba, positive_recall_weight=0.0)
            metrics = summarize_classification(y_test, test_proba, positive_threshold=threshold)
            protocol = summarize_skab_protocol_detection(
                y_test,
                test_proba,
                meta_test,
                positive_threshold=threshold,
                changepoint_window_steps=60,
            )
            runs.append(
                {
                    "seed": int(seed),
                    "mode": str(mode),
                    "sequence_epochs": int(sequence_epochs),
                    "sequence_hidden_dim": int(sequence_hidden_dim),
                    "sequence_window_size": int(sequence_window_size),
                    "macro_f1": float(metrics["macro_f1"]),
                    "positive_f1": float(metrics["positive_f1"]),
                    "positive_precision": float(metrics["positive_precision"]),
                    "positive_recall": float(metrics["positive_recall"]),
                    "point_adjusted_f1": float(protocol["point_adjusted"]["f1"]),
                    "far_percent": float(protocol["binary"]["far_percent"]),
                    "mar_percent": float(protocol["binary"]["mar_percent"]),
                    "threshold": float(threshold),
                    "n_channels": int(mode_windows.shape[2]),
                    "fusion": spec["fusion"],
                    "expert_pruning": spec["expert_pruning"],
                    "data_graph": data_diag,
                    "dynamic_llm_graph": dynamic_llm_diag,
                    "model_diagnostics": model_diag,
                    "input_diagnostics": {
                        "feature_role": mode_input_diag.get("feature_role"),
                        "n_channels": mode_input_diag.get("n_channels"),
                        "evidence_gate_mean": mode_input_diag.get("evidence_gate_mean"),
                        "evidence_gate_max": mode_input_diag.get("evidence_gate_max"),
                        "fusion": mode_input_diag.get("fusion"),
                    },
                }
            )
    result = {
        "status": "ok",
        "task": "skab_msfg_pruning_source_ablation",
        "modes": list(modes),
        "runs": runs,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SKAB MSFG source/pruning ablation.")
    parser.add_argument("--dataset-root", default=str(DEFAULT_PUBLIC_DATASET_ROOT))
    parser.add_argument("--output", default=str(PROJECT_ROOT / "knowledge_exports" / "skab_msfg_pruning_source_ablation.json"))
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--sequence-window-size", type=int, default=32)
    parser.add_argument("--sequence-epochs", type=int, default=3)
    parser.add_argument("--sequence-hidden-dim", type=int, default=48)
    parser.add_argument("--sequence-batch-size", type=int, default=256)
    parser.add_argument("--sequence-learning-rate", type=float, default=0.001)
    parser.add_argument("--min-support-score", type=float, default=0.18)
    parser.add_argument("--min-reliability", type=float, default=0.10)
    parser.add_argument("--modes", default=",".join(MODE_ORDER))
    args = parser.parse_args()
    result = run_skab_msfg_pruning_ablation(
        Path(args.dataset_root),
        Path(args.output),
        seeds=_split_csv_ints(args.seeds),
        sequence_window_size=int(args.sequence_window_size),
        sequence_epochs=int(args.sequence_epochs),
        sequence_hidden_dim=int(args.sequence_hidden_dim),
        sequence_batch_size=int(args.sequence_batch_size),
        sequence_learning_rate=float(args.sequence_learning_rate),
        min_support_score=float(args.min_support_score),
        min_reliability=float(args.min_reliability),
        modes=[item.strip() for item in str(args.modes).split(",") if item.strip()],
    )
    for run in result.get("runs", []):
        print(
            "seed={seed} mode={mode} macro_f1={macro:.4f} positive_f1={pf1:.4f} "
            "point_adjusted_f1={paf1:.4f} far={far:.2f} fused={fused}".format(
                seed=run["seed"],
                mode=run["mode"],
                macro=run["macro_f1"],
                pf1=run["positive_f1"],
                paf1=run["point_adjusted_f1"],
                far=run["far_percent"],
                fused=run["fusion"].get("n_fused_edges"),
            )
        )


if __name__ == "__main__":
    main()
