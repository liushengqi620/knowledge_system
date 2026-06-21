"""Build advanced experiment groups for KG-enhanced anomaly traceability.

The mechanism KG extraction task remains separate from production traceability
data. These experiment groups evaluate whether the extracted mechanism KG helps
downstream anomaly/root-cause traceability after extraction is complete.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "advanced_traceability_experiment_groups"
DEFAULT_DOC_PATH = PROJECT_ROOT / "docs" / "advanced_anomaly_traceability_experiment_groups.md"


@dataclass(frozen=True)
class ExperimentGroup:
    experiment_id: str
    track: str
    research_question: str
    dataset: str
    method: str
    baseline_family: str
    mechanism_kg_usage: str
    anomaly_model_usage: str
    llm_usage: str
    primary_metrics: str
    secondary_metrics: str
    expected_claim: str
    priority: str
    implementation_notes: str


def _row(
    experiment_id: str,
    track: str,
    research_question: str,
    dataset: str,
    method: str,
    baseline_family: str,
    mechanism_kg_usage: str,
    anomaly_model_usage: str,
    llm_usage: str,
    primary_metrics: str,
    secondary_metrics: str,
    expected_claim: str,
    priority: str,
    implementation_notes: str,
) -> ExperimentGroup:
    return ExperimentGroup(
        experiment_id=experiment_id,
        track=track,
        research_question=research_question,
        dataset=dataset,
        method=method,
        baseline_family=baseline_family,
        mechanism_kg_usage=mechanism_kg_usage,
        anomaly_model_usage=anomaly_model_usage,
        llm_usage=llm_usage,
        primary_metrics=primary_metrics,
        secondary_metrics=secondary_metrics,
        expected_claim=expected_claim,
        priority=priority,
        implementation_notes=implementation_notes,
    )


def build_groups() -> list[ExperimentGroup]:
    rows: list[ExperimentGroup] = []

    plain = [
        ("rule_top_feature_trace", "Use top abnormal process features and expert rules only."),
        ("shap_feature_trace", "Rank root causes from feature attribution of the anomaly classifier."),
        ("bm25_case_retrieval", "Retrieve similar historical cases by text/label similarity."),
        ("vector_case_retrieval", "Retrieve similar historical cases with embedding similarity."),
    ]
    for idx, (method, notes) in enumerate(plain, start=1):
        rows.append(
            _row(
                f"AT-E1.{idx}",
                "plain_traceability_baselines",
                "Does the KG add value beyond conventional feature/case traceability?",
                "baosteel_weak_traceability_splits; reviewed case subset",
                method,
                "non_kg_traceability",
                "none",
                "uses_existing_anomaly_scores_or_case_labels",
                "none",
                "Hit@1/3/5 for root-cause group; trace path hit rate",
                "case retrieval precision; explanation length; runtime",
                "KG-enhanced methods should beat feature-only and case-only traceability on explanation completeness.",
                "P0",
                notes,
            )
        )

    anomaly_backbones = [
        ("isolation_forest_trace", "classical_unsupervised"),
        ("one_class_svm_trace", "classical_unsupervised"),
        ("autoencoder_reconstruction_trace", "neural_reconstruction"),
        ("dagmm_trace", "deep_density_reconstruction"),
        ("tranad_trace", "transformer_time_series"),
        ("mtad_gat_trace", "graph_attention_time_series"),
        ("gdn_trace", "learned_sensor_graph"),
    ]
    for idx, (method, family) in enumerate(anomaly_backbones, start=1):
        rows.append(
            _row(
                f"AT-E2.{idx}",
                "anomaly_detection_backbone_comparison",
                "Which anomaly detector provides the strongest signal before KG reasoning?",
                "baosteel_process_time_windows; anomaly labels from weak and reviewed subsets",
                method,
                family,
                "optional_posthoc_mapping_to_kg",
                "primary_detection_or_feature_scoring_module",
                "none",
                "Anomaly F1; AUROC; AUPRC; root-cause Hit@k",
                "latency; training time; missing-sensor robustness",
                "The proposed KG layer should improve root-cause localization regardless of the detector backbone.",
                "P0" if method in {"tranad_trace", "mtad_gat_trace", "gdn_trace"} else "P1",
                "Use detector residuals or attention/deviation scores as observations aligned to KG entities.",
            )
        )

    causal_rows = [
        ("lagged_correlation_rca", "correlation_baseline", "none"),
        ("granger_graph_rca", "causal_time_series", "causal_edges_as_soft_prior"),
        ("pcmci_or_notears_rca", "causal_discovery", "learned_graph_compared_with_mechanism_kg"),
        ("pyrca_causal_graph_scoring", "rca_library_baseline", "expert_or_learned_causal_graph"),
        ("dowhy_counterfactual_rca", "counterfactual_causal_inference", "kg_path_as_structural_prior"),
        ("neural_granger_aerca_style_rca", "neural_causal_rca", "kg_edges_as_regularizer"),
    ]
    for idx, (method, family, kg_usage) in enumerate(causal_rows, start=1):
        rows.append(
            _row(
                f"AT-E3.{idx}",
                "causal_rca_baselines",
                "Does mechanism KG reasoning improve causal root-cause ranking?",
                "event-centered multivariate process windows with reviewed root-cause labels",
                method,
                family,
                kg_usage,
                "uses_temporal_features_and_anomaly_residuals",
                "none_or_explanation_only",
                "Root-cause Hit@1/3/5; MRR; causal direction accuracy",
                "counterfactual effect score; false-cause rate; runtime",
                "Mechanism KG should reduce symptom/root-cause confusion and improve causal direction.",
                "P0",
                "Evaluate with time-lag constraints so downstream symptoms are not ranked ahead of upstream causes.",
            )
        )

    kg_reasoning = [
        ("exact_schema_path_search", "symbolic_kg_reasoning", "hard KG constraints"),
        ("personalized_pagerank_on_kg", "graph_walk_reasoning", "weighted mechanism graph"),
        ("kg_embedding_link_prediction", "embedding_kg_reasoning", "TransE/RotatE/ComplEx style embeddings"),
        ("relational_gnn_trace_ranker", "gnn_kg_reasoning", "R-GCN/GAT over mechanism-instance graph"),
        ("temporal_kg_path_ranker", "temporal_kg_reasoning", "time-window constrained mechanism paths"),
        ("counterfactual_kg_path_ranker", "causal_kg_reasoning", "path intervention and do-calculus inspired scoring"),
    ]
    for idx, (method, family, kg_usage) in enumerate(kg_reasoning, start=1):
        rows.append(
            _row(
                f"AT-E4.{idx}",
                "kg_reasoning_for_traceability",
                "Which KG reasoning strategy best converts mechanism knowledge into trace paths?",
                "large mechanism KG plus attached Baosteel instance/event subset",
                method,
                family,
                kg_usage,
                "uses_detector_outputs_as_query_nodes",
                "none_or_verbalization_only",
                "Trace path Hit@k; path NDCG; explanation completeness",
                "path length; unsupported-edge rate; expert path acceptability",
                "Path-constrained KG reasoning should produce more faithful explanations than flat retrieval.",
                "P0",
                "Attach ProcessObservation nodes to ProcessParameter/EquipmentState/QualityDefect nodes before ranking paths.",
            )
        )

    graph_rag_llm = [
        ("llm_zero_shot_rca", "llm_only", "none", "direct prompt"),
        ("text_rag_rca", "text_rag", "retrieves raw cases/documents", "retrieval augmented prompt"),
        ("schema_rag_rca", "schema_rag", "retrieves schema and labels", "schema constrained prompt"),
        ("graph_rag_rca", "graph_rag", "retrieves KG communities/paths", "graph-grounded generation"),
        ("lightrag_style_dual_level_rca", "dual_level_graph_rag", "low-level and high-level KG retrieval", "graph-vector hybrid generation"),
        ("hipporag_style_ppr_rca", "memory_graph_rag", "PPR over KG memory", "retrieval plus generator"),
        ("agentic_kg_rca", "llm_agent", "tool calls to graph search and case retrieval", "plan-search-verify agent"),
    ]
    for idx, (method, family, kg_usage, llm_usage) in enumerate(graph_rag_llm, start=1):
        rows.append(
            _row(
                f"AT-E5.{idx}",
                "llm_and_graphrag_traceability",
                "Can LLM reasoning use the mechanism KG without hallucinating unsupported causes?",
                "case questions generated from reviewed traceability events plus held-out mechanism KG",
                method,
                family,
                kg_usage,
                "uses_event_summary_and_detector_outputs",
                llm_usage,
                "Answer faithfulness; root-cause Hit@k; action recommendation accuracy",
                "token/record; invalid path rate; unsupported triple rate",
                "Graph-grounded LLM methods should improve faithfulness over direct LLM and flat RAG.",
                "P0" if method in {"graph_rag_rca", "lightrag_style_dual_level_rca", "agentic_kg_rca"} else "P1",
                "Require every generated explanation to cite graph paths and evidence spans.",
            )
        )

    proposed = [
        ("late_fusion_detector_kg", "detector score plus KG path score"),
        ("early_fusion_kg_regularized_detector", "KG adjacency regularizes time-series model"),
        ("plm_aligned_event_to_kg_mapper", "PLM maps event text and feature names to mechanism nodes"),
        ("llm_path_adjudicator", "LLM accepts/rejects candidate trace paths with prompt atoms"),
        ("kg_counterfactual_verifier", "counterfactual test reranks graph paths"),
        ("full_plm_llm_kg_traceability", "detector + PLM alignment + KG path search + LLM atom adjudication"),
    ]
    for idx, (method, notes) in enumerate(proposed, start=1):
        rows.append(
            _row(
                f"AT-E6.{idx}",
                "proposed_fusion_variants",
                "Which fusion point makes PLM, LLM, KG, and anomaly models mutually necessary?",
                "same reviewed traceability benchmark; fixed extraction KG",
                method,
                "proposed_or_ablation",
                "core component",
                "uses_detector_outputs_and_temporal_context",
                "used_for_alignment_or_path_adjudication",
                "Root-cause Hit@k; trace path F1; recommendation acceptability",
                "token/record; latency; hallucination rate; expert acceptability",
                "Full fusion should outperform late-fusion and single-component variants while remaining evidence-grounded.",
                "P0",
                notes,
            )
        )

    ablations = [
        ("no_mechanism_kg", "Remove graph reasoning and keep detector plus LLM."),
        ("no_plm_alignment", "Replace PLM event-to-KG alignment with lexical matching."),
        ("no_llm_adjudication", "Accept top KG paths without prompt-atom verification."),
        ("no_hard_negative_guard", "Remove no-relation and hallucination guard atoms."),
        ("no_temporal_gate", "Allow paths that violate event time order."),
        ("no_evidence_span", "Do not require textual or case evidence for accepted paths."),
        ("randomized_kg_edges", "Keep node labels but randomize KG edges as a graph-prior sanity check."),
    ]
    for idx, (method, notes) in enumerate(ablations, start=1):
        rows.append(
            _row(
                f"AT-E7.{idx}",
                "component_ablation_and_sanity_checks",
                "Which component is responsible for the traceability gains?",
                "same reviewed traceability benchmark; same detector outputs",
                method,
                "ablation",
                "varies_by_ablation",
                "fixed_best_detector",
                "varies_by_ablation",
                "Trace path F1; unsupported cause rate; hard-negative accuracy",
                "root-cause MRR; token/record; path invalidity rate",
                "Removing KG, PLM alignment, LLM adjudication, or temporal constraints should hurt different failure modes.",
                "P0",
                notes,
            )
        )

    robustness = [
        ("label_budget_curve", "Train/alignment budgets: 50, 100, 300, 500, all reviewed cases."),
        ("new_steel_grade_transfer", "Train on seen steel grades and test on unseen grade groups."),
        ("process_stage_transfer", "Train on mold/tundish and test on secondary cooling/straightening."),
        ("missing_sensor_stress", "Mask 10/30/50 percent process variables at inference."),
        ("noisy_weak_label_stress", "Inject 5/10/20 percent wrong weak labels."),
        ("time_shift_stress", "Shift observation windows to test temporal robustness."),
    ]
    for idx, (method, notes) in enumerate(robustness, start=1):
        rows.append(
            _row(
                f"AT-E8.{idx}",
                "low_resource_transfer_and_robustness",
                "Is KG-enhanced traceability robust under realistic industrial constraints?",
                "budgeted and shifted Baosteel traceability splits",
                method,
                "robustness_protocol",
                "fixed_or_incrementally_updated_kg",
                "fixed_best_detector_or_retrained_per_budget",
                "same_prompt_policy_across_budgets",
                "Area under low-resource curve; transfer Hit@k; robustness degradation",
                "latency; expert acceptability; missing-feature tolerance",
                "Mechanism KG should stabilize traceability when labels, sensors, or stages are scarce or shifted.",
                "P1",
                notes,
            )
        )

    expert_eval = [
        ("blind_expert_pairwise_ranking", "Experts compare proposed vs baseline explanations without method names."),
        ("trace_path_acceptability_audit", "Experts judge whether each path is physically plausible."),
        ("action_suggestion_audit", "Experts judge whether suggested controls are actionable and safe."),
        ("operator_time_to_diagnosis", "Measure time needed to reach a diagnosis with or without KG explanation."),
    ]
    for idx, (method, notes) in enumerate(expert_eval, start=1):
        rows.append(
            _row(
                f"AT-E9.{idx}",
                "human_and_operational_evaluation",
                "Does the system help engineers diagnose and act faster?",
                "sampled real or replayed traceability cases with expert review",
                method,
                "human_evaluation",
                "shown_as_path_and_evidence",
                "shown_as_event_context",
                "used_for_natural_language_explanation",
                "expert acceptability; diagnosis time; recommendation usefulness",
                "inter-annotator agreement; confidence calibration; rejection reasons",
                "A strong paper should show operational usefulness, not only automatic scores.",
                "P1",
                notes,
            )
        )

    cost_safety = [
        ("latency_token_budget", "Measure latency and token cost for each method at 1k/10k/100k case scale."),
        ("incremental_kg_update", "Update graph with new mechanism text or new cases and re-evaluate stale-path rate."),
        ("adversarial_hard_negative_cases", "Use plausible but unsupported root-cause-action paths."),
        ("evidence_faithfulness_check", "Verify that every output path has matching KG edge and evidence span."),
    ]
    for idx, (method, notes) in enumerate(cost_safety, start=1):
        rows.append(
            _row(
                f"AT-E10.{idx}",
                "cost_safety_and_online_readiness",
                "Can the system run reliably in a production-style traceability loop?",
                "full weak pool plus reviewed safety subset",
                method,
                "deployment_readiness",
                "audited_or_incremental_kg",
                "fixed_best_detector",
                "budgeted_or_verifier_only",
                "latency; token/record; unsupported output rate",
                "incremental update time; path freshness; safety rejection accuracy",
                "The final system must be cheaper and safer than unconstrained LLM RCA.",
                "P1",
                notes,
            )
        )

    return rows


def _group_by_track(rows: Iterable[ExperimentGroup]) -> dict[str, list[ExperimentGroup]]:
    grouped: dict[str, list[ExperimentGroup]] = {}
    for row in rows:
        grouped.setdefault(row.track, []).append(row)
    return grouped


def write_csv(path: Path, rows: Sequence[ExperimentGroup]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with open(str(path), "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def render_markdown(rows: Sequence[ExperimentGroup]) -> str:
    grouped = _group_by_track(rows)
    lines = [
        "# Advanced Experiment Groups for KG-Enhanced Anomaly Traceability",
        "",
        "## Positioning",
        "",
        "The mechanism KG is not trained on production traceability rows. It is first extracted from mechanism text, then attached to downstream anomaly traceability as a reasoning and explanation layer.",
        "",
        "Target application flow:",
        "",
        "`anomaly event -> process observations -> KG alignment -> causal path ranking -> LLM atom adjudication -> trace explanation and optimization suggestion`",
        "",
        "## Evidence Levels",
        "",
        "- Level 1: mechanism KG extraction quality, already covered by the seed and paper-scale extraction protocols.",
        "- Level 2: event-to-KG alignment quality, evaluated with reviewed process/defect mappings.",
        "- Level 3: root-cause and trace-path ranking quality, evaluated with case labels and expert review.",
        "- Level 4: operational usefulness, evaluated with diagnosis time, recommendation usefulness, and safety checks.",
        "",
        "## Summary",
        "",
        f"- Total experiment rows: {len(rows)}",
        f"- Tracks: {len(grouped)}",
        "- Main graph artifact: `data/quality_traceability_large_kg/quality_traceability_large_kg_seed.json`",
        "- Main instance pool: `data/baosteel_knowledge_extraction/records.jsonl`",
        "",
        "## Experiment Tracks",
        "",
    ]
    for track, items in grouped.items():
        lines.extend(
            [
                f"### {track}",
                "",
                "| ID | Method | Baseline family | KG usage | Primary metrics | Priority |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in items:
            lines.append(
                f"| {item.experiment_id} | `{item.method}` | {item.baseline_family} | {item.mechanism_kg_usage} | {item.primary_metrics} | {item.priority} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Recommended Execution Order",
            "",
            "1. Build a small reviewed traceability benchmark from Baosteel weak labels: defect type, top process observations, root-cause group, accepted trace path, recommended action.",
            "2. Run AT-E1 and AT-E2 to establish non-KG and detector backbone baselines.",
            "3. Run AT-E3 and AT-E4 to compare causal RCA and KG reasoning methods.",
            "4. Run AT-E5 to compare LLM-only, text RAG, GraphRAG, LightRAG-style, HippoRAG-style, and agentic KG RCA.",
            "5. Run AT-E6 and AT-E7 to prove the proposed PLM-LLM-KG fusion and component necessity.",
            "6. Run AT-E8 to show low-resource and cross-condition robustness.",
            "7. Run AT-E9 and AT-E10 only after automatic metrics are stable, because they require expert time and deployment-style measurements.",
            "",
            "## Core Metrics",
            "",
            "- Detection: AUROC, AUPRC, anomaly F1.",
            "- Localization: root-cause Hit@1/3/5, MRR, NDCG.",
            "- Traceability: trace path F1, path hit rate, explanation completeness, causal direction accuracy.",
            "- Faithfulness: unsupported edge rate, evidence span coverage, hallucination rate, hard-negative accuracy.",
            "- Utility: expert acceptability, recommendation usefulness, diagnosis time reduction.",
            "- Cost: latency, token/record, graph update time, memory footprint.",
            "",
            "## Paper-Strength Claims Enabled",
            "",
            "- The mechanism KG improves anomaly traceability beyond feature attribution and case retrieval.",
            "- PLM alignment is useful because it maps noisy event text and feature names to mechanism nodes.",
            "- LLM prompt-atom adjudication is useful because it rejects plausible but unsupported trace paths.",
            "- Graph reasoning is useful because it converts extracted mechanism knowledge into causal paths and optimization suggestions.",
            "- The system remains robust under low labels, unseen conditions, missing sensors, and noisy weak labels.",
            "",
            "## Reference Anchors",
            "",
            "- GraphRAG and graph-enhanced retrieval motivate graph-based retrieval and generation baselines.",
            "- LightRAG motivates dual-level graph/vector retrieval and incremental update baselines.",
            "- HippoRAG motivates PPR-style KG memory retrieval baselines.",
            "- TranAD, MTAD-GAT, and GDN motivate strong multivariate time-series anomaly backbones.",
            "- PyRCA, neural Granger RCA, counterfactual RCA, and DoWhy motivate causal RCA baselines.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(rows: Sequence[ExperimentGroup], output_dir: Path, doc_path: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    row_dicts = [asdict(row) for row in rows]
    csv_path = output_dir / "groups.csv"
    json_path = output_dir / "groups.json"
    markdown_path = output_dir / "groups.md"
    write_csv(csv_path, rows)
    write_json(json_path, row_dicts)
    markdown = render_markdown(rows)
    markdown_path.write_text(markdown, encoding="utf-8")
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(markdown, encoding="utf-8")
    summary = {
        "status": "advanced_traceability_experiment_groups_built",
        "rows": len(rows),
        "tracks": sorted(_group_by_track(rows)),
        "outputs": {
            "csv": str(csv_path),
            "json": str(json_path),
            "markdown": str(markdown_path),
            "doc": str(doc_path),
        },
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build advanced anomaly traceability experiment groups.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    args = parser.parse_args()
    summary = write_outputs(build_groups(), args.output_dir, args.doc_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
