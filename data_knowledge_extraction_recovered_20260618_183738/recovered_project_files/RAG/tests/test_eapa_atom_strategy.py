from experiments import prompt_engineering_ablation as pea


SAMPLE_STAGE_TEXT = """
Extract only text-supported industrial knowledge.

Entity types include ProcessParameter and QualityDefect.

Relation types include cause and improve. Causal relations must follow cause-to-effect direction.

Return schema-valid JSON with entities and relations.
""".strip()


def test_prompt_atom_strategy_changes_stage_granularity():
    pea.set_atom_decomposition_strategy("functional_atom")
    functional = pea.decompose_prompt_to_min_atoms(SAMPLE_STAGE_TEXT, "S")

    pea.set_atom_decomposition_strategy("no_atom")
    monolithic = pea.decompose_prompt_to_min_atoms(SAMPLE_STAGE_TEXT, "S")

    pea.set_atom_decomposition_strategy("over_fine")
    over_fine = pea.decompose_prompt_to_min_atoms(SAMPLE_STAGE_TEXT, "S")

    assert len(monolithic) == 1
    assert len(functional) > len(monolithic)
    assert len(over_fine) > len(functional)


def test_unknown_prompt_atom_strategy_is_rejected():
    try:
        pea.set_atom_decomposition_strategy("unknown")
    except ValueError as exc:
        assert "Unsupported atom decomposition strategy" in str(exc)
    else:
        raise AssertionError("unknown strategy should be rejected")
    finally:
        pea.set_atom_decomposition_strategy("functional_atom")
