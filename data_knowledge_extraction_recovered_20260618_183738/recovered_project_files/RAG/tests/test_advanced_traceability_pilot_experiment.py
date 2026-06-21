from pathlib import Path
import json


def _write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_advanced_traceability_pilot_writes_metrics(tmp_path: Path):
    from experiments.run_advanced_traceability_pilot_experiment import run_pilot

    train = [
        {
            "record_id": "tr-1",
            "text": "cast speed fluctuation",
            "source": {
                "quality_abnormal_group": "speed_stopper_flow",
                "quality_abnormal_groups": "speed_stopper_flow",
                "selected_features": [{"name": "cast_speed_range", "value": "0.2", "group": "casting_speed"}],
            },
        },
        {
            "record_id": "tr-2",
            "text": "mold level fluctuation",
            "source": {
                "quality_abnormal_group": "mold_level_slag_risk",
                "quality_abnormal_groups": "mold_level_slag_risk",
                "selected_features": [{"name": "mold_level_range", "value": "20", "group": "mold_level"}],
            },
        },
    ]
    test = [
        {
            "record_id": "te-1",
            "text": "cast speed abnormal",
            "source": {
                "quality_abnormal_group": "speed_stopper_flow",
                "quality_abnormal_groups": "speed_stopper_flow",
                "selected_features": [{"name": "cast_speed_mean", "value": "1.1", "group": "casting_speed"}],
            },
        }
    ]
    graph = {
        "nodes": [
            {"node_id": "n1", "text": "cast speed", "type": "ProcessParameter"},
            {"node_id": "n2", "text": "flow instability", "type": "DefectMechanism"},
            {"node_id": "n3", "text": "sliver defect risk", "type": "QualityDefect"},
        ],
        "edges": [
            {
                "edge_id": "e1",
                "head": "n1",
                "relation": "affect",
                "tail": "n2",
                "evidence": [{"text": "cast speed affects flow instability"}],
            },
            {
                "edge_id": "e2",
                "head": "n2",
                "relation": "increase_risk_of",
                "tail": "n3",
                "evidence": [{"text": "flow instability increases sliver risk"}],
            },
        ],
    }
    train_path = tmp_path / "train.jsonl"
    test_path = tmp_path / "test.jsonl"
    graph_path = tmp_path / "graph.json"
    _write_jsonl(train_path, train)
    _write_jsonl(test_path, test)
    graph_path.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")

    summary = run_pilot(train_path=train_path, test_path=test_path, graph_path=graph_path, output_dir=tmp_path / "out")
    assert summary["status"] == "advanced_traceability_pilot_completed"
    assert (tmp_path / "out" / "metrics.json").exists()
    assert (tmp_path / "out" / "predictions.jsonl").exists()
    assert (tmp_path / "out" / "report.md").exists()
    metrics = json.loads((tmp_path / "out" / "metrics.json").read_text(encoding="utf-8"))
    assert "proposed_plm_llm_kg_fusion" in {row["method"] for row in metrics}
