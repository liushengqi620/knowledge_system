import json
from pathlib import Path


def test_quality_traceability_large_kg_pack_writes_schema_graph_and_protocol(tmp_path: Path):
    from experiments.build_quality_traceability_large_kg_pack import build_pack

    mechanism_graph_path = tmp_path / "mechanism_seed_graph.json"
    metrics_path = tmp_path / "metrics.json"
    baosteel_manifest_path = tmp_path / "baosteel_manifest.json"
    output_dir = tmp_path / "outputs"
    kg_dir = tmp_path / "kg"

    mechanism_graph_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "n1",
                        "text": "mold level fluctuation",
                        "type": "ProcessParameter",
                        "record_ids": ["r1"],
                    },
                    {
                        "node_id": "n2",
                        "text": "slag entrapment",
                        "type": "QualityDefect",
                        "record_ids": ["r1"],
                    },
                ],
                "edges": [
                    {
                        "edge_id": "e1",
                        "head": "n1",
                        "relation": "increase_risk_of",
                        "tail": "n2",
                        "evidence": ["r1"],
                        "confidence": 0.91,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    metrics_path.write_text(
        json.dumps(
            [
                {
                    "method": "plm_candidate_proxy",
                    "entity_precision": 1.0,
                    "entity_recall": 1.0,
                    "entity_f1": 1.0,
                    "relation_precision": 0.8,
                    "relation_recall": 0.8,
                    "relation_f1": 0.8,
                    "triple_f1": 0.8,
                    "hallucination_rate": 0.1,
                    "hard_negative_accuracy": 0.5,
                },
                {
                    "method": "proposed_atom_adjudication_proxy",
                    "entity_precision": 1.0,
                    "entity_recall": 1.0,
                    "entity_f1": 1.0,
                    "relation_precision": 0.9,
                    "relation_recall": 0.9,
                    "relation_f1": 0.9,
                    "triple_f1": 0.9,
                    "hallucination_rate": 0.02,
                    "hard_negative_accuracy": 1.0,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    baosteel_manifest_path.write_text(json.dumps({"records": 10}), encoding="utf-8")

    summary = build_pack(
        mechanism_graph_path=mechanism_graph_path,
        metrics_path=metrics_path,
        baosteel_manifest_path=baosteel_manifest_path,
        output_dir=output_dir,
        kg_dir=kg_dir,
    )

    assert summary["status"] == "quality_traceability_large_kg_pack_built"
    assert summary["graph_summary"]["mechanism_node_count"] == 2
    assert summary["graph_summary"]["total_node_count"] > summary["graph_summary"]["mechanism_node_count"]
    assert (kg_dir / "schema.json").exists()
    assert (kg_dir / "quality_traceability_large_kg_seed.json").exists()
    assert (output_dir / "extraction_experiment_protocol.json").exists()
    assert (output_dir / "extraction_experiment_matrix.csv").exists()
    assert (output_dir / "quality_traceability_large_kg_report.md").exists()

    schema = json.loads((kg_dir / "schema.json").read_text(encoding="utf-8"))
    protocol = json.loads((output_dir / "extraction_experiment_protocol.json").read_text(encoding="utf-8"))
    assert {"mechanism", "instance", "evidence", "application"}.issubset(schema["layers"])
    assert protocol["planned_experiments"][0]["experiment_id"] == "QKG-E0"
    assert any(row["track"] == "traceability_attachment_validation" for row in protocol["planned_experiments"])
