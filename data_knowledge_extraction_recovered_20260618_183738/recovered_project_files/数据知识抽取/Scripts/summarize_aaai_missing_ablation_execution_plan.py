from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = REPO_ROOT / "knowledge_exports"
DEFAULT_OUTPUT_DIR = EXPORT_DIR


PYTHON = r"C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe"
ENV_PREFIX = "$env:KMP_DUPLICATE_LIB_OK='TRUE'; $env:PYTHONPATH='Scripts';"
SEEDS = [42, 43, 44]
TAIL_POLICY_REPLAY = (
    EXPORT_DIR
    / "aaai_missing_ablation_runs"
    / "skab_tail_safety_policy_replay"
    / "skab_tail_safety_policy_replay.json"
)
NO_COMPLEXITY_MATRIX = (
    EXPORT_DIR
    / "aaai_missing_ablation_runs"
    / "skab_no_complexity_full"
    / "mechanism_gate_ablation_matrix.json"
)
NO_CF_FORMAL_SUMMARY = (
    EXPORT_DIR
    / "aaai_missing_ablation_runs"
    / "skab_cf_subset_formal_summary"
    / "skab_cf_subset_formal_summary.json"
)


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path | str) -> bool:
    return os.path.exists(_fs_path(path))


def _read_json(path: Path | str) -> dict[str, Any]:
    if not _exists(path):
        return {}
    try:
        with open(_fs_path(path), encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {}


def _command(script: str, *args: str) -> str:
    return " ".join([ENV_PREFIX, f"& '{PYTHON}'", script, *args])


def _skab_no_cf_commands() -> list[str]:
    commands = []
    commands.append(
        _command(
            "Scripts/export_skab_cf_candidate_edges.py",
            "--seeds 42,43,44",
            "--max-edges 8",
            "--min-reliability 0.20",
            "--max-data-edges 24",
        )
    )
    for seed in SEEDS:
        commands.append(
            _command(
                "Scripts/sweep_skab_dynamic_edge_subsets.py",
                f"--seed {seed}",
                "--sequence-epochs 1",
                "--max-subset-size 2",
                "--edge-reliability-threshold 0.45",
                "--write-best-cache",
                "--output-dir knowledge_exports/aaai_missing_ablation_runs/skab_edge_subset_sweep_formal_prep",
            )
        )
    for seed in SEEDS:
        best_edges = f"knowledge_exports/aaai_missing_ablation_runs/skab_edge_subset_sweep_formal_prep/seed{seed}_best_validated_edges.json"
        commands.append(
            _command(
                "Scripts/run_skab_dynamic_llm_graph_experiment.py",
                f"--seed {seed}",
                "--sequence-epochs 8",
                "--edge-policy learned_reliability",
                "--edge-reliability-threshold 0.45",
                f"--dynamic-edges-file {best_edges}",
                "--edge-counterfactual-guard-modes reverse_direction lag_shift random_target",
                "--edge-counterfactual-min-macro-drop 0.01",
                "--edge-counterfactual-min-passing-modes 1",
                (
                    "--output "
                    f"knowledge_exports/aaai_missing_ablation_runs/skab_cf_guarded_subset_formal/seed{seed}.json"
                ),
            )
        )
    for seed in SEEDS:
        best_edges = f"knowledge_exports/aaai_missing_ablation_runs/skab_edge_subset_sweep_formal_prep/seed{seed}_best_validated_edges.json"
        commands.append(
            _command(
                "Scripts/run_skab_dynamic_llm_graph_experiment.py",
                f"--seed {seed}",
                "--sequence-epochs 8",
                "--edge-policy learned_reliability",
                "--edge-reliability-threshold 0.45",
                f"--dynamic-edges-file {best_edges}",
                (
                    "--output "
                    f"knowledge_exports/aaai_missing_ablation_runs/skab_no_counterfactual_guard/seed{seed}.json"
                ),
            )
        )
    return commands


def build_execution_plan() -> dict[str, Any]:
    tail_policy = _read_json(TAIL_POLICY_REPLAY)
    no_complexity = _read_json(NO_COMPLEXITY_MATRIX)
    no_cf_formal = _read_json(NO_CF_FORMAL_SUMMARY)
    no_complexity_variants = {str(row.get("variant", "")) for row in no_complexity.get("summary", [])}
    tail_complete = tail_policy.get("status") == "complete_policy_replay"
    no_cf_complete = no_cf_formal.get("status") == "complete_formal"
    no_complexity_complete = {
        "expert_llm_candidate_data_gate_no_complexity",
        "expert_llm_candidate_data_gate_complexity_guarded",
    }.issubset(no_complexity_variants)
    rows = [
        {
            "ablation": "No counterfactual guard",
            "dataset": "SKAB primary; optional TEP confirmation after SKAB closes",
            "purpose": (
                "Isolate the counterfactual-relevance term by comparing the current CF-guarded "
                "admission policy against the identical candidate set with the CF check disabled."
            ),
            "status": "requires_formal_three_seed_run",
            "must_hold_fixed": [
                "same train/validation/test split",
                "same anchor checkpoint family",
                "same expert/algorithmic/LLM candidate pool",
                "same validation threshold grid except the CF switch",
                "same seeds 42,43,44",
            ],
            "primary_metrics": [
                "macro_f1",
                "weak-class macro_f1",
                "admitted_edge_count",
                "counterfactual_drop_by_reverse/lag/target perturbation",
            ],
            "minimum_artifacts": [
                "per-seed metrics JSON",
                "per-seed admitted edge/path manifest",
                "counterfactual perturbation report",
                "aggregated mean/std table",
            ],
            "commands": [
                _command(
                    "Scripts/run_skab_cf_guard_suite.py",
                    "--seeds 42,43,44",
                    "--sequence-epochs 8",
                    "--probe-epochs 2",
                    "--guard-modes reverse_direction lag_shift random_target",
                    "--edge-reliability-threshold 0.45",
                    "--run",
                    (
                        "--summary-output "
                        "knowledge_exports/aaai_missing_ablation_runs/skab_cf_guarded/skab_cf_guarded_admission_suite.md"
                    ),
                ),
                *_skab_no_cf_commands(),
            ],
            "implementation_needed": (
                "The suite now falls back to the live OpenAI-compatible LLM path when cached edge files are absent. "
                "For reproducible formal runs, first export the frozen expert/static-LLM/train-data candidate pool, "
                "then run validation-only subset selection and use each seed's best validated edge file for both CF "
                "and no-CF branches. This keeps the candidate set fixed while removing only the CF term."
            ),
            "acceptance_rule": (
                "The row becomes paper-ready only if both branches produce three seed-level metric "
                "files and the only intended mechanism difference is the CF admission term."
            ),
        },
    ]
    closed_rows: list[dict[str, Any]] = []
    if no_cf_complete:
        rows = [row for row in rows if row.get("ablation") != "No counterfactual guard"]
        closed_rows.append(
            {
                "ablation": "No counterfactual guard",
                "status": "complete_seed_level_evidence",
                "artifact": "knowledge_exports/aaai_missing_ablation_runs/skab_cf_subset_formal_summary/skab_cf_subset_formal_summary.json",
                "note": "Matched CF/no-CF three-seed SKAB formal summary is complete; the effect is non-differential and should be reported as a reliability/interpretability guard.",
            }
        )
    tail_row = {
            "ablation": "No tail safety",
            "dataset": "SKAB primary; TEP weak/fault-family tail as secondary if runtime allows",
            "purpose": (
                "Remove only the low-tail safety term H_k to test whether validation-gain admission "
                "overfits majority classes or frequent regimes."
            ),
            "status": "requires_matched_tail_safety_run",
            "must_hold_fixed": [
                "same candidate pool and source priors",
                "same validation metric objective",
                "same complexity and CF checks",
                "same seeds 42,43,44",
            ],
            "primary_metrics": [
                "macro_f1",
                "low-tail class/group f1 delta",
                "worst-decile validation benefit",
                "admitted_edge_count",
            ],
            "minimum_artifacts": [
                "tail-group definition JSON",
                "per-seed low-tail metric JSON",
                "admitted candidate manifest",
                "mean/std safety table",
            ],
            "commands": [
                _command(
                    "Scripts/mechanism_gate_ablation_matrix.py",
                    "--seeds 42,43,44",
                    "--max-low-tail-f1-drop 0.02",
                    "--output-root knowledge_exports/aaai_missing_ablation_runs/skab_tail_guarded",
                    "--report-dir knowledge_exports/aaai_missing_ablation_runs/skab_tail_guarded",
                ),
                _command(
                    "Scripts/mechanism_gate_ablation_matrix.py",
                    "--seeds 42,43,44",
                    "--max-low-tail-f1-drop 999.0",
                    "--output-root knowledge_exports/aaai_missing_ablation_runs/skab_no_tail_safety",
                    "--report-dir knowledge_exports/aaai_missing_ablation_runs/skab_no_tail_safety",
                ),
            ],
            "acceptance_rule": (
                "The no-tail row must be labeled as a matched intervention, not a new model search. "
                "If the current script only replays admission policy, the report must say policy replay "
                "and the final scored model run remains pending."
            ),
        }
    complexity_row = {
            "ablation": "No complexity penalty",
            "dataset": "SKAB source-pruning study, with optional TEP candidate-pool confirmation",
            "purpose": (
                "Disable the source/complexity burden while preserving validation, low-tail, and CF checks, "
                "so the paper can show whether unsupported multi-source accumulation is genuinely controlled."
            ),
            "status": "requires_formal_three_seed_run",
            "must_hold_fixed": [
                "same expert+LLM candidate set",
                "same data-support calibration",
                "same validation and tail thresholds",
                "same CF guard",
                "same seeds 42,43,44",
            ],
            "primary_metrics": [
                "macro_f1",
                "admitted_edge_count",
                "admitted_source_family_count",
                "path_depth_or_burden_score",
                "metric variance across seeds",
            ],
            "minimum_artifacts": [
                "candidate source-family manifest",
                "per-seed admitted candidate manifest",
                "per-seed metric JSON",
                "complexity burden summary",
            ],
            "commands": [
                _command(
                    "Scripts/mechanism_gate_ablation_matrix.py",
                    "--seeds 42,43,44",
                    "--variants no_mechanism,expert_llm_candidate_data_gate_complexity_guarded,expert_llm_candidate_data_gate_no_complexity",
                    "--profile full",
                    "--min-baseline-path-jaccard 0.0",
                    "--output-root knowledge_exports/aaai_missing_ablation_runs/skab_complexity_guarded",
                    "--report-dir knowledge_exports/aaai_missing_ablation_runs/skab_complexity_guarded",
                    "--execute",
                    "--skip-complete",
                ),
                _command(
                    "Scripts/mechanism_gate_ablation_matrix.py",
                    "--seeds 42,43,44",
                    "--variants no_mechanism,expert_llm_candidate_data_gate_complexity_guarded,expert_llm_candidate_data_gate_no_complexity",
                    "--profile full",
                    "--min-baseline-path-jaccard -1.0",
                    "--output-root knowledge_exports/aaai_missing_ablation_runs/skab_no_complexity_penalty",
                    "--report-dir knowledge_exports/aaai_missing_ablation_runs/skab_no_complexity_penalty",
                    "--execute",
                    "--skip-complete",
                ),
            ],
            "implementation_needed": (
                "The run entry point now supports `--disable-source-complexity-penalty`, and the matrix includes "
                "`expert_llm_candidate_data_gate_no_complexity`. The remaining work is execution plus artifact "
                "promotion, not parser implementation."
            ),
            "acceptance_rule": (
                "This row is not complete unless admitted edge/path count and source-family burden are "
                "reported beside the task metric, because the mechanism being tested is complexity admission."
            ),
        }
    if tail_complete:
        closed_rows.append(
            {
                "ablation": "No tail safety",
                "status": "complete_policy_replay",
                "artifact": "knowledge_exports/aaai_missing_ablation_runs/skab_tail_safety_policy_replay/skab_tail_safety_policy_replay.json",
                "note": "Matched H_k policy replay complete; no final-protocol admissions changed because low-tail safety was already satisfied.",
            }
        )
    else:
        rows.append(tail_row)
    if no_complexity_complete:
        closed_rows.append(
            {
                "ablation": "No complexity penalty",
                "status": "complete_seed_level_evidence",
                "artifact": "knowledge_exports/aaai_missing_ablation_runs/skab_no_complexity_full/mechanism_gate_ablation_matrix.json",
                "note": "Matched complexity-guarded/no-complexity three-seed rows are present.",
            }
        )
    else:
        rows.append(complexity_row)
    return {
        "status": "complete" if not rows else "ready_to_execute_missing_runs",
        "scope": "Final AAAI ablation table gaps",
        "seeds": SEEDS,
        "important_note": (
            "Commands are execution templates tied to existing experiment entry points. Before a long run, "
            "verify each flag is supported by the local parser; unsupported switches must be implemented as "
            "narrow experiment-branch flags rather than silently changing another mechanism."
        ),
        "rows": rows,
        "closed_rows": closed_rows,
        "completion_rule": (
            "A row becomes final-paper evidence only after matched three-seed metrics, copied raw artifacts, "
            "and a one-mechanism intervention audit are present."
        ),
    }


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# AAAI Missing Ablation Execution Plan",
        "",
        f"- Status: {plan['status']}",
        f"- Scope: {plan['scope']}",
        f"- Seeds: {', '.join(str(seed) for seed in plan['seeds'])}",
        f"- Completion rule: {plan['completion_rule']}",
        "",
        "## Guardrail",
        "",
        plan["important_note"],
        "",
    ]
    for row in plan["rows"]:
        lines.extend(
            [
                f"## {row['ablation']}",
                "",
                f"- Dataset: {row['dataset']}",
                f"- Status: {row['status']}",
                f"- Purpose: {row['purpose']}",
                f"- Acceptance rule: {row['acceptance_rule']}",
                "",
            ]
        )
        if row.get("implementation_needed"):
            lines.extend(["", f"Implementation needed: {row['implementation_needed']}"])
        lines.append("Must hold fixed:")
        lines.extend(f"- {item}" for item in row["must_hold_fixed"])
        lines.extend(["", "Primary metrics:"])
        lines.extend(f"- {item}" for item in row["primary_metrics"])
        lines.extend(["", "Minimum artifacts:"])
        lines.extend(f"- {item}" for item in row["minimum_artifacts"])
        lines.extend(["", "Command templates:", ""])
        lines.extend(f"```powershell\n{command}\n```" for command in row["commands"])
        lines.append("")
    if plan.get("closed_rows"):
        lines.extend(["## Closed Rows", ""])
        for row in plan["closed_rows"]:
            lines.extend(
                [
                    f"- {row['ablation']}: {row['status']}",
                    f"  - Artifact: `{row['artifact']}`",
                    f"  - Note: {row['note']}",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def write_execution_plan(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = build_execution_plan()
    json_path = output_dir / "aaai_missing_ablation_execution_plan.json"
    md_path = output_dir / "aaai_missing_ablation_execution_plan.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(plan))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render the missing AAAI ablation execution plan.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_execution_plan(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
