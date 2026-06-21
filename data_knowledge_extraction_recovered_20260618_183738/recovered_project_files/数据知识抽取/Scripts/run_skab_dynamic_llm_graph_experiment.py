from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from public_benchmark_experiment import (
    DEFAULT_PUBLIC_DATASET_ROOT,
    SKAB_LAGGED_MECHANISM_EDGES,
    SKAB_LLM_MECHANISM_EDGE_CANDIDATES,
    _scale_skab_sequence_windows,
    build_skab_causal_sequence_windows,
    build_skab_llm_graph_update_prompt,
    build_skab_msfg_tcn_windows,
    build_skab_time_context_sequence_windows,
    call_openai_skab_graph_proposer,
    load_skab_dataset,
    merge_skab_dynamic_llm_edges,
    parse_skab_llm_edge_proposals,
    scale_skab_named_sequence_windows,
    split_skab_runs,
    summarize_classification,
    summarize_skab_protocol_detection,
    tune_binary_threshold,
)
from tep_sequence_heads import train_sequence_model


COUNTERFACTUAL_MODES = {"reverse_direction", "lag_shift", "random_target"}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path | str) -> bool:
    return os.path.exists(_fs_path(path))


def _read_text(path: Path | str) -> str:
    with open(_fs_path(path), encoding="utf-8") as handle:
        return handle.read()


def _write_text(path: Path | str, text: str) -> None:
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        handle.write(text)


def _load_previous_error_summary(path: Path, *, seed: int, branch: str) -> dict[str, Any]:
    if not _exists(path):
        return {
            "source": "default",
            "false_negative_rate": 0.25,
            "false_positive_rate": 0.10,
            "weak_segments": [],
        }
    data = json.loads(_read_text(path))
    for run in data.get("runs", []):
        if int(run.get("seed", -1)) != int(seed):
            continue
        proto = run.get("skab_protocol_detection", {}).get(branch, {})
        binary = proto.get("binary", {})
        return {
            "source": str(path),
            "branch": str(branch),
            "false_negative_rate": float(binary.get("mar_percent", 0.0)) / 100.0,
            "false_positive_rate": float(binary.get("far_percent", 0.0)) / 100.0,
            "binary_f1": float(binary.get("f1", 0.0)),
            "point_adjusted_f1": float(proto.get("point_adjusted", {}).get("f1", 0.0)),
            "right_window_changepoint": proto.get("right_window_changepoint", {}),
        }
    return {
        "source": str(path),
        "branch": str(branch),
        "false_negative_rate": 0.25,
        "false_positive_rate": 0.10,
        "weak_segments": [],
    }


