from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


VERSION = "aaai-claim-boundary-v1"
SEEDS = [42, 43, 44]


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _dataset_protocols() -> list[dict[str, Any]]:
    return [
        {
            "name": "TEP",
            "role": "main strict multiclass benchmark",
            "split": "fault-run-aware train/validation/test split; no window overlap across split boundaries",
            "window_or_label": "strict 22-class fault labels with process windows and lag/residual graph evidence",
            "primary_metric": "Target-F1 over 22 classes",
            "thresholding": "validation-only tau_R/tau_q selection; test used once",
            "budget": "seeds 42/43/44; shared threshold grid; matched preprocessing for all baselines",
        },
        {
            "name": "SKAB",
            "role": "binary anomaly reliability stress test",
            "split": "time-series split by scenario/run with changepoint leakage blocked",
            "window_or_label": "binary anomaly windows; formal runs use 48-step windows and validation-only thresholds",
            "primary_metric": "Macro-F1 with FAR/MAR safety diagnostics",
            "thresholding": "thresholds selected on validation only",
            "budget": "seeds 42/43/44; hidden_dim 64; max_paths 16; 40 epochs; no test-threshold tuning",
        },
        {
            "name": "Hydraulic",
            "role": "non-degradation safety evidence",
            "split": "cycle-level split following target-specific operating states",
            "window_or_label": "per-target equipment health labels",
            "primary_metric": "per-target F1 and non-degradation count",
            "thresholding": "validation-only admission; no target-specific test tuning",
            "budget": "seeds 42/43/44; report Cooler/Valve/Pump/Accumulator separately",
        },
        {
            "name": "C-MAPSS",
            "role": "original RUL generalization evidence",
            "split": "FD001-FD004 train/test protocol with validation carved from training units",
            "window_or_label": "original remaining useful life regression; degradation-stage labels are auxiliary only",
            "primary_metric": "RUL RMSE, RUL MAE, and PHM-style RUL score",
            "thresholding": "no class-threshold tuning for primary RUL metric; validation-only route/admission selection",
            "budget": "seeds 42/43/44; pooled and per-subset RUL reporting",
        },
    ]


def _command_template(model: str, dataset: str = "TEP") -> str:
    return (
        "python Scripts/protocol_aligned_external_baseline_runner.py "
        f"--dataset {dataset} --model \"{model}\" --seed 42 "
        "--protocol matched --validation-only-thresholds "
        "--budget-status local_matched_adapter_probe"
    )


