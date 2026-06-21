"""Build a quality-traceability large-KG design pack and extraction evidence report.

The pack connects the mechanism-layer extraction output to a future
quality-traceability graph without making processed production rows the primary
mechanism-extraction dataset.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MECHANISM_GRAPH = PROJECT_ROOT / "outputs" / "mechanism_kg_seed_experiment" / "mechanism_seed_graph.json"
DEFAULT_METRICS = PROJECT_ROOT / "outputs" / "mechanism_kg_seed_experiment" / "metrics.json"
DEFAULT_BAOSTEEL_MANIFEST = PROJECT_ROOT / "data" / "baosteel_knowledge_extraction" / "manifest.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "quality_traceability_large_kg_pack"
DEFAULT_KG_DIR = PROJECT_ROOT / "data" / "quality_traceability_large_kg"


SCHEMA_NODE_CLASSES = [
    ("MechanismLayer", "SchemaClass", "Mechanism knowledge extracted from papers/manuals/expert rules."),
    ("InstanceLayer", "SchemaClass", "Production batches, quality events, and process observations."),
    ("EvidenceLayer", "SchemaClass", "Text evidence, model confidence, provenance, and review states."),
    ("TraceabilityApplication", "SchemaClass", "Quality cause-location-action traceability application layer."),
    ("ProcessParameter", "EntityType", "Process variable or operating parameter."),
    ("EquipmentState", "EntityType", "Equipment condition or operating state."),
    ("MaterialState", "EntityType", "Steel, slag, inclusion, solidification, or thermal state."),
    ("DefectMechanism", "EntityType", "Intermediate physical mechanism."),
    ("QualityDefect", "EntityType", "Observed or potential quality defect."),
    ("ControlAction", "EntityType", "Control, prevention, or correction action."),
    ("ProcessStage", "EntityType", "Process location or stage."),
    ("ProductionBatch", "InstanceType", "Batch/heat/cast-sequence node for future traceability data."),
    ("QualityEvent", "InstanceType", "Observed quality event or warning event."),
    ("ProcessObservation", "InstanceType", "Observed process variable value in a batch/event."),
    ("RiskWarning", "InstanceType", "Warning output from a future risk model."),
    ("TracePath", "InstanceType", "Path connecting observation, mechanism, defect, and action."),
]

SCHEMA_EDGE_TYPES = [
    ("MechanismLayer", "supports", "TraceabilityApplication"),
    ("InstanceLayer", "instantiates", "TraceabilityApplication"),
    ("EvidenceLayer", "audits", "MechanismLayer"),
    ("ProductionBatch", "has_event", "QualityEvent"),
    ("QualityEvent", "has_observation", "ProcessObservation"),
    ("ProcessObservation", "aligned_to", "ProcessParameter"),
    ("QualityEvent", "explained_by", "DefectMechanism"),
    ("DefectMechanism", "increase_risk_of", "QualityDefect"),
    ("ControlAction", "suppress", "QualityDefect"),
    ("TracePath", "uses_mechanism", "MechanismLayer"),
    ("TracePath", "suggests_action", "ControlAction"),
]


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_schema() -> dict[str, Any]:
    return {
        "schema_name": "quality_traceability_large_kg",
        "version": "0.1-seed",
        "layers": {
            "mechanism": "Text-extracted mechanism entities, relations, chains, and control actions.",
            "instance": "Future production batches/events/observations attached to the mechanism graph.",
            "evidence": "Source text, extraction confidence, prompt atoms, adjudication, and review metadata.",
            "application": "Quality traceability queries, paths, warnings, and recommended actions.",
        },
        "node_classes": [
            {"name": name, "class_type": class_type, "description": description}
            for name, class_type, description in SCHEMA_NODE_CLASSES
        ],
        "edge_types": [
            {"head": head, "relation": relation, "tail": tail}
            for head, relation, tail in SCHEMA_EDGE_TYPES
        ],
        "mechanism_relation_types": [
            "cause",
            "affect",
            "increase_risk_of",
            "suppress",
            "improve",
            "located_at",
            "controlled_by",
            "indicates",
        ],
        "traceability_queries": [
            "Given a quality defect, return upstream mechanisms, process parameters, and control actions.",
            "Given a process observation, return possible mechanisms and quality risks.",
            "Given a warning event, return evidence-backed trace paths and recommended checks/actions.",
        ],
    }


def schema_graph_nodes() -> list[dict[str, Any]]:
    nodes = []
    for idx, (name, class_type, description) in enumerate(SCHEMA_NODE_CLASSES, start=1):
        nodes.append(
            {
                "node_id": f"s{idx}",
                "text": name,
                "type": class_type,
                "layer": "schema",
                "description": description,
                "record_ids": [],
            }
        )
    return nodes


def schema_graph_edges(nodes: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_text = {node["text"]: node["node_id"] for node in nodes}
    edges = []
    for idx, (head, relation, tail) in enumerate(SCHEMA_EDGE_TYPES, start=1):
        edges.append(
            {
                "edge_id": f"schema_r{idx}",
                "head": by_text[head],
                "relation": relation,
                "tail": by_text[tail],
                "layer": "schema",
                "evidence": [],
                "confidence": 1.0,
            }
        )
    return edges


def merge_graph(mechanism_graph: dict[str, Any]) -> dict[str, Any]:
    schema_nodes = schema_graph_nodes()
    schema_edges = schema_graph_edges(schema_nodes)
    mechanism_nodes = []
    for node in mechanism_graph.get("nodes", []):
        new_node = dict(node)
        new_node["node_id"] = f"m_{node['node_id']}"
        new_node["layer"] = "mechanism"
        mechanism_nodes.append(new_node)
    mechanism_edges = []
    for edge in mechanism_graph.get("edges", []):
        new_edge = dict(edge)
        new_edge["edge_id"] = f"m_{edge['edge_id']}"
        new_edge["head"] = f"m_{edge['head']}"
        new_edge["tail"] = f"m_{edge['tail']}"
        new_edge["layer"] = "mechanism"
        mechanism_edges.append(new_edge)

    return {
        "status": "quality_traceability_large_kg_seed",
        "description": "Seed instantiation of a future quality-traceability large KG. Mechanism graph comes from the seed extraction experiment; instance layer is a schema hook for future production/event data.",
        "nodes": schema_nodes + mechanism_nodes,
        "edges": schema_edges + mechanism_edges,
        "summary": {
            "schema_node_count": len(schema_nodes),
            "schema_edge_count": len(schema_edges),
            "mechanism_node_count": len(mechanism_nodes),
            "mechanism_edge_count": len(mechanism_edges),
            "total_node_count": len(schema_nodes) + len(mechanism_nodes),
            "total_edge_count": len(schema_edges) + len(mechanism_edges),
        },
    }


def best_method(metrics: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    if not metrics:
        return None
    return max(metrics, key=lambda row: float(row.get("triple_f1") or 0.0))


def evidence_summary(metrics: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_method = {row["method"]: row for row in metrics}
    proposed = by_method.get("proposed_atom_adjudication_proxy")
    baseline = by_method.get("plm_candidate_proxy") or by_method.get("rule_based")
    delta = None
    hallucination_reduction = None
    if proposed and baseline:
        delta = round(float(proposed["triple_f1"]) - float(baseline["triple_f1"]), 4)
        hallucination_reduction = round(float(baseline["hallucination_rate"]) - float(proposed["hallucination_rate"]), 4)
    return {
        "best_method": best_method(metrics),
        "proposed_vs_candidate_triple_f1_delta": delta,
        "proposed_vs_candidate_hallucination_rate_reduction": hallucination_reduction,
        "metric_status": "seed_proxy_result",
        "publication_caveat": "Use these results only as engineering evidence. Paper claims require real mechanism text corpus, real PLM/LLM backends, and held-out test reporting.",
    }


def build_experiment_protocol(
    metrics: Sequence[dict[str, Any]],
    large_graph: dict[str, Any],
    baosteel_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    evidence = evidence_summary(metrics)
    seed_scale = large_graph["summary"]
    instance_records = baosteel_manifest.get("records") if baosteel_manifest else None
    rows = [
        {
            "experiment_id": "QKG-E0",
            "track": "completed_seed_evidence",
            "purpose": "Check that the mechanism extraction pipeline can produce schema-valid records, final predictions, metrics, and a seed graph.",
            "dataset": "generated_mechanism_kg_seed",
            "methods": "rule_based; plm_candidate_proxy; proposed_atom_adjudication_proxy",
            "primary_metrics": "Entity F1; Relation F1; Triple F1; Hallucination Rate; Hard Negative Accuracy",
            "expected_evidence": "A reproducible seed run with machine-readable outputs and validation reports.",
            "status": "completed_seed_proxy",
            "current_result": f"best={evidence['best_method']['method'] if evidence['best_method'] else 'none'}; nodes={seed_scale['total_node_count']}; edges={seed_scale['total_edge_count']}",
        },
        {
            "experiment_id": "QKG-E1",
            "track": "main_extraction_effectiveness",
            "purpose": "Prove the proposed PLM-guided prompt-atom adjudication method improves mechanism KG extraction.",
            "dataset": "document-split mechanism corpus from papers/manuals/expert rules",
            "methods": "rule_based; plm_only; llm_zero_shot; llm_few_shot; GLiNER; InstructUIE; GoLLIE; Code4UIE; KnowCoder; DeepKE-LLM; constrained_json_llm; proposed",
            "primary_metrics": "Entity F1; Relation F1; Triple F1; Evidence F1; Direction Accuracy",
            "expected_evidence": "Proposed improves Triple F1 and evidence grounding over PLM-only, LLM-only, and simple cascade baselines.",
            "status": "planned_paper_scale",
            "current_result": "requires real corpus and real model backends",
        },
        {
            "experiment_id": "QKG-E2",
            "track": "low_resource_extraction",
            "purpose": "Show why the method fits low-annotation industrial mechanism extraction.",
            "dataset": "50/100/300/500-record train budgets with fixed dev/test documents",
            "methods": "plm_only; llm_few_shot; plm_llm_cascade; proposed",
            "primary_metrics": "Triple F1; low-resource area under curve; Token/record; Time/record",
            "expected_evidence": "Proposed is more stable than PLM-only under few labels and cheaper than LLM-only full extraction.",
            "status": "planned_paper_scale",
            "current_result": "requires budgeted train splits",
        },
        {
            "experiment_id": "QKG-E3",
            "track": "plm_prompt_fusion_ablation",
            "purpose": "Prove PLM is structurally useful rather than an optional add-on.",
            "dataset": "same held-out mechanism corpus",
            "methods": "no_atom; full_prompt; random_atom; rule_atom; plm_uncertainty_atom; proposed_full",
            "primary_metrics": "Triple F1; hallucination rate; LLM call precision; Token/record",
            "expected_evidence": "PLM uncertainty/evidence/atom routing outperforms random or static prompts and reduces unnecessary LLM calls.",
            "status": "planned_paper_scale",
            "current_result": "seed proxy already shows lower hallucination for proposed method",
        },
        {
            "experiment_id": "QKG-E4",
            "track": "hard_negative_and_hallucination",
            "purpose": "Verify that unsupported but plausible triples are rejected.",
            "dataset": "mechanism corpus plus hard negative entity pairs",
            "methods": "llm_free_extraction; plm_llm_cascade; proposed",
            "primary_metrics": "Hard Negative Accuracy; Unsupported Triple Rate; Hallucination Rate",
            "expected_evidence": "Constrained adjudication plus evidence atoms rejects plausible-but-unsupported triples better than free extraction.",
            "status": "planned_paper_scale",
            "current_result": f"seed proposed hard-negative accuracy={evidence['best_method'].get('hard_negative_accuracy') if evidence['best_method'] else 'n/a'}",
        },
        {
            "experiment_id": "QKG-E5",
            "track": "graph_level_quality",
            "purpose": "Evaluate whether better extraction creates a better mechanism graph.",
            "dataset": "assembled KG from each extraction method",
            "methods": "graph_exact; graph_canonicalized; expert_audit",
            "primary_metrics": "node duplicate rate; relation conflict rate; mechanism-chain completeness; expert acceptability",
            "expected_evidence": "The proposed method yields cleaner causal/control chains and fewer unsupported graph edges.",
            "status": "planned_paper_scale",
            "current_result": "seed graph files are available for graph-level tooling",
        },
        {
            "experiment_id": "QKG-E6",
            "track": "traceability_attachment_validation",
            "purpose": "Show that the mechanism KG can be attached to later quality traceability work without using production rows as extraction gold.",
            "dataset": "downstream production/event records attached after extraction",
            "methods": "entity alignment; event-to-mechanism explanation paths; case-study expert audit",
            "primary_metrics": "trace path hit rate; explanation completeness; expert acceptability; case retrieval precision",
            "expected_evidence": "Quality events can be explained through evidence-backed mechanism paths and recommended actions.",
            "status": "planned_downstream_validation",
            "current_result": f"available instance-pool records={instance_records}" if instance_records else "instance pool pending",
        },
        {
            "experiment_id": "QKG-E7",
            "track": "frontier_baseline_comparison",
            "purpose": "Benchmark recent generalist, guideline-following, code-generation, and constrained-output IE methods against the proposed PLM-guided atom adjudication framework.",
            "dataset": "same document-split mechanism corpus and seed proxy dataset for smoke testing",
            "methods": "GLiNER; InstructUIE; GoLLIE; Code4UIE; KnowCoder; DeepKE-LLM; constrained_json_llm; retrieval_augmented_schema_prompt",
            "primary_metrics": "Entity F1; Relation F1; Triple F1; Evidence F1; Invalid Output Rate",
            "expected_evidence": "Frontier baselines clarify whether gains come from schema following, retrieval, constrained decoding, or PLM-guided atom routing.",
            "status": "planned_paper_scale",
            "current_result": "experiment matrix generated; external adapters required",
        },
    ]
    return {
        "status": "seed_plus_paper_scale_protocol",
        "completed_seed_evidence": evidence,
        "planned_experiments": rows,
        "reporting_rule": "Use QKG-E0 only as seed engineering evidence; use QKG-E1 to QKG-E7 for paper-scale claims.",
    }


def render_report(
    schema: dict[str, Any],
    large_graph: dict[str, Any],
    metrics: Sequence[dict[str, Any]],
    baosteel_manifest: dict[str, Any] | None,
) -> str:
    summary = evidence_summary(metrics)
    protocol = build_experiment_protocol(metrics, large_graph, baosteel_manifest)
    lines = [
        "# Quality Traceability Large KG Pack",
        "",
        "## Scope",
        "",
        "This pack defines a large-KG structure that can later absorb quality-traceability instance data. The current mechanism extraction experiment does not use processed Baosteel production rows as its primary source.",
        "",
        "## KG Layers",
        "",
    ]
    for layer, description in schema["layers"].items():
        lines.append(f"- `{layer}`: {description}")
    lines.extend(
        [
            "",
            "## Seed Graph Scale",
            "",
            f"- Schema nodes: {large_graph['summary']['schema_node_count']}",
            f"- Schema edges: {large_graph['summary']['schema_edge_count']}",
            f"- Mechanism nodes: {large_graph['summary']['mechanism_node_count']}",
            f"- Mechanism edges: {large_graph['summary']['mechanism_edge_count']}",
            f"- Total nodes: {large_graph['summary']['total_node_count']}",
            f"- Total edges: {large_graph['summary']['total_edge_count']}",
            "",
            "## Extraction Metrics",
            "",
            "| Method | Entity F1 | Relation F1 | Triple F1 | Hallucination Rate | Hard Negative Accuracy |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in metrics:
        lines.append(
            f"| `{row['method']}` | {row['entity_f1']} | {row['relation_f1']} | {row['triple_f1']} | {row['hallucination_rate']} | {row['hard_negative_accuracy']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Summary",
            "",
            f"- Best seed method: `{summary['best_method']['method'] if summary['best_method'] else 'none'}`",
            f"- Proposed vs candidate Triple F1 delta: `{summary['proposed_vs_candidate_triple_f1_delta']}`",
            f"- Proposed vs candidate hallucination-rate reduction: `{summary['proposed_vs_candidate_hallucination_rate_reduction']}`",
            "",
            "## Extraction Experiment Protocol",
            "",
            "| ID | Track | Status | Primary Metrics |",
            "|---|---|---|---|",
        ]
    )
    for row in protocol["planned_experiments"]:
        lines.append(
            f"| `{row['experiment_id']}` | {row['track']} | {row['status']} | {row['primary_metrics']} |"
        )
    lines.extend(
        [
            "",
            "## Downstream Traceability Hook",
            "",
        ]
    )
    if baosteel_manifest:
        lines.extend(
            [
                f"- Existing Baosteel instance pool records: `{baosteel_manifest.get('records')}`",
                "- Position: downstream instance-layer attachment and application validation only.",
            ]
        )
    else:
        lines.append("- Baosteel instance manifest not found; instance-layer attachment remains pending.")
    lines.extend(
        [
            "",
            "## Required Paper-Scale Experiments",
            "",
            "1. Replace generated seed data with a document-split corpus from papers/manuals/expert rules.",
            "2. Replace deterministic proxy candidate generation with real PLM NER/RE/evidence models.",
            "3. Replace deterministic proxy adjudication with a real constrained LLM backend.",
            "4. Report main effectiveness, low-resource, prompt-atom ablation, PLM role ablation, and graph-level evaluation.",
            "5. Use Baosteel or other production data only after mechanism KG extraction, as instance-layer traceability validation.",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(
    *,
    mechanism_graph_path: Path = DEFAULT_MECHANISM_GRAPH,
    metrics_path: Path = DEFAULT_METRICS,
    baosteel_manifest_path: Path = DEFAULT_BAOSTEEL_MANIFEST,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    kg_dir: Path = DEFAULT_KG_DIR,
) -> dict[str, Any]:
    mechanism_graph = read_json(mechanism_graph_path, {"nodes": [], "edges": [], "summary": {}})
    metrics = read_json(metrics_path, [])
    baosteel_manifest = read_json(baosteel_manifest_path, None)

    schema = build_schema()
    large_graph = merge_graph(mechanism_graph)
    evidence = evidence_summary(metrics)
    protocol = build_experiment_protocol(metrics, large_graph, baosteel_manifest)

    write_json(kg_dir / "schema.json", schema)
    write_json(kg_dir / "quality_traceability_large_kg_seed.json", large_graph)
    write_json(kg_dir / "manifest.json", {
        "status": "large_kg_seed_pack",
        "schema_path": str(kg_dir / "schema.json"),
        "graph_path": str(kg_dir / "quality_traceability_large_kg_seed.json"),
        "source_mechanism_graph": str(mechanism_graph_path),
        "source_metrics": str(metrics_path),
        "extraction_evidence": evidence,
        "experiment_protocol": str(output_dir / "extraction_experiment_protocol.json"),
        "downstream_instance_manifest": str(baosteel_manifest_path) if baosteel_manifest else None,
    })

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "large_kg_schema.json", schema)
    write_json(output_dir / "large_kg_seed_graph.json", large_graph)
    write_json(output_dir / "extraction_evidence_summary.json", evidence)
    write_json(output_dir / "extraction_experiment_protocol.json", protocol)
    write_csv(output_dir / "extraction_experiment_matrix.csv", protocol["planned_experiments"])
    if metrics:
        write_csv(output_dir / "extraction_metrics.csv", metrics)
    report = render_report(schema, large_graph, metrics, baosteel_manifest)
    (output_dir / "quality_traceability_large_kg_report.md").write_text(report, encoding="utf-8")

    summary = {
        "status": "quality_traceability_large_kg_pack_built",
        "kg_dir": str(kg_dir),
        "output_dir": str(output_dir),
        "graph_summary": large_graph["summary"],
        "extraction_evidence": evidence,
        "experiment_protocol": str(output_dir / "extraction_experiment_protocol.json"),
        "report": str(output_dir / "quality_traceability_large_kg_report.md"),
    }
    write_json(output_dir / "pack_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build quality traceability large-KG pack.")
    parser.add_argument("--mechanism-graph", type=Path, default=DEFAULT_MECHANISM_GRAPH)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--baosteel-manifest", type=Path, default=DEFAULT_BAOSTEEL_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--kg-dir", type=Path, default=DEFAULT_KG_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_pack(
        mechanism_graph_path=args.mechanism_graph,
        metrics_path=args.metrics,
        baosteel_manifest_path=args.baosteel_manifest,
        output_dir=args.output_dir,
        kg_dir=args.kg_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
