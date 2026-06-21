from experiments.run_atom_decomposition_result_experiment import (
    STRATEGIES,
    build_strategy_command,
    extract_transfer_metrics,
)


def test_runner_command_contains_strategy_and_output_dirs():
    cmd = build_strategy_command(
        strategy="functional_atom",
        output_root="outputs/atom_result",
        samples=8,
        valset_size=6,
        iterations=2,
        quick_eval_samples=4,
        mode="train",
    )
    joined = " ".join(cmd)
    assert "--atom_decomposition_strategy functional_atom" in joined
    assert "--output_dir outputs/atom_result/functional_atom/prompt_training" in joined
    assert "--output outputs/atom_result/functional_atom/post_eval" in joined


def test_runner_extracts_fsdv_eapa_metrics_from_transfer_results():
    report = {
        "results": {
            "FSDV": {"avg_f1": 0.75},
            "FSDV-EAPA": {
                "avg_ner_f1": 0.91,
                "avg_re_f1": 0.80,
                "avg_f1": 0.855,
                "avg_khr": 0.04,
            },
        }
    }
    row = extract_transfer_metrics("functional_atom", report)
    assert row["strategy"] == "functional_atom"
    assert row["ner_f1"] == 0.91
    assert row["re_f1"] == 0.80
    assert row["overall_f1"] == 0.855
    assert row["khr"] == 0.04


def test_runner_strategy_list_matches_atom_ablation_design():
    assert STRATEGIES == [
        "no_atom",
        "fsdv_block",
        "sentence_level",
        "random_atom",
        "over_fine",
        "functional_atom",
    ]