def _train_msfg_time_context_branch(
    *,
    x_raw,
    y: np.ndarray,
    meta,
    train_mask: np.ndarray,
    val_mask: np.ndarray,
    test_mask: np.ndarray,
    sequence_windows: np.ndarray,
    sequence_feature_cols: list[str],
    dynamic_llm_edges: list[dict[str, Any]] | None,
    seed: int,
    sequence_window_size: int,
    epochs: int,
    hidden_dim: int,
    batch_size: int,
) -> dict[str, Any]:
    y_train = y[train_mask]
    y_val = y[val_mask]
    y_test = y[test_mask]
    meta_train = meta.iloc[np.flatnonzero(train_mask)].reset_index(drop=True)
    meta_test = meta.iloc[np.flatnonzero(test_mask)].reset_index(drop=True)
    scaled_sequence = _scale_skab_sequence_windows(sequence_windows, train_mask, has_valid_mask=True)
    time_context_only_sequence, time_context_cols, time_context_diag = build_skab_time_context_sequence_windows(
        y_train,
        meta_train,
        meta.reset_index(drop=True),
        window_size=sequence_window_size,
    )
    time_context_only_sequence = scale_skab_named_sequence_windows(
        time_context_only_sequence,
        time_context_cols,
        train_mask=train_mask,
        passthrough_cols=(),
    )
    msfg_sequence, msfg_cols, msfg_diag = build_skab_msfg_tcn_windows(
        scaled_sequence,
        sequence_feature_cols,
        x_raw.reset_index(drop=True),
        meta.reset_index(drop=True),
        train_mask=train_mask,
        window_size=sequence_window_size,
        fused_edges=dynamic_llm_edges,
    )
    msfg_sequence = scale_skab_named_sequence_windows(
        msfg_sequence,
        msfg_cols,
        train_mask=train_mask,
        passthrough_cols=("valid_mask",),
    )
    feature_cols = list(msfg_cols) + [f"time_ctx_{col}" for col in time_context_cols]
    model_sequence = np.concatenate([msfg_sequence, time_context_only_sequence], axis=2).astype(np.float32)
    val_proba, test_proba, train_diag = train_sequence_model(
        model_sequence[train_mask],
        y_train,
        model_sequence[val_mask],
        model_sequence[test_mask],
        model_name="tcn",
        n_classes=2,
        hidden_dim=hidden_dim,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=0.001,
        seed=seed,
    )
    threshold = tune_binary_threshold(y_val, val_proba, positive_recall_weight=0.0)
    return {
        "threshold": float(threshold),
        "validation_metrics": summarize_classification(y_val, val_proba, positive_threshold=threshold),
        "metrics": summarize_classification(y_test, test_proba, positive_threshold=threshold),
        "protocol": summarize_skab_protocol_detection(
            y_test,
            test_proba,
            meta_test,
            positive_threshold=threshold,
            changepoint_window_steps=60,
        ),
        "sequence_n_features": int(model_sequence.shape[2]),
        "time_context": time_context_diag,
        "msfg": msfg_diag,
        "train": train_diag,
    }


