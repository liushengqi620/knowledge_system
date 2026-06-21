from pathlib import Path
import json


def test_advanced_traceability_experiment_groups_outputs(tmp_path: Path):
    from experiments.build_advanced_traceability_experiment_groups import build_groups, write_outputs

    rows = build_groups()
    assert len(rows) >= 50
    tracks = {row.track for row in rows}
    assert {
        "plain_traceability_baselines",
        "anomaly_detection_backbone_comparison",
        "causal_rca_baselines",
        "kg_reasoning_for_traceability",
        "llm_and_graphrag_traceability",
        "proposed_fusion_variants",
        "component_ablation_and_sanity_checks",
    }.issubset(tracks)

    summary = write_outputs(rows, tmp_path / "out", tmp_path / "doc.md")
    assert summary["status"] == "advanced_traceability_experiment_groups_built"
    assert (tmp_path / "out" / "groups.csv").exists()
    assert (tmp_path / "out" / "groups.json").exists()
    assert (tmp_path / "out" / "groups.md").exists()
    assert (tmp_path / "doc.md").exists()

    json_rows = json.loads((tmp_path / "out" / "groups.json").read_text(encoding="utf-8"))
    methods = {row["method"] for row in json_rows}
    assert {"graph_rag_rca", "gdn_trace", "full_plm_llm_kg_traceability"}.issubset(methods)
