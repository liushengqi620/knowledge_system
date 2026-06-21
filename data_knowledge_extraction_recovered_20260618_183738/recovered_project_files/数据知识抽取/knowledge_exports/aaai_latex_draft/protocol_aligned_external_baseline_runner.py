from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence

from pending_baseline_alignment_artifact import build_alignment_artifact
from run_tep_sequence_graph_ablation import run_ablation_suite
from public_benchmark_experiment import DEFAULT_PUBLIC_DATASET_ROOT
from skab_external_baselines import run_skab_external_baselines
from tep_sequence_heads import DEFAULT_TEP_DATASET_DIR


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "knowledge_exports" / "external_baseline_protocol_runs"
DEFAULT_ALIGNMENT_ROOT = PROJECT_ROOT / "knowledge_exports" / "aaai_external_baseline_alignment_decision"

MODEL_ALIASES = {
    "patchtst": "patchtst",
    "patch_tst": "patchtst",
    "patchtst-style": "patchtst",
    "anomaly_transformer": "anomaly_transformer",
    "anomaly-transformer": "anomaly_transformer",
    "anomaly transformer": "anomaly_transformer",
    "graph_wavenet": "graph_wavenet",
    "graph-wavenet": "graph_wavenet",
    "graph wavenet": "graph_wavenet",
}

DISPLAY_NAMES = {
    "patchtst": "PatchTST",
    "anomaly_transformer": "Anomaly Transformer",
    "graph_wavenet": "Graph WaveNet",
}

