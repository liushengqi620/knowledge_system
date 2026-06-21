from pathlib import Path

from experiments.prompt_atom_decomposition_experiment import (
    ERROR_PROBES,
    build_atoms,
    evaluate_strategy,
    run,
)


def test_all_decomposition_strategies_generate_atoms():
    strategies = [
        "no_atom",
        "fsdv_block",
        "sentence_level",
        "random_atom",
        "over_fine",
        "functional_atom",
    ]
    for strategy in strategies:
        atoms = build_atoms(strategy, seed=2026)
        assert atoms, strategy
        assert all(atom.tags for atom in atoms)


def test_functional_atoms_have_better_locality_than_coarse_prompt():
    no_atom = evaluate_strategy("no_atom")
    functional = evaluate_strategy("functional_atom")
    assert functional["edit_locality"] > no_atom["edit_locality"]
    assert functional["diagnostic_score"] > no_atom["diagnostic_score"]


def test_over_fine_strategy_has_fragmentation_risk():
    over_fine = evaluate_strategy("over_fine")
    functional = evaluate_strategy("functional_atom")
    assert over_fine["over_fine_risk"] > functional["over_fine_risk"]
    assert over_fine["semantic_completeness"] < functional["semantic_completeness"]


def test_each_error_probe_has_attribution_under_functional_atoms():
    atoms = build_atoms("functional_atom")
    for probe in ERROR_PROBES:
        matches = [atom for atom in atoms if atom.tags.intersection(probe.required_tags)]
        assert matches, probe.error_id


def test_run_writes_expected_artifacts(tmp_path: Path):
    rows = run(tmp_path, seed=2026)
    assert len(rows) == 6
    assert (tmp_path / "diagnostic_results.json").exists()
    assert (tmp_path / "diagnostic_summary.csv").exists()
    assert (tmp_path / "diagnostic_table.tex").exists()
    assert (tmp_path / "experiment_protocol.md").exists()
