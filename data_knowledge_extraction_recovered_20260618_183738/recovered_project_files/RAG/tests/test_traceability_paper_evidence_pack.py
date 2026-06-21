import csv
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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


def _metric(scenario: str, method: str, hit1: float, hit3: float, coverage: float, path_quality: float) -> dict[str, object]:
    return {
        "scenario": scenario,
        "method": method,
        "primary_hit1": hit1,
        "primary_hit3": hit3,
        "mrr": hit3,
        "macro_f1": hit1 / 2,
        "explanation_coverage": coverage,
        "avg_path_quality": path_quality,
        "faithful_path_rate": path_quality,
    }


def test_traceability_paper_evidence_pack_pending_and_scored(tmp_path: Path):
    from experiments.build_traceability_paper_evidence_pack import build_evidence_pack

    demo_dir = tmp_path / "demo"
    metrics = [
        _metric("full_weak_label_masked_text", "feature_group_prior", 0.9, 0.9, 0.0, 0.0),
        _metric("full_weak_label_masked_text", "kg_path_reasoning", 0.3, 0.6, 0.8, 0.7),
        _metric("full_weak_label_masked_text", "proposed_explainable_rerank", 0.9, 0.95, 0.5, 0.4),
        _metric("balanced_label_masked_text", "label_prior_majority", 0.1, 0.3, 0.0, 0.0),
        _metric("balanced_label_masked_text", "feature_group_prior", 0.9, 0.9, 0.0, 0.0),
        _metric("balanced_label_masked_text", "feature_name_naive_bayes", 0.9, 0.9, 0.0, 0.0),
        _metric("balanced_label_masked_text", "kg_anchor_reasoning", 0.4, 0.7, 0.0, 0.0),
        _metric("balanced_label_masked_text", "kg_path_reasoning", 0.35, 0.65, 0.85, 0.75),
        _metric("balanced_label_masked_text", "proposed_score_fusion", 0.9, 0.95, 0.55, 0.5),
        _metric("balanced_label_masked_text", "proposed_explainable_rerank", 0.92, 0.96, 0.6, 0.55),
        _metric("balanced_group_only", "feature_group_prior", 0.8, 0.9, 0.0, 0.0),
        _metric("balanced_group_only", "kg_path_reasoning", 0.4, 0.7, 0.3, 0.25),
        _metric("balanced_group_only", "proposed_score_fusion", 0.85, 0.9, 0.2, 0.2),
        _metric("balanced_group_only", "proposed_explainable_rerank", 0.86, 0.91, 0.25, 0.22),
        _metric("balanced_feature_anonymized", "feature_group_prior", 0.2, 0.4, 0.0, 0.0),
        _metric("balanced_feature_anonymized", "kg_path_reasoning", 0.3, 0.5, 0.0, 0.0),
        _metric("balanced_feature_anonymized", "proposed_explainable_rerank", 0.35, 0.55, 0.0, 0.0),
    ]
    audit_rows = [
        {
            "scenario": "balanced_label_masked_text",
            "record_id": "case-1",
            "gold_primary_label": "cause-a",
            "predicted_top3": "cause-a;cause-b",
            "top_features": "feature-a",
            "trace_path": "A [affect] B",
            "path_quality_proxy": "0.8",
            "expert_root_cause_correct": "",
            "expert_path_plausible": "",
            "expert_action_useful": "",
            "expert_notes": "",
        }
    ]
    _write_json(demo_dir / "metrics.json", metrics)
    _write_csv(demo_dir / "expert_audit_template.csv", audit_rows)

    summary = build_evidence_pack(demo_dir=demo_dir, output_dir=tmp_path / "pack_pending")
    assert summary["status"] == "traceability_paper_evidence_pack_built"
    assert summary["audit_status"] == "audit_pending"
    assert (tmp_path / "pack_pending" / "paper_ready_tables.md").exists()
    assert (tmp_path / "pack_pending" / "paper_ready_tables.tex").exists()
    assert (tmp_path / "pack_pending" / "explainability_path_quality.svg").exists()
    assert (tmp_path / "pack_pending" / "expert_audit_blind.csv").exists()
    assert (tmp_path / "pack_pending" / "expert_audit_key.csv").exists()

    scored_rows = [
        {**audit_rows[0], "expert_root_cause_correct": "1", "expert_path_plausible": "1", "expert_action_useful": "0.5"},
        {**audit_rows[0], "expert_root_cause_correct": "1", "expert_path_plausible": "0.5", "expert_action_useful": "0"},
    ]
    _write_csv(demo_dir / "expert_audit_template.csv", scored_rows)
    scored_summary = build_evidence_pack(demo_dir=demo_dir, output_dir=tmp_path / "pack_scored")
    assert scored_summary["audit_status"] == "audit_scored"
    scores = json.loads((tmp_path / "pack_scored" / "expert_audit_scores.json").read_text(encoding="utf-8"))
    assert scores["complete_case_count"] == 2
    assert scores["dimensions"][0]["usable_acceptance_rate"] == 1.0
    assert scores["inter_reviewer_agreement"][0]["reviewer_pairs"] == 1
