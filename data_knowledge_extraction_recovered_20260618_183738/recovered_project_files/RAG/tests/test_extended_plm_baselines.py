import tempfile
import unittest
from pathlib import Path


class ExtendedPLMBaselineTests(unittest.TestCase):
    def test_budget_sampling_is_deterministic(self):
        from experiments.extended_plm_baselines import sample_budget

        data = [{"id": i} for i in range(20)]
        first = sample_budget(data, 0.25, seed=2026, min_samples=1)
        second = sample_budget(data, 0.25, seed=2026, min_samples=1)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)

    def test_experiment_matrix_contains_all_plm_runs_and_fixed_llm_refs(self):
        from experiments.extended_plm_baselines import build_experiment_matrix

        rows = build_experiment_matrix(
            datasets=["continuous_casting", "electrochemistry"],
            models=["BERT-CRF+CasRel", "PURE", "TPLinker"],
            ratios=[0.1, 0.5, 1.0],
            seeds=[2026, 2027, 2028],
            include_fixed_refs=True,
        )

        plm_rows = [r for r in rows if r["annotation_ratio"] != "--"]
        fixed_rows = [r for r in rows if r["annotation_ratio"] == "--"]
        self.assertEqual(len(plm_rows), 2 * 3 * 3 * 3)
        self.assertEqual(len(fixed_rows), 2 * 2)
        self.assertIn("adapter_status", plm_rows[0])

    def test_prepare_writes_manifest_and_results_template(self):
        from experiments.extended_plm_baselines import prepare_extended_experiment

        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            source = out_dir / "train.json"
            source.write_text(
                '[{"id": 1, "text": "a", "ner": {"entities": []}, "re": {"relations": []}},'
                '{"id": 2, "text": "b", "ner": {"entities": []}, "re": {"relations": []}}]',
                encoding="utf-8",
            )

            prepare_extended_experiment(
                output_dir=out_dir / "prepared",
                datasets=["continuous_casting"],
                source_overrides={"continuous_casting": source},
                models=["BERT-CRF+CasRel", "PURE"],
                ratios=[0.5],
                seeds=[2026],
                min_samples=1,
                prepare_only=True,
            )

            self.assertTrue((out_dir / "prepared" / "manifest.json").exists())
            self.assertTrue((out_dir / "prepared" / "results_template.csv").exists())
            self.assertTrue((out_dir / "prepared" / "run_commands.ps1").exists())


if __name__ == "__main__":
    unittest.main()
