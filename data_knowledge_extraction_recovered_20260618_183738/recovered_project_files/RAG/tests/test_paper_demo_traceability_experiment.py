from pathlib import Path
import json


def _write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_paper_demo_traceability_outputs(tmp_path: Path):
    from experiments.run_paper_demo_traceability_experiment import run_demo

    train_rows = [
        {
            "record_id": "train-speed",
            "text": "main group speed_stopper_flow",
            "source": {
                "quality_abnormal_group": "speed_stopper_flow",
                "quality_abnormal_groups": "speed_stopper_flow",
                "selected_features": [{"name": "cast_speed_range", "value": "0.3", "group": "casting_speed"}],
            },
        },
        {
            "record_id": "train-mold",
            "text": "main group mold_level_slag_risk",
            "source": {
                "quality_abnormal_group": "mold_level_slag_risk",
                "quality_abnormal_groups": "mold_level_slag_risk",
                "selected_features": [{"name": "mold_level_range", "value": "30", "group": "mold_level"}],
            },
        },
    ]
    test_rows = [
        {
            "record_id": "test-speed",
            "text": "main group speed_stopper_flow",
            "source": {
                "quality_abnormal_group": "speed_stopper_flow",
                "quality_abnormal_groups": "speed_stopper_flow",
                "selected_features": [{"name": "cast_speed_mean", "value": "1.2", "group": "casting_speed"}],
            },
        },
        {
            "record_id": "test-mold",
            "text": "main group mold_level_slag_risk",
            "source": {
                "quality_abnormal_group": "mold_level_slag_risk",
                "quality_abnormal_groups": "mold_level_slag_risk",
                "selected_features": [{"name": "mold_level_mean", "value": "15", "group": "mold_level"}],
            },
        },
    ]
    graph = {
        "nodes": [
            {"node_id": "n1", "text": "cast speed", "type": "ProcessParameter"},
            {"node_id": "n2", "text": "flow instability", "type": "DefectMechanism"},
            {"node_id": "n3", "text": "mold level", "type": "ProcessParameter"},
            {"node_id": "n4", "text": "slag entrapment", "type": "DefectMechanism"},
        ],
        "edges": [
            {"edge_id": "e1", "head": "n1", "relation": "affect", "tail": "n2", "evidence": [{"text": "speed affects flow"}]},
            {"edge_id": "e2", "head": "n3", "relation": "cause", "tail": "n4", "evidence": [{"text": "mold level causes slag"}]},
        ],
    }
    train_path = tmp_path / "train.jsonl"
    test_path = tmp_path / "test.jsonl"
    graph_path = tmp_path / "graph.json"
    _write_jsonl(train_path, train_rows)
    _write_jsonl(test_path, test_rows)
    graph_path.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")

    summary = run_demo(
        train_path=train_path,
        test_path=test_path,
        graph_path=graph_path,
        output_dir=tmp_path / "out",
        per_label=2,
    )
    assert summary["status"] == "paper_demo_traceability_completed"
    assert (tmp_path / "out" / "metrics.json").exists()
    assert (tmp_path / "out" / "paper_demo_report.md").exists()
    assert (tmp_path / "out" / "expert_audit_template.csv").exists()
    metrics = json.loads((tmp_path / "out" / "metrics.json").read_text(encoding="utf-8"))
    scenarios = {row["scenario"] for row in metrics}
    assert {"balanced_label_masked_text", "balanced_feature_anonymized"}.issubset(scenarios)