def _load_dynamic_edges_file(path: Path, *, max_edges: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not _exists(path):
        return [], {"status": "missing", "path": str(path)}
    data = json.loads(_read_text(path))
    if isinstance(data, list):
        edges = data
    elif isinstance(data, dict):
        edges = (
            data.get("dynamic_edges")
            or data.get("candidate_dynamic_edges")
            or data.get("edges")
            or data.get("candidate_edges")
            or data.get("llm_edges")
            or []
        )
    else:
        edges = []
    out = [dict(edge) for edge in list(edges) if isinstance(edge, Mapping)]
    return out[: int(max_edges)], {"status": "ok", "path": str(path), "loaded_edges": len(out[: int(max_edges)])}


def _filter_edges_by_reliability(
    edges: list[dict[str, Any]],
    *,
    threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    kept = []
    rejected = 0
    for edge in edges:
        if float(edge.get("reliability", 0.0) or 0.0) >= float(threshold):
            kept.append(dict(edge))
        else:
            rejected += 1
    return kept, {
        "n_input_edges": len(edges),
        "n_kept_after_reliability": len(kept),
        "n_rejected_by_reliability": rejected,
        "edge_reliability_threshold": float(threshold),
    }


def _perturb_edges(
    edges: list[dict[str, Any]],
    *,
    mode: str,
    allowed_features: list[str],
) -> list[dict[str, Any]]:
    perturbed: list[dict[str, Any]] = []
    for index, edge in enumerate(edges):
        changed = dict(edge)
        if mode == "reverse_direction":
            changed["source"], changed["target"] = changed.get("target"), changed.get("source")
        elif mode == "lag_shift":
            changed["lag"] = int(changed.get("lag", 0) or 0) + 1
        elif mode == "random_target" and allowed_features:
            current_target = str(changed.get("target", ""))
            target = allowed_features[(index + 1) % len(allowed_features)]
            if target == current_target and len(allowed_features) > 1:
                target = allowed_features[(index + 2) % len(allowed_features)]
            changed["target"] = target
        perturbed.append(changed)
    return perturbed


def _apply_counterfactual_guard(
    *,
    candidate: dict[str, Any],
    common: dict[str, Any],
    edges: list[dict[str, Any]],
    modes: list[str],
    min_macro_drop: float,
    min_passing_modes: int,
    allowed_features: list[str],
    seed: int,
) -> tuple[bool, dict[str, Any]]:
    drops: dict[str, float] = {}
    candidate_macro = float(candidate["validation_metrics"]["macro_f1"])
    for offset, mode in enumerate(modes):
        if mode not in COUNTERFACTUAL_MODES:
            continue
        perturbed = _perturb_edges(edges, mode=mode, allowed_features=allowed_features)
        branch = _train_msfg_time_context_branch(
            **common,
            dynamic_llm_edges=perturbed,
            seed=int(seed) + 8400 + offset,
        )
        drops[mode] = float(candidate_macro - float(branch["validation_metrics"]["macro_f1"]))
    max_drop = max(drops.values()) if drops else 0.0
    passing_modes = [mode for mode, value in drops.items() if float(value) >= float(min_macro_drop)]
    required_modes = max(1, int(min_passing_modes))
    admitted = bool(len(passing_modes) >= required_modes) if modes else True
    return admitted, {
        "counterfactual_guard_modes": modes,
        "counterfactual_validation_macro_drops": drops,
        "counterfactual_min_macro_drop": float(min_macro_drop),
        "counterfactual_max_macro_drop": float(max_drop),
        "counterfactual_passing_modes": passing_modes,
        "counterfactual_min_passing_modes": int(required_modes),
        "n_rejected_by_counterfactual_guard": 0 if admitted else len(edges),
    }


def _apply_validation_gain_guard(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    min_macro_gain: float,
    n_edges: int,
) -> tuple[bool, dict[str, Any]]:
    baseline_macro = float(baseline["validation_metrics"]["macro_f1"])
    candidate_macro = float(candidate["validation_metrics"]["macro_f1"])
    gain = float(candidate_macro - baseline_macro)
    admitted = bool(gain >= float(min_macro_gain))
    return admitted, {
        "validation_macro_f1_baseline": baseline_macro,
        "validation_macro_f1_candidate": candidate_macro,
        "validation_macro_f1_gain": gain,
        "edge_min_validation_macro_gain": float(min_macro_gain),
        "n_rejected_by_validation_gain_guard": 0 if admitted else int(n_edges),
    }


def run_experiment(args: argparse.Namespace) -> dict[str, Any]:
    dataset_root = Path(args.dataset_root)
    x_raw, y_raw, meta = load_skab_dataset(dataset_root)
    y = np.asarray(y_raw, dtype=np.int64)
    allowed_features = [
        str(col)
        for col in x_raw.columns
        if col not in {"run_id", "run_group", "sample_index"} and np.issubdtype(x_raw[col].dtype, np.number)
    ]
    previous_path = Path(args.previous_result)
    error_summary = _load_previous_error_summary(previous_path, seed=int(args.seed), branch=str(args.error_branch))
    dynamic_edges: list[dict[str, Any]] = []
    parse_diag: dict[str, Any] = {"status": "skipped"}
    api_diag: dict[str, Any] = {"status": "skipped"}
    if str(getattr(args, "dynamic_edges_file", "") or "").strip():
        dynamic_edges, parse_diag = _load_dynamic_edges_file(
            Path(str(args.dynamic_edges_file)),
            max_edges=int(args.max_dynamic_edges),
        )
    else:
        prompt = build_skab_llm_graph_update_prompt(
            allowed_features=allowed_features,
            error_summary=error_summary,
            existing_edges=list(SKAB_LAGGED_MECHANISM_EDGES) + list(SKAB_LLM_MECHANISM_EDGE_CANDIDATES),
            max_edges=int(args.max_dynamic_edges),
        )
        response_text, api_diag = call_openai_skab_graph_proposer(
            prompt,
            model=str(args.model),
            timeout_seconds=float(args.api_timeout),
        )
        if response_text:
            try:
                dynamic_edges, parse_diag = parse_skab_llm_edge_proposals(
                    response_text,
                    allowed_features=allowed_features,
                    max_edges=int(args.max_dynamic_edges),
                    max_lag=12,
                    reliability_cap=0.72,
                )
            except Exception as exc:  # pragma: no cover - defensive experiment output
                parse_diag = {"status": "error", "reason": str(exc)}
    if not dynamic_edges and not bool(args.allow_empty_dynamic):
        return {
            "status": "api_no_dynamic_edges",
            "task": "skab_dynamic_llm_graph_api_experiment",
            "model": str(args.model),
            "api": api_diag,
            "parse": parse_diag,
            "error_summary": error_summary,
            "allowed_feature_count": int(len(allowed_features)),
        }
    dynamic_edges, merge_diag = merge_skab_dynamic_llm_edges(
        [],
        dynamic_edges,
        max_dynamic_edges=int(args.max_dynamic_edges),
    )
    if str(args.edge_policy) == "learned_reliability":
        dynamic_edges, reliability_diag = _filter_edges_by_reliability(
            dynamic_edges,
            threshold=float(args.edge_reliability_threshold),
        )
    else:
        reliability_diag = {
            "n_input_edges": len(dynamic_edges),
            "n_kept_after_reliability": len(dynamic_edges),
            "n_rejected_by_reliability": 0,
            "edge_reliability_threshold": None,
        }

    sequence_windows, sequence_feature_cols = build_skab_causal_sequence_windows(
        x_raw,
        meta,
        window_size=int(args.sequence_window_size),
        include_valid_mask=True,
    )
    train_runs, val_runs, test_runs = split_skab_runs(
        meta,
        seed=int(args.seed),
        test_size=0.30,
        val_fraction=0.25,
    )
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
        "sequence_feature_cols": sequence_feature_cols,
        "sequence_window_size": int(args.sequence_window_size),
        "epochs": int(args.sequence_epochs),
        "hidden_dim": int(args.sequence_hidden_dim),
        "batch_size": int(args.sequence_batch_size),
    }
    baseline = _train_msfg_time_context_branch(
        **common,
        dynamic_llm_edges=None,
        seed=int(args.seed) + 8200,
    )
    dynamic = _train_msfg_time_context_branch(
        **common,
        dynamic_llm_edges=dynamic_edges,
        seed=int(args.seed) + 8200,
    )
    validation_admitted, validation_diag = _apply_validation_gain_guard(
        baseline=baseline,
        candidate=dynamic,
        min_macro_gain=float(args.edge_min_validation_macro_gain),
        n_edges=len(dynamic_edges),
    )
    guard_modes = [str(mode) for mode in list(args.edge_counterfactual_guard_modes or [])]
    if validation_admitted and guard_modes and dynamic_edges:
        cf_admitted, cf_diag = _apply_counterfactual_guard(
            candidate=dynamic,
            common=common,
            edges=dynamic_edges,
            modes=guard_modes,
            min_macro_drop=float(args.edge_counterfactual_min_macro_drop),
            min_passing_modes=int(args.edge_counterfactual_min_passing_modes),
            allowed_features=allowed_features,
            seed=int(args.seed),
        )
    else:
        cf_admitted, cf_diag = True, {
            "counterfactual_guard_modes": guard_modes,
            "counterfactual_validation_macro_drops": {},
            "counterfactual_min_macro_drop": float(args.edge_counterfactual_min_macro_drop),
            "counterfactual_max_macro_drop": 0.0,
            "counterfactual_passing_modes": [],
            "counterfactual_min_passing_modes": int(args.edge_counterfactual_min_passing_modes),
            "n_rejected_by_counterfactual_guard": 0,
            "counterfactual_guard_skipped": "validation_gain_guard_rejected" if not validation_admitted else "no_guard_modes_or_edges",
        }
    admitted = bool(validation_admitted and cf_admitted)
    final_dynamic = dynamic if admitted else baseline
    edge_policy = {
        "policy": str(args.edge_policy),
        **merge_diag,
        **reliability_diag,
        **validation_diag,
        **cf_diag,
        "n_kept_edges": len(dynamic_edges) if admitted else 0,
        "admitted": bool(admitted),
        "edge_max_far_increase_percent": float(args.edge_max_far_increase_percent),
    }
    return {
        "status": "ok",
        "task": "skab_dynamic_llm_graph_api_experiment",
        "model": str(args.model),
        "seed": int(args.seed),
        "sequence_epochs": int(args.sequence_epochs),
        "edge_probe_epochs": int(getattr(args, "edge_probe_epochs", 0) or 0),
        "api": api_diag,
        "parse": parse_diag,
        "error_summary": error_summary,
        "dynamic_edges": dynamic_edges if admitted else [],
        "candidate_dynamic_edges": dynamic_edges,
        "edge_policy": edge_policy,
        "baseline": baseline,
        "dynamic_llm_kg": final_dynamic,
        "macro_f1_delta": float(final_dynamic["metrics"]["macro_f1"] - baseline["metrics"]["macro_f1"]),
        "point_adjusted_f1_delta": float(
            final_dynamic["protocol"]["point_adjusted"]["f1"] - baseline["protocol"]["point_adjusted"]["f1"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SKAB dynamic LLM graph API experiment.")
    parser.add_argument("--dataset-root", default=str(DEFAULT_PUBLIC_DATASET_ROOT))
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sequence-window-size", type=int, default=32)
    parser.add_argument("--sequence-epochs", type=int, default=3)
    parser.add_argument("--sequence-hidden-dim", type=int, default=32)
    parser.add_argument("--sequence-batch-size", type=int, default=512)
    parser.add_argument("--max-dynamic-edges", type=int, default=8)
    parser.add_argument("--api-timeout", type=float, default=45.0)
    parser.add_argument("--dynamic-edges-file", default="")
    parser.add_argument("--edge-policy", choices=["none", "learned_reliability"], default="none")
    parser.add_argument(
        "--edge-probe-epochs",
        type=int,
        default=0,
        help="Compatibility field recorded for CF-suite provenance; dynamic-edge reliability is loaded or API-proposed.",
    )
    parser.add_argument("--edge-reliability-threshold", type=float, default=0.45)
    parser.add_argument("--edge-max-far-increase-percent", type=float, default=1.0)
    parser.add_argument("--edge-min-validation-macro-gain", type=float, default=0.0)
    parser.add_argument(
        "--edge-counterfactual-guard-modes",
        nargs="*",
        default=[],
        choices=sorted(COUNTERFACTUAL_MODES),
    )
    parser.add_argument("--edge-counterfactual-min-macro-drop", type=float, default=0.01)
    parser.add_argument("--edge-counterfactual-min-passing-modes", type=int, default=1)
    parser.add_argument(
        "--previous-result",
        default=str(DEFAULT_PUBLIC_DATASET_ROOT.parent / "public_benchmark_skab_dynamic_gate_3seeds_e5.json"),
    )
    parser.add_argument("--error-branch", default="dynamic_graph_tcn_gate")
    parser.add_argument("--allow-empty-dynamic", action="store_true")
    args = parser.parse_args()
    result = run_experiment(args)
    output = Path(args.output)
    os.makedirs(_fs_path(output.parent), exist_ok=True)
    _write_text(output, json.dumps(result, indent=2, ensure_ascii=False))
    if result.get("status") == "ok":
        base = result["baseline"]["metrics"]["macro_f1"]
        dyn = result["dynamic_llm_kg"]["metrics"]["macro_f1"]
        print(
            f"status=ok model={result['model']} baseline_macro={base:.4f} "
            f"dynamic_macro={dyn:.4f} delta={result['macro_f1_delta']:+.4f} "
            f"dynamic_edges={len(result['dynamic_edges'])}"
        )
    else:
        print(f"status={result.get('status')} model={result.get('model')} api={result.get('api')}")


if __name__ == "__main__":
    main()