def _baseline_obligations() -> list[dict[str, Any]]:
    return [
        {
            "family": "temporal sequence",
            "name": "TCN",
            "status": "materialized_matched_protocol",
            "datasets": ["TEP"],
            "command_template": _command_template("TCN"),
            "checks": ["matched_preprocessing", "same_seeds", "same_metric"],
        },
        {
            "family": "temporal sequence",
            "name": "GRU",
            "status": "materialized_matched_protocol",
            "datasets": ["TEP"],
            "command_template": _command_template("GRU"),
            "checks": ["matched_preprocessing", "same_seeds", "same_metric"],
        },
        {
            "family": "temporal sequence",
            "name": "FT-Transformer",
            "status": "materialized_matched_protocol",
            "datasets": ["TEP"],
            "command_template": _command_template("FT-Transformer"),
            "checks": ["matched_preprocessing", "same_seeds", "same_metric"],
        },
        {
            "family": "temporal sequence",
            "name": "PatchTST",
            "status": "materialized_official_source_adapted_control",
            "datasets": ["TEP", "SKAB"],
            "command_template": (
                "python Scripts/run_patchtst_tep_official_wrapper.py "
                "--seeds 42,43,44 --max-rows 20000 --window-size 32 --epochs 10 --device auto"
            ),
            "checks": [
                "official_source_checkout_verified",
                "same_seeds",
                "validation_only_model_selection",
                "official_external_score_false",
                "no_public_leaderboard_claim",
            ],
            "score_artifact": "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_budget_probe.json",
            "official_external_score": False,
        },
        {
            "family": "temporal sequence",
            "name": "Anomaly Transformer",
            "status": "materialized_official_source_adapted_control",
            "datasets": ["SKAB", "TEP"],
            "command_template": (
                "python Scripts/run_anomaly_transformer_skab_official_wrapper.py "
                "--adapter-root knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_adapter "
                "--checkout C:\\Users\\CPILAB\\aaai_external_baseline_checkouts\\anomaly_transformer "
                "--seeds 42,43,44 --epochs 5"
            ),
            "checks": [
                "official_source_checkout_verified",
                "same_seeds",
                "validation_only_threshold",
                "point_adjustment_disabled",
                "official_external_score_false",
                "no_public_leaderboard_claim",
            ],
            "score_artifact": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json",
            "official_external_score": False,
        },
        {
            "family": "temporal sequence",
            "name": "TranAD",
            "status": "materialized_style_baseline",
            "datasets": ["SKAB"],
            "command_template": _command_template("TranAD", "SKAB"),
            "checks": ["matched_windowing", "same_metric", "external_style_not_official_leaderboard"],
        },
        {
            "family": "graph temporal",
            "name": "GDN",
            "status": "materialized_style_baseline",
            "datasets": ["SKAB", "TEP"],
            "command_template": _command_template("GDN", "SKAB"),
            "checks": ["matched_windowing", "same_metric", "external_style_not_official_leaderboard"],
        },
        {
            "family": "graph temporal",
            "name": "MTAD-GAT",
            "status": "materialized_style_baseline",
            "datasets": ["SKAB", "TEP"],
            "command_template": _command_template("MTAD-GAT", "SKAB"),
            "checks": ["matched_windowing", "same_metric", "external_style_not_official_leaderboard"],
        },
        {
            "family": "graph temporal",
            "name": "Graph WaveNet",
            "status": "materialized_official_source_adapted_control",
            "datasets": ["TEP"],
            "command_template": (
                "python Scripts/run_graph_wavenet_tep_official_wrapper.py "
                "--seeds 42,43,44 --max-rows 20000 --window-size 32 --epochs 10 --device auto"
            ),
            "checks": [
                "official_source_checkout_verified",
                "same_seeds",
                "graph_input_contract_declared",
                "validation_only_model_selection",
                "official_external_score_false",
                "no_public_leaderboard_claim",
            ],
            "score_artifact": "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_budget_probe.json",
            "official_external_score": False,
        },
        {
            "family": "RUL tabular-sequence summary",
            "name": "C-MAPSS Ridge/HistGB/ExtraTrees",
            "status": "materialized_matched_protocol",
            "datasets": ["C-MAPSS"],
            "command_template": (
                "python Scripts/run_cmapss_rul_baselines.py --seeds 42,43,44 "
                "--use-regime-prototype-residuals --window-size 80"
            ),
            "checks": ["terminal_test_unit_rul", "same_seeds", "same_ready_data", "fd001_fd004_subset_metrics"],
        },
        {
            "family": "RUL temporal sequence",
            "name": "C-MAPSS GRU/TCN RUL",
            "status": "materialized_matched_protocol",
            "datasets": ["C-MAPSS"],
            "command_template": (
                "python Scripts/run_cmapss_rul_baselines.py --baselines gru_sequence,tcn_sequence "
                "--seeds 42,43,44 --use-regime-prototype-residuals --window-size 80 --device cuda"
            ),
            "checks": ["terminal_test_unit_rul", "same_seeds", "same_ready_data", "deep_sequence_runner_materialized"],
        },
    ]


def _gate_obligations() -> list[dict[str, Any]]:
    return [
        {
            "name": "ordinary gate",
            "optimization": "end-to-end prediction loss",
            "must_control": [],
            "purpose": "tests whether a learned soft gate is enough",
        },
        {
            "name": "attention gate",
            "optimization": "attention-weighted challenger fusion",
            "must_control": [],
            "purpose": "tests whether edge or token attention explains the gain",
        },
        {
            "name": "validation-only gate",
            "optimization": "mean validation gain",
            "must_control": ["G_k"],
            "purpose": "tests whether mean validation gain is sufficient without harm and perturbation evidence",
        },
        {
            "name": "complete reliability admission",
            "optimization": "global admission plus local ERE routing",
            "must_control": ["G_k", "H_k", "C_k", "S_k", "B_k"],
            "purpose": "target method; deployment risk control before bounded correction",
        },
    ]


def _ablation_plan() -> list[dict[str, Any]]:
    variants = [
        ("Anchor only", "remove all challengers and reliability correction"),
        ("Unfiltered evidence", "use all generated evidence without reliability admission"),
        ("Expert only", "keep expert mechanism evidence; remove LLM/statistical sources"),
        ("LLM only", "keep LLM-generated weak-class rules; remove expert/statistical sources"),
        ("Lag/residual only", "keep lag and residual triggers; remove expert/LLM graph evidence"),
        ("Graph only", "keep graph path evidence; remove residual and source reliability channels"),
        ("No counterfactual guard", "remove C_k perturbation-dependence admission"),
        ("No tail safety", "remove H_k low-tail harm control"),
        ("No complexity penalty", "remove B_k path/source burden"),
        ("Full model", "use all source, safety, perturbation, and routing terms"),
    ]
    return [{"name": name, "intervention": intervention} for name, intervention in variants]


