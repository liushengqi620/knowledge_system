"""Build a concrete research plan for the recovered RAG experiments."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List

try:
    from experiment_status import PROJECT_ROOT, build_status_report
except ImportError:  # pragma: no cover - used when imported as experiments.*
    from experiments.experiment_status import PROJECT_ROOT, build_status_report


@dataclass(frozen=True)
class ExperimentPlanItem:
    experiment_id: str
    track: str
    title: str
    research_question: str
    status: str
    command: str
    expected_outputs: str
    decision_gate: str
    notes: str


def _status_lookup(status_report: dict[str, Any]) -> dict[str, str]:
    return {item["name"]: item["status"] for item in status_report["items"]}


def build_research_plan(project_root: Path = PROJECT_ROOT) -> List[ExperimentPlanItem]:
    report = build_status_report(project_root)
    statuses = _status_lookup(report)
    python = "python"

    prompt_diag_ready = statuses.get("prompt_diagnostic") == "ready"
    prompt_pipeline_ready = statuses.get("prompt_ablation_pipeline") == "ready"
    datasets_ready = statuses.get("continuous_casting") == "ready" and statuses.get("electrochemistry") == "ready"
    train_modules_ready = (
        statuses.get("advanced_ner_training_module") == "ready"
        and statuses.get("relation_extraction_training_module") == "ready"
    )

    plan = [
        ExperimentPlanItem(
            experiment_id="A1",
            track="prompt_atom",
            title="Prompt-atom decomposition diagnostics",
            research_question="Which prompt decomposition strategy creates the most useful local update units before LLM evaluation?",
            status="ready" if prompt_diag_ready else "blocked",
            command=f"{python} experiments/prompt_atom_decomposition_experiment.py --output-dir outputs/prompt_atom_decomposition",
            expected_outputs="diagnostic_results.json; diagnostic_summary.csv; diagnostic_table.tex; experiment_protocol.md",
            decision_gate="functional_atom should beat no_atom on edit locality and diagnostic score without over_fine fragmentation risk",
            notes="This is a safe first experiment because it does not fabricate extraction metrics.",
        ),
        ExperimentPlanItem(
            experiment_id="A2",
            track="prompt_atom",
            title="Prompt-atom runner dry run",
            research_question="Can all decomposition strategies be scheduled and summarized with explicit missing-result states?",
            status="ready",
            command=f"{python} experiments/run_atom_decomposition_result_experiment.py --dry-run --output-root atom_dryrun",
            expected_outputs="atom_decomposition_result_summary.csv; atom_decomposition_result_summary.json; atom_decomposition_result_table.tex",
            decision_gate="Every strategy should produce a row with missing_result_file or not_executed rather than failing silently",
            notes="Use this to inspect commands before running any expensive LLM pipeline.",
        ),
        ExperimentPlanItem(
            experiment_id="A3",
            track="prompt_atom",
            title="Full prompt-atom result ablation",
            research_question="Does functional_atom improve NER F1, RE F1, Overall F1, and KHR over coarse or random prompt decompositions?",
            status="ready_scaffold_only" if prompt_pipeline_ready else "blocked",
            command=f"{python} experiments/run_atom_decomposition_result_experiment.py --output-root atom_result",
            expected_outputs="per-strategy ablation_results.json plus consolidated CSV/JSON/LaTeX table",
            decision_gate="functional_atom must improve Overall F1 and reduce KHR against no_atom and random_atom under the same data and evaluator",
            notes="The recovered prompt_engineering_ablation.py is a scaffold unless a real evaluator is restored.",
        ),
        ExperimentPlanItem(
            experiment_id="B1",
            track="plm_baseline",
            title="Prepare supervised PLM matrix",
            research_question="What exact dataset/model/ratio/seed combinations are required for a fair low-annotation comparison?",
            status="ready" if datasets_ready else "blocked_missing_dataset",
            command=f"{python} experiments/extended_plm_baselines.py --output-dir outputs/plm_extended_baselines_runs",
            expected_outputs="manifest.json; results_template.csv; run_commands.ps1; split files",
            decision_gate="All configured combinations appear in the manifest, and fixed FSDV/FSDV-EAPA rows remain separated from trainable PLM rows",
            notes="Provide dataset paths or restore data before running on real inputs.",
        ),
        ExperimentPlanItem(
            experiment_id="B2",
            track="plm_baseline",
            title="BERT-CRF+CasRel supervised baseline",
            research_question="How much annotation does the local supervised pipeline need to approach FSDV-EAPA?",
            status="ready" if datasets_ready and train_modules_ready else "blocked_missing_data_or_training_modules",
            command=f"{python} experiments/extended_plm_baselines.py --execute --models BERT-CRF+CasRel --output-dir outputs/plm_extended_baselines_runs",
            expected_outputs="summary_metrics.json for each dataset/ratio/seed row",
            decision_gate="Use dev Overall F1 for checkpoint selection, then evaluate held-out test splits separately",
            notes="Do not compare dev-selected metrics directly against test-only FSDV/FSDV-EAPA rows.",
        ),
        ExperimentPlanItem(
            experiment_id="B3",
            track="plm_baseline",
            title="External PLM adapters",
            research_question="Do PURE, CasRel, TPLinker, and PRGC change the conclusion under the same annotation budgets?",
            status="pending_adapter_implementation",
            command="edit experiments/plm_external_adapters.template.json, then run extended_plm_baselines.py --execute",
            expected_outputs="summary_metrics.json from each external adapter plus per-sample predictions",
            decision_gate="Each adapter must use the same split, seed, encoder policy, and test metric schema",
            notes="OneRel can remain optional unless the final paper table needs it.",
        ),
        ExperimentPlanItem(
            experiment_id="C1",
            track="evaluation",
            title="Held-out test evaluation",
            research_question="Do completed supervised baselines hold up on test data after dev selection?",
            status="blocked_until_trained_runs_exist",
            command=f"{python} experiments/evaluate_local_plm_baseline.py --run-root outputs/plm_extended_baselines_runs --device cuda",
            expected_outputs="test_results.csv; test_summary.csv; per-run test_metrics.json",
            decision_gate="Paper tables must use test metrics or clearly mark development metrics",
            notes="Run after BERT-CRF+CasRel training outputs exist.",
        ),
        ExperimentPlanItem(
            experiment_id="D1",
            track="reporting",
            title="Evidence audit for paper claims",
            research_question="Which claims are supported by completed evidence and which are still planned?",
            status="ready",
            command=f"{python} experiments/experiment_status.py --output-dir outputs/experiment_status",
            expected_outputs="status_report.json; status_items.csv; status_report.md",
            decision_gate="No placeholder row can be described as an experimental result",
            notes="Use this before writing or updating any manuscript table.",
        ),
    ]
    return plan


def write_plan(rows: List[ExperimentPlanItem], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    dict_rows = [asdict(row) for row in rows]
    (output_dir / "experiment_research_plan.json").write_text(
        json.dumps(dict_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (output_dir / "experiment_research_plan.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(dict_rows[0].keys()))
        writer.writeheader()
        writer.writerows(dict_rows)
    (output_dir / "experiment_research_plan.md").write_text(render_markdown(rows), encoding="utf-8")


def render_markdown(rows: List[ExperimentPlanItem]) -> str:
    lines = [
        "# RAG Experiment Research Plan",
        "",
        "| ID | Track | Title | Status | Decision Gate |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.experiment_id} | {row.track} | {row.title} | {row.status} | {row.decision_gate} |"
        )
    lines.extend(["", "## Commands", ""])
    for row in rows:
        lines.extend(
            [
                f"### {row.experiment_id}. {row.title}",
                "",
                f"Question: {row.research_question}",
                "",
                "```powershell",
                row.command,
                "```",
                "",
                f"Expected outputs: {row.expected_outputs}",
                "",
                f"Notes: {row.notes}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a concrete RAG experiment research plan.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "experiment_research_plan")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_research_plan(args.project_root)
    write_plan(rows, args.output_dir)
    print(json.dumps({"items": len(rows), "output_dir": str(args.output_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
