"""Build the mechanism-layer KG extraction experiment matrix.

This plan is intentionally dataset-agnostic with respect to Baosteel production
records. The target dataset is a mechanism-text corpus built from papers,
manuals, expert rules, and defect mechanism reports.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, List, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "mechanism_kg_experiment_plan"


@dataclass(frozen=True)
class ExperimentRow:
    experiment_id: str
    research_question: str
    track: str
    setting: str
    method: str
    dataset: str
    train_budget: str
    plm_policy: str
    llm_policy: str
    prompt_atom_policy: str
    primary_metrics: str
    secondary_metrics: str
    expected_evidence: str
    priority: str
    status: str
    notes: str


def _row(
    experiment_id: str,
    research_question: str,
    track: str,
    setting: str,
    method: str,
    *,
    train_budget: str = "full_gold_train",
    plm_policy: str = "none",
    llm_policy: str = "none",
    prompt_atom_policy: str = "none",
    primary_metrics: str = "Entity F1; Relation F1; Triple F1",
    secondary_metrics: str = "Evidence F1; Direction Accuracy; Hallucination Rate; Token/record; Time/record",
    expected_evidence: str = "",
    priority: str = "P1",
    status: str = "planned",
    notes: str = "",
) -> ExperimentRow:
    return ExperimentRow(
        experiment_id=experiment_id,
        research_question=research_question,
        track=track,
        setting=setting,
        method=method,
        dataset="mechanism_text_gold_split_by_document",
        train_budget=train_budget,
        plm_policy=plm_policy,
        llm_policy=llm_policy,
        prompt_atom_policy=prompt_atom_policy,
        primary_metrics=primary_metrics,
        secondary_metrics=secondary_metrics,
        expected_evidence=expected_evidence,
        priority=priority,
        status=status,
        notes=notes,
    )


def build_experiment_rows() -> List[ExperimentRow]:
    rows: List[ExperimentRow] = []

    main_methods = [
        (
            "rule_based",
            "dictionary and pattern rules",
            "none",
            "none",
            "none",
            "lower-bound baseline for precision-oriented extraction",
        ),
        (
            "plm_only",
            "BERT/MacBERT NER + supervised RE",
            "candidate_generation_only",
            "none",
            "none",
            "tests whether supervised PLM alone is sufficient",
        ),
        (
            "llm_zero_shot",
            "zero-shot full extraction",
            "none",
            "free_extraction_zero_shot",
            "full_static_prompt",
            "tests open-ended LLM extraction without examples",
        ),
        (
            "llm_few_shot",
            "few-shot full extraction",
            "none",
            "free_extraction_few_shot",
            "full_static_prompt",
            "strong LLM-only baseline",
        ),
        (
            "plm_llm_cascade",
            "PLM candidates + LLM adjudication without atom routing",
            "candidate_generation_uncertainty",
            "candidate_adjudication",
            "fixed_minimal_prompt",
            "tests whether candidate-level adjudication alone explains gains",
        ),
        (
            "proposed",
            "PLM-guided prompt-atom LLM adjudication",
            "candidate_generation_uncertainty_evidence",
            "constrained_candidate_adjudication",
            "plm_guided_atoms",
            "main proposed method",
        ),
    ]
    for idx, (method, setting, plm, llm, atom, notes) in enumerate(main_methods, start=1):
        rows.append(
            _row(
                f"E1.{idx}",
                "RQ1",
                "main_effectiveness",
                setting,
                method,
                plm_policy=plm,
                llm_policy=llm,
                prompt_atom_policy=atom,
                expected_evidence="Proposed improves Triple F1 and reduces hallucination/token cost versus strong baselines.",
                priority="P0",
                notes=notes,
            )
        )

    low_resource_methods = [
        ("plm_only", "candidate_generation_only", "none", "none"),
        ("llm_few_shot", "none", "free_extraction_few_shot", "full_static_prompt"),
        ("plm_llm_cascade", "candidate_generation_uncertainty", "candidate_adjudication", "fixed_minimal_prompt"),
        ("proposed", "candidate_generation_uncertainty_evidence", "constrained_candidate_adjudication", "plm_guided_atoms"),
    ]
    for budget in ["50", "100", "300", "500"]:
        for idx, (method, plm, llm, atom) in enumerate(low_resource_methods, start=1):
            rows.append(
                _row(
                    f"E2.{budget}.{idx}",
                    "RQ2",
                    "low_resource",
                    f"{budget} gold training records",
                    method,
                    train_budget=f"{budget}_gold_records",
                    plm_policy=plm,
                    llm_policy=llm,
                    prompt_atom_policy=atom,
                    primary_metrics="Entity F1; Relation F1; Triple F1; area under low-resource curve",
                    secondary_metrics="Hallucination Rate; Token/record; LLM call rate",
                    expected_evidence="Proposed has stronger low-resource stability than PLM-only and lower cost than LLM-only.",
                    priority="P0" if budget in {"100", "300"} else "P1",
                )
            )

    atom_settings = [
        ("no_atom", "minimal schema and candidate only", "none"),
        ("full_prompt", "all atoms inserted for every candidate", "full_prompt_atoms"),
        ("random_atom", "random atoms with same count as proposed", "random_atoms"),
        ("rule_atom", "hand-written uncertainty-to-atom mapping", "rule_atoms"),
        ("plm_learned_atom", "learned multi-label atom selector", "learned_atoms"),
        ("proposed_full", "learned selector plus uncertainty routing", "plm_guided_atoms"),
    ]
    for idx, (method, setting, atom) in enumerate(atom_settings, start=1):
        rows.append(
            _row(
                f"E3.{idx}",
                "RQ3",
                "prompt_atom_ablation",
                setting,
                method,
                plm_policy="candidate_generation_uncertainty_evidence",
                llm_policy="constrained_candidate_adjudication",
                prompt_atom_policy=atom,
                primary_metrics="Relation F1; Triple F1; Correction Accuracy",
                secondary_metrics="Hallucination Rate; Token/record; Invalid Output Rate",
                expected_evidence="PLM-guided atom selection outperforms random/no-atom and approaches or beats full prompt with fewer tokens.",
                priority="P0",
            )
        )

    router_settings = [
        ("random_router", "randomly route candidates to LLM", "random"),
        ("rule_router", "keyword/schema rules decide LLM calls", "rule"),
        ("confidence_only_router", "single confidence threshold", "confidence_only"),
        ("uncertainty_router", "calibrated uncertainty type controls routing", "uncertainty"),
        ("proposed_full_router", "uncertainty + evidence + atom routing", "uncertainty_evidence_atom"),
    ]
    for idx, (method, setting, plm) in enumerate(router_settings, start=1):
        rows.append(
            _row(
                f"E4.{idx}",
                "RQ4",
                "plm_role_ablation",
                setting,
                method,
                plm_policy=plm,
                llm_policy="constrained_candidate_adjudication",
                prompt_atom_policy="matched_to_router",
                primary_metrics="Triple F1; high-risk error coverage; LLM call precision",
                secondary_metrics="LLM call rate; Token/record; Hallucination Rate",
                expected_evidence="PLM uncertainty and evidence signals route difficult candidates better than rules/random/confidence alone.",
                priority="P1",
            )
        )

    feedback_rounds = [
        ("round_0", "initial PLM trained only on gold train"),
        ("round_1", "add LLM accepted/corrected/rejected candidates"),
        ("round_2", "second feedback iteration"),
    ]
    for idx, (method, setting) in enumerate(feedback_rounds, start=1):
        rows.append(
            _row(
                f"E5.{idx}",
                "RQ5",
                "feedback_distillation",
                setting,
                method,
                plm_policy="iterative_training",
                llm_policy="teacher_adjudication",
                prompt_atom_policy="plm_guided_atoms",
                primary_metrics="PLM-only Triple F1; candidate precision; candidate recall",
                secondary_metrics="LLM call rate; hard-negative rejection accuracy",
                expected_evidence="LLM adjudication feedback improves the next PLM and reduces later LLM dependence.",
                priority="P2",
            )
        )

    graph_rows = [
        (
            "graph_exact",
            "strict graph assembly with exact surface forms",
            "node duplicate rate; relation conflict rate; isolated node ratio",
        ),
        (
            "graph_canonicalized",
            "canonicalized graph assembly with alias merging",
            "mechanism chain completeness; conflict rate; expert acceptability",
        ),
        (
            "expert_audit",
            "manual expert audit of sampled triples and chains",
            "expert acceptability; unsupported triple rate; direction error rate",
        ),
    ]
    for idx, (method, setting, metrics) in enumerate(graph_rows, start=1):
        rows.append(
            _row(
                f"E6.{idx}",
                "RQ6",
                "graph_level_evaluation",
                setting,
                method,
                plm_policy="uses_best_extractor_outputs",
                llm_policy="none_or_audit_assist",
                prompt_atom_policy="not_applicable",
                primary_metrics=metrics,
                secondary_metrics="case-study chain completeness; duplicate alias count",
                expected_evidence="The proposed extractor produces a cleaner and more complete mechanism KG, not only better sentence-level F1.",
                priority="P1",
            )
        )

    frontier_methods = [
        (
            "gliner_zero_shot_ner_pair_re",
            "GLiNER-style generalist zero-shot NER plus a lightweight pairwise relation classifier",
            "generalist_ner_candidate_generation",
            "none_or_pairwise_classifier",
            "schema_labels_as_entity_prompts",
            "tests whether compact generalist NER can reduce annotation and API dependence",
        ),
        (
            "instructuie_instruction_tuned",
            "instruction-tuned unified IE model with task-specific extraction instructions",
            "instruction_uie_adapter",
            "text_to_text_extraction",
            "expert_instruction_prompt",
            "tests unified instruction tuning against task-specific PLM and generic LLM prompting",
        ),
        (
            "gollie_guideline_following",
            "guideline-following zero-shot IE model using detailed annotation guidelines",
            "none",
            "guideline_following_extraction",
            "annotation_guideline_atoms",
            "tests whether detailed guidelines improve zero-shot mechanism extraction",
        ),
        (
            "code4uie_retrieval_code_generation",
            "retrieval-augmented code-style schema generation with similar examples",
            "example_retriever",
            "code_generation_extraction",
            "python_class_schema_prompt",
            "tests code-format schema prompting and example retrieval for structured KG output",
        ),
        (
            "knowcoder_code_schema_uie",
            "code-style universal IE model with schema library and schema-following training",
            "code_schema_adapter",
            "code_generation_extraction",
            "python_class_schema_prompt",
            "tests stronger schema following on unseen mechanism entity/relation types",
        ),
        (
            "deepke_llm_kgc_adapter",
            "DeepKE-style toolkit baseline with NER/RE/LLM knowledge extraction adapters",
            "toolkit_plm_or_llm_adapter",
            "adapter_controlled_extraction",
            "toolkit_schema_config",
            "tests reproducibility against an external KG extraction toolkit",
        ),
        (
            "constrained_json_llm",
            "LLM extraction with JSON schema or grammar-constrained decoding",
            "none",
            "constrained_structured_generation",
            "json_schema_prompt",
            "tests whether output constraints reduce invalid triples without hurting recall",
        ),
        (
            "retrieval_augmented_schema_prompt",
            "LLM prompt with retrieved mechanism examples and schema snippets",
            "dense_or_bm25_example_retrieval",
            "retrieval_augmented_extraction",
            "retrieved_schema_and_examples",
            "tests retrieval-augmented prompting against static few-shot prompting",
        ),
    ]
    for idx, (method, setting, plm, llm, atom, notes) in enumerate(frontier_methods, start=1):
        rows.append(
            _row(
                f"E7.{idx}",
                "RQ7",
                "frontier_extraction_baselines",
                setting,
                method,
                plm_policy=plm,
                llm_policy=llm,
                prompt_atom_policy=atom,
                primary_metrics="Entity F1; Relation F1; Triple F1; Evidence F1",
                secondary_metrics="Invalid Output Rate; Hallucination Rate; Token/record; Setup Cost; Adapter Reproducibility",
                expected_evidence="The proposed method should be compared with recent generalist IE, guideline-following IE, code-generation IE, and constrained-output LLM baselines.",
                priority="P0" if method in {"gliner_zero_shot_ner_pair_re", "gollie_guideline_following", "code4uie_retrieval_code_generation"} else "P1",
                notes=notes,
            )
        )

    return rows


def write_csv(path: Path, rows: Sequence[ExperimentRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _group_by_track(rows: Iterable[ExperimentRow]) -> dict[str, list[ExperimentRow]]:
    grouped: dict[str, list[ExperimentRow]] = {}
    for row in rows:
        grouped.setdefault(row.track, []).append(row)
    return grouped


def render_markdown(rows: Sequence[ExperimentRow]) -> str:
    lines = [
        "# Mechanism KG Experiment Matrix",
        "",
        "This matrix is for mechanism-layer knowledge graph extraction from papers, manuals, expert rules, and defect mechanism documents. It does not use processed Baosteel production data.",
        "",
        "## Summary",
        "",
        f"- Total experiment rows: {len(rows)}",
        f"- Tracks: {', '.join(sorted(_group_by_track(rows)))}",
        "- Primary held-out dataset: `mechanism_text_gold_split_by_document`",
        "",
        "## Tracks",
        "",
    ]
    for track, items in _group_by_track(rows).items():
        lines.extend([f"### {track}", "", "| ID | RQ | Method | Setting | Priority |", "|---|---|---|---|---|"])
        for item in items:
            lines.append(
                f"| {item.experiment_id} | {item.research_question} | `{item.method}` | {item.setting} | {item.priority} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Recommended Execution Order",
            "",
            "1. Build and validate the mechanism-text gold dataset with document-level splits.",
            "2. Run E1 main effectiveness baselines.",
            "3. Run E3 prompt-atom ablation using the best E1 PLM checkpoint.",
            "4. Run E2 low-resource curves for 100 and 300 labels first, then 50 and 500.",
            "5. Run E4 PLM role ablation after routing thresholds are selected on dev.",
            "6. Run E6 graph-level evaluation on the best extractor output.",
            "7. Run E5 feedback/distillation if time permits.",
            "",
            "## Paper Evidence Gate",
            "",
            "A result row is publishable only when the command, dataset split, seed, model checkpoint, prompt version, output file, and test metric source are recorded.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(rows: Sequence[ExperimentRow], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    row_dicts = [asdict(row) for row in rows]
    write_csv(output_dir / "mechanism_kg_experiment_matrix.csv", rows)
    write_json(output_dir / "mechanism_kg_experiment_matrix.json", row_dicts)
    (output_dir / "mechanism_kg_experiment_plan.md").write_text(render_markdown(rows), encoding="utf-8")
    summary = {
        "row_count": len(rows),
        "track_counts": {track: len(items) for track, items in _group_by_track(rows).items()},
        "priority_counts": {
            priority: sum(1 for row in rows if row.priority == priority)
            for priority in sorted({row.priority for row in rows})
        },
        "dataset": "mechanism_text_gold_split_by_document",
        "excludes": ["processed_baosteel_production_records", "quality_traceability_instance_rows"],
        "outputs": {
            "csv": str(output_dir / "mechanism_kg_experiment_matrix.csv"),
            "json": str(output_dir / "mechanism_kg_experiment_matrix.json"),
            "markdown": str(output_dir / "mechanism_kg_experiment_plan.md"),
        },
    }
    write_json(output_dir / "mechanism_kg_experiment_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build mechanism-layer KG experiment plan.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_experiment_rows()
    summary = write_outputs(rows, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
