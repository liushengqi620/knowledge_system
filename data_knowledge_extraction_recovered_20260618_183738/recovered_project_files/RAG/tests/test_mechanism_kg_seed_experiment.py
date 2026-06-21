from pathlib import Path
import json


def test_mechanism_kg_seed_experiment_writes_dataset_results_and_graph(tmp_path: Path):
    from experiments.run_mechanism_kg_seed_experiment import run_experiment
    from experiments.validate_knowledge_extraction_dataset import iter_records, validate_records

    data_dir = tmp_path / "mechanism_kg"
    output_dir = tmp_path / "outputs"
    summary = run_experiment(data_dir=data_dir, output_dir=output_dir)

    assert summary["status"] == "seed_proxy_experiment_completed"
    assert (data_dir / "annotations" / "all_records.jsonl").exists()
    assert (data_dir / "annotations" / "train.jsonl").exists()
    assert (output_dir / "final_records_with_predictions.jsonl").exists()
    assert (output_dir / "metrics.json").exists()
    assert (output_dir / "challenge_metrics.json").exists()
    assert (output_dir / "mechanism_seed_graph.json").exists()

    gold_records = list(iter_records(data_dir / "annotations" / "all_records.jsonl"))
    pred_records = list(iter_records(output_dir / "final_records_with_predictions.jsonl"))
    assert len(gold_records) == 1000
    assert summary["dataset_manifest"]["splits"] == {"train": 600, "dev": 200, "test": 200}
    assert summary["dataset_manifest"]["nested_entity_count"] == 500
    assert validate_records(gold_records) == []
    assert validate_records(pred_records) == []

    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    by_method = {row["method"]: row for row in metrics}
    assert all(row["evaluated_split"] == "test" for row in metrics)
    assert all(row["evaluated_records"] == 200 for row in metrics)
    assert by_method["rule_based"]["triple_f1"] < by_method["proposed_atom_adjudication_proxy"]["triple_f1"]
    assert by_method["plm_candidate_proxy"]["entity_precision"] >= 0.95
    assert by_method["proposed_atom_adjudication_proxy"]["triple_f1"] >= 0.95
    assert (
        by_method["proposed_atom_adjudication_proxy"]["hallucination_rate"]
        <= by_method["plm_candidate_proxy"]["hallucination_rate"]
    )
    assert (
        by_method["proposed_atom_adjudication_proxy"]["hard_negative_accuracy"]
        > by_method["plm_candidate_proxy"]["hard_negative_accuracy"]
    )

    challenge_metrics = json.loads((output_dir / "challenge_metrics.json").read_text(encoding="utf-8"))
    tags = {row["challenge_tag"] for row in challenge_metrics}
    assert {"implicit", "nested", "nested_entity", "hard_negative", "alias", "pronoun"}.issubset(tags)
    proposed_by_tag = {
        row["challenge_tag"]: row
        for row in challenge_metrics
        if row["method"] == "proposed_atom_adjudication_proxy"
    }
    assert proposed_by_tag["nested_entity"]["entity_precision"] >= 0.95
    assert proposed_by_tag["hard_negative"]["hard_negative_accuracy"] == 1.0
