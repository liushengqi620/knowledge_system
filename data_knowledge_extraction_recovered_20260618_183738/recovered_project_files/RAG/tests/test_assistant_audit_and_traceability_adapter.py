import csv
import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECOVERED_ROOT = PROJECT_ROOT.parent
TRACE_SYSTEM_ROOT = RECOVERED_ROOT / "溯源系统"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_assistant_traceability_audit_scores(tmp_path: Path):
    from experiments.fill_assistant_traceability_audit import fill_assistant_audit

    blind = tmp_path / "blind.csv"
    key = tmp_path / "key.csv"
    out = tmp_path / "assistant.csv"
    _write_csv(
        blind,
        [
            {
                "case_id": "TACE-0001",
                "scenario": "balanced",
                "predicted_top3": "cause_a;cause_b",
                "top_features": "feature_a",
                "trace_path": "A [cause] B",
                "path_quality_proxy": "0.8",
                "expert_root_cause_correct": "",
                "expert_path_plausible": "",
                "expert_action_useful": "",
                "expert_notes": "",
            }
        ],
    )
    _write_csv(key, [{"case_id": "TACE-0001", "record_id": "r1", "gold_primary_label": "cause_a"}])
    summary = fill_assistant_audit(blind, key, out)
    assert summary["status"] == "assistant_traceability_audit_filled"
    rows = list(csv.DictReader(out.open("r", encoding="utf-8-sig", newline="")))
    assert rows[0]["expert_root_cause_correct"] == "1.0"
    assert rows[0]["expert_path_plausible"] == "1.0"
    assert rows[0]["review_type"] == "ai_precheck_not_expert_validation"


def test_mechanism_kg_traceability_adapter_builds_rules(tmp_path: Path):
    module = _load_module(
        TRACE_SYSTEM_ROOT / "src" / "mechanism_kg_traceability_adapter.py",
        "mechanism_kg_traceability_adapter_for_test",
    )
    graph = {
        "nodes": [
            {"node_id": "n1", "text": "mold level fluctuation", "type": "EquipmentState"},
            {"node_id": "n2", "text": "slag entrapment", "type": "DefectMechanism"},
            {"node_id": "n3", "text": "surface crack risk", "type": "QualityDefect"},
            {"node_id": "n4", "text": "stabilize mold level", "type": "ControlAction"},
        ],
        "edges": [
            {
                "edge_id": "e1",
                "head": "n1",
                "relation": "cause",
                "tail": "n2",
                "layer": "mechanism",
                "confidence": 0.9,
                "evidence": [{"text": "mold level fluctuation causes slag entrapment"}],
            },
            {
                "edge_id": "e2",
                "head": "n2",
                "relation": "increase_risk_of",
                "tail": "n3",
                "layer": "mechanism",
                "confidence": 0.9,
                "evidence": [{"text": "slag entrapment increases surface crack risk"}],
            },
            {
                "edge_id": "e3",
                "head": "n1",
                "relation": "improve",
                "tail": "n4",
                "layer": "mechanism",
                "confidence": 0.9,
                "evidence": [{"text": "stabilize mold level improves quality"}],
            },
        ],
    }
    kg_path = tmp_path / "graph.json"
    kg_path.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")
    summary = module.build_adapter_pack(kg_path, tmp_path / "pack", min_confidence=0.7, max_rules=10)
    assert summary["status"] == "mechanism_kg_traceability_adapter_built"
    assert summary["rule_count"] == 2
    rules = json.loads((tmp_path / "pack" / "mechanism_traceability_rules.json").read_text(encoding="utf-8"))
    assert rules["rules"][0]["solution"] == "stabilize mold level"
    assert (tmp_path / "pack" / "mechanism_traceability_seed.cypher").exists()
