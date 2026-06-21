from pathlib import Path


def test_mechanism_kg_plan_excludes_baosteel_production_data():
    from experiments.build_mechanism_kg_experiment_plan import build_experiment_rows

    rows = build_experiment_rows()
    assert rows
    assert all(row.dataset == "mechanism_text_gold_split_by_document" for row in rows)
    assert all("baosteel" not in row.dataset.lower() for row in rows)


def test_mechanism_kg_plan_covers_required_paper_tracks(tmp_path: Path):
    from experiments.build_mechanism_kg_experiment_plan import build_experiment_rows, write_outputs

    rows = build_experiment_rows()
    tracks = {row.track for row in rows}
    assert {
        "main_effectiveness",
        "low_resource",
        "prompt_atom_ablation",
        "plm_role_ablation",
        "feedback_distillation",
        "graph_level_evaluation",
        "frontier_extraction_baselines",
    }.issubset(tracks)
    methods = {row.method for row in rows}
    assert {
        "gliner_zero_shot_ner_pair_re",
        "gollie_guideline_following",
        "code4uie_retrieval_code_generation",
        "knowcoder_code_schema_uie",
        "constrained_json_llm",
    }.issubset(methods)

    summary = write_outputs(rows, tmp_path)
    assert summary["row_count"] == len(rows)
    assert (tmp_path / "mechanism_kg_experiment_matrix.csv").exists()
    assert (tmp_path / "mechanism_kg_experiment_matrix.json").exists()
    assert (tmp_path / "mechanism_kg_experiment_plan.md").exists()
