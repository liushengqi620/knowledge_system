import argparse
import tempfile
from pathlib import Path


def test_status_report_marks_missing_datasets():
    from experiments.experiment_status import build_status_report

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "experiments").mkdir()
        for name in [
            "prompt_atom_decomposition_experiment.py",
            "run_atom_decomposition_result_experiment.py",
            "prompt_engineering_ablation.py",
            "extended_plm_baselines.py",
            "run_local_plm_baseline.py",
            "evaluate_local_plm_baseline.py",
            "plm_external_adapters.template.json",
        ]:
            (root / "experiments" / name).write_text("{}" if name.endswith(".json") else "", encoding="utf-8")
        (root / "experiments" / "plm_external_adapters.template.json").write_text(
            '{"PURE": {"command": "python path\\\\to\\\\pure_adapter.py", "note": "pending"}}',
            encoding="utf-8",
        )

        report = build_status_report(root)
        statuses = {item["name"]: item["status"] for item in report["items"]}
        assert statuses["continuous_casting"] == "missing"
        assert statuses["electrochemistry"] == "missing"
        assert statuses["PURE"] == "pending"


def test_research_plan_keeps_real_result_ablation_scaffold_labeled():
    from experiments.build_experiment_research_plan import build_research_plan

    rows = build_research_plan()
    by_id = {row.experiment_id: row for row in rows}
    assert by_id["A3"].status in {"ready_scaffold_only", "blocked"}
    assert "real evaluator" in by_id["A3"].notes


def test_suite_dry_run_records_planned_steps(tmp_path: Path):
    from experiments.run_experiment_suite import run_suite

    args = argparse.Namespace(
        project_root=Path(__file__).resolve().parents[1],
        output_dir=tmp_path,
        phases="status,research_plan",
        dry_run=True,
        continue_on_error=False,
        force_plm_prepare=False,
    )
    steps = run_suite(args)
    assert [step.status for step in steps] == ["planned", "planned"]
    assert (tmp_path / "suite_manifest.json").exists()
    assert (tmp_path / "suite_commands.ps1").exists()