SUPPORTED_LOCAL_ADAPTERS = {
    ("tep", "patchtst"),
    ("tep", "anomaly_transformer"),
    ("tep", "graph_wavenet"),
    ("skab", "anomaly_transformer"),
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _normalise_model(name: str) -> str:
    key = str(name).strip().lower().replace("_style", "")
    key = key.replace("  ", " ")
    if key not in MODEL_ALIASES:
        raise ValueError(f"Unsupported external baseline model: {name}")
    return MODEL_ALIASES[key]


def _normalise_dataset(name: str) -> str:
    value = str(name).strip().lower()
    if value not in {"tep", "skab"}:
        raise ValueError(f"Unsupported external baseline dataset: {name}")
    return value


def _split_seeds(seed: int | None, seeds: str | Sequence[int] | None) -> list[int]:
    values: list[int] = []
    if seeds is not None and str(seeds).strip():
        if isinstance(seeds, str):
            values.extend(int(part.strip()) for part in seeds.replace(";", ",").split(",") if part.strip())
        else:
            values.extend(int(item) for item in seeds)
    if seed is not None:
        values.append(int(seed))
    if not values:
        values.append(42)
    deduped: list[int] = []
    for value in values:
        if value not in deduped:
            deduped.append(int(value))
    return deduped


def _seed_slug(seeds: Sequence[int]) -> str:
    return "s" + "_".join(str(int(seed)) for seed in seeds)


def _default_result_path(dataset: str, model: str, seeds: Sequence[int], output_root: Path) -> Path:
    return Path(output_root) / f"{dataset}_{model}_{_seed_slug(seeds)}.json"


def _default_alignment_path(dataset: str, model: str, seeds: Sequence[int], alignment_root: Path) -> Path:
    return Path(alignment_root) / f"{model}_{dataset}_{_seed_slug(seeds)}_protocol_runner_alignment_artifact.json"


def build_runner_plan(
    *,
    dataset: str,
    model: str,
    seed: int | None = None,
    seeds: str | Sequence[int] | None = None,
    protocol: str = "matched",
    validation_only_thresholds: bool = False,
    output: Path | str | None = None,
    alignment_output: Path | str | None = None,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    alignment_root: Path | str = DEFAULT_ALIGNMENT_ROOT,
    max_rows: int | None = 3000,
    window_size: int = 16,
    hidden_dim: int = 32,
    epochs: int = 3,
    batch_size: int = 256,
    variants: str = "no_graph",
    device: str = "auto",
    budget_status: str = "local_matched_adapter_probe",
) -> dict[str, Any]:
    dataset_key = _normalise_dataset(dataset)
    model_key = _normalise_model(model)
    seed_values = _split_seeds(seed, seeds)
    if str(protocol).strip().lower() != "matched":
        raise ValueError("Only the matched protocol is supported by this runner.")
    result_path = Path(output) if output else _default_result_path(dataset_key, model_key, seed_values, Path(output_root))
    alignment_path = (
        Path(alignment_output)
        if alignment_output
        else _default_alignment_path(dataset_key, model_key, seed_values, Path(alignment_root))
    )
    supported = (dataset_key, model_key) in SUPPORTED_LOCAL_ADAPTERS
    return {
        "schema": "aaai_external_baseline_protocol_runner_v1",
        "status": "ready" if supported else "unsupported_protocol_pair",
        "dataset": dataset_key.upper(),
        "model": DISPLAY_NAMES[model_key],
        "normalized_model": model_key,
        "protocol": "matched",
        "validation_only_thresholds": bool(validation_only_thresholds),
        "seeds": [int(seed) for seed in seed_values],
        "budget_status": str(budget_status),
        "claim_boundary": (
            "This runner produces local matched-adapter artifacts only. It does not produce an official external "
            "paper score and must not be used for public SOTA wording until exact repository/protocol/budget "
            "alignment passes."
        ),
        "supported_local_adapter": bool(supported),
        "unsupported_reason": "" if supported else "No faithful local adapter runner is materialized for this dataset/model pair.",
        "result_path": str(result_path),
        "alignment_artifact_path": str(alignment_path),
        "runner_contract": {
            "accepts_declared_dataset_seed_split_window_arguments": True,
            "uses_validation_only_threshold_flag": bool(validation_only_thresholds),
            "writes_metric_json": True,
            "writes_config_and_command_provenance": True,
            "writes_alignment_artifact_with_hash": True,
            "official_external_score": False,
        },
        "execution": {
            "dataset_dir": str(DEFAULT_TEP_DATASET_DIR) if dataset_key == "tep" else "",
            "dataset_root": str(DEFAULT_PUBLIC_DATASET_ROOT) if dataset_key == "skab" else "",
            "max_rows": int(max_rows) if max_rows is not None and int(max_rows) > 0 else None,
            "window_size": int(window_size),
            "hidden_dim": int(hidden_dim),
            "epochs": int(epochs),
            "batch_size": int(batch_size),
            "variants": str(variants),
            "device": str(device),
        },
    }


def execute_runner_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("status") != "ready":
        raise ValueError(str(plan.get("unsupported_reason") or "Runner plan is not executable."))
    dataset = str(plan["dataset"]).lower()
    execution = dict(plan.get("execution", {}) or {})
    result_path = Path(str(plan["result_path"]))
    if dataset == "tep":
        variants = [part.strip() for part in str(execution.get("variants", "no_graph")).split(",") if part.strip()]
        result = run_ablation_suite(
            dataset_dir=Path(str(execution["dataset_dir"])),
            output_path=result_path,
            model_name=str(plan["normalized_model"]),
            seeds=[int(seed) for seed in plan["seeds"]],
            max_rows=execution.get("max_rows"),
            window_size=int(execution["window_size"]),
            hidden_dim=int(execution["hidden_dim"]),
            epochs=int(execution["epochs"]),
            batch_size=int(execution["batch_size"]),
            normal_pretrain_epochs=1,
            normal_residual_features=False,
            graph_strength=0.0,
            reliability_threshold=0.0,
            max_edges=None,
            graph_prior_name="tep_expert_llm_graph_prior.json",
            apply_llm_rerank=False,
            include_residual_gated=False,
            selected_variants=variants,
            resume=True,
            device=str(execution["device"]),
        )
    elif dataset == "skab" and str(plan["normalized_model"]) == "anomaly_transformer":
        result = run_skab_external_baselines(
            Path(str(execution["dataset_root"])),
            result_path,
            seeds=[int(seed) for seed in plan["seeds"]],
            methods=["anomaly_transformer"],
            window_size=int(execution["window_size"]),
            epochs=int(execution["epochs"]),
            hidden_dim=int(execution["hidden_dim"]),
            batch_size=int(execution["batch_size"]),
        )
    else:
        raise ValueError(f"No executable local adapter route for {plan['dataset']} / {plan['model']}.")
    artifact = build_alignment_artifact(
        source_result=result_path,
        output=Path(str(plan["alignment_artifact_path"])),
        baseline=str(plan["model"]),
        dataset=str(plan["dataset"]),
        budget_status=str(plan["budget_status"]),
        admissibility="not_admissible_until_exact_external_alignment",
        notes=plan["claim_boundary"],
    )
    return {
        **plan,
        "status": "executed_local_matched_adapter",
        "result_summary": result.get("summary", {}),
        "alignment_artifact": artifact,
    }


def write_payload(path: Path | str, payload: dict[str, Any]) -> None:
    out = Path(path)
    os.makedirs(_fs_path(out.parent), exist_ok=True)
    with open(_fs_path(out), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run protocol-aligned local adapters for pending external baselines.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--seeds", default="")
    parser.add_argument("--protocol", default="matched")
    parser.add_argument("--validation-only-thresholds", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--alignment-output", type=Path, default=None)
    parser.add_argument("--plan-output", type=Path, default=None)
    parser.add_argument("--max-rows", type=int, default=3000)
    parser.add_argument("--window-size", type=int, default=16)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--variants", default="no_graph")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--budget-status", default="local_matched_adapter_probe")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    plan = build_runner_plan(
        dataset=args.dataset,
        model=args.model,
        seed=args.seed,
        seeds=args.seeds,
        protocol=args.protocol,
        validation_only_thresholds=bool(args.validation_only_thresholds),
        output=args.output,
        alignment_output=args.alignment_output,
        max_rows=int(args.max_rows) if int(args.max_rows) > 0 else None,
        window_size=int(args.window_size),
        hidden_dim=int(args.hidden_dim),
        epochs=int(args.epochs),
        batch_size=int(args.batch_size),
        variants=str(args.variants),
        device=str(args.device),
        budget_status=str(args.budget_status),
    )
    payload = plan if bool(args.dry_run) else execute_runner_plan(plan)
    if args.plan_output:
        write_payload(args.plan_output, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