def build_manifest() -> dict[str, Any]:
    return {
        "version": VERSION,
        "seeds": SEEDS,
        "claim_boundary": {
            "positive_claim": "matched-protocol method evidence",
            "forbidden_claim_until_complete": "official all-benchmark leaderboard dominance",
            "rule": "Official-source adapted controls are completed matched-protocol controls, not official external leaderboard scores.",
        },
        "global_admission_rule": {
            "same_equation_across_datasets": True,
            "validation_only_selection": True,
            "tau_R_grid": [0.55, 0.60, 0.65, 0.70],
            "tau_q_grid": [0.50, 0.60, 0.70],
            "terms": ["G_k", "H_k", "C_k", "S_k", "B_k"],
            "invariants": [
                "No test-set threshold or route tuning",
                "Same reliability equation across datasets",
                "Official-source adapted controls must keep official_external_score=false",
                "Public leaderboard wording requires exact native benchmark reproduction",
            ],
        },
        "datasets": _dataset_protocols(),
        "baseline_obligations": _baseline_obligations(),
        "reliability_gate_obligations": _gate_obligations(),
        "systematic_ablation_plan": _ablation_plan(),
    }


def render_markdown(manifest: dict[str, Any]) -> str:
    lines: list[str] = [
        "# AAAI Experiment Execution Manifest",
        "",
        "This manifest turns the remaining paper claims into executable, auditable obligations. Pending items are not completed result claims.",
        "",
        "## Global Rule",
        "",
        f"- Seeds: {', '.join(str(seed) for seed in manifest['seeds'])}",
        f"- tau_R grid: {manifest['global_admission_rule']['tau_R_grid']}",
        f"- tau_q grid: {manifest['global_admission_rule']['tau_q_grid']}",
        "- No test-set threshold or route tuning.",
        "- Same reliability equation across datasets.",
        "",
        "## Dataset Protocols",
        "",
        "| Dataset | Role | Split | Primary metric |",
        "|---|---|---|---|",
    ]
    for dataset in manifest["datasets"]:
        lines.append(
            f"| {dataset['name']} | {dataset['role']} | {dataset['split']} | {dataset['primary_metric']} |"
        )

    lines.extend([
        "",
        "## Baseline Obligations",
        "",
        "| Family | Method | Status | Checks | Command template |",
        "|---|---|---|---|---|",
    ])
    for baseline in manifest["baseline_obligations"]:
        checks = ", ".join(baseline["checks"])
        lines.append(
            f"| {baseline['family']} | {baseline['name']} | {baseline['status']} | {checks} | `{baseline['command_template']}` |"
        )

    lines.extend([
        "",
        "## Reliability/Gating Controls",
        "",
        "| Method | Optimization | Required controls | Purpose |",
        "|---|---|---|---|",
    ])
    for gate in manifest["reliability_gate_obligations"]:
        controls = ", ".join(gate["must_control"]) if gate["must_control"] else "none"
        lines.append(f"| {gate['name']} | {gate['optimization']} | {controls} | {gate['purpose']} |")

    lines.extend([
        "",
        "## Systematic Ablation Plan",
        "",
        "| Variant | Intervention |",
        "|---|---|",
    ])
    for ablation in manifest["systematic_ablation_plan"]:
        lines.append(f"| {ablation['name']} | {ablation['intervention']} |")

    lines.extend([
        "",
        "## Claim Boundary",
        "",
        f"- Positive claim: {manifest['claim_boundary']['positive_claim']}.",
        f"- Forbidden until complete: {manifest['claim_boundary']['forbidden_claim_until_complete']}.",
        f"- Rule: {manifest['claim_boundary']['rule']}",
        "",
    ])
    return "\n".join(lines)


def build_execution_manifest(output_dir: Path) -> list[Path]:
    output_dir = Path(output_dir)
    Path(_fs_path(output_dir)).mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()

    json_path = output_dir / "aaai_experiment_execution_manifest.json"
    with open(_fs_path(json_path), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    markdown_path = output_dir / "aaai_experiment_execution_manifest.md"
    with open(_fs_path(markdown_path), "w", encoding="utf-8") as fh:
        fh.write(render_markdown(manifest))
    return [json_path, markdown_path]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AAAI experiment execution manifest.")
    parser.add_argument("--output-dir", type=Path, default=Path("knowledge_exports") / "aaai_experiment_manifest")
    args = parser.parse_args()
    for path in build_execution_manifest(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
