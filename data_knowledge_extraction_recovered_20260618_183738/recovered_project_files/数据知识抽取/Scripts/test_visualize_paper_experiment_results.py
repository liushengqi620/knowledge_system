from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from visualize_paper_experiment_results import (
    EXPECTED_FIGURES,
    build_experiment_tables,
    generate_all_visualizations,
    render_visualization_report,
)


class VisualizePaperExperimentResultsTest(unittest.TestCase):
    def test_build_experiment_tables_contains_all_core_experiment_groups(self) -> None:
        tables = build_experiment_tables()

        self.assertIn("main_multi_benchmark", tables)
        self.assertIn("reliability_ablation", tables)
        self.assertIn("tep_mechanism_ablation", tables)
        self.assertIn("tep_matched_baselines", tables)
        self.assertIn("skab_external_baselines", tables)
        self.assertIn("hydraulic_four_target", tables)
        self.assertIn("cmapss_rul_matched", tables)

        self.assertEqual(4, len(tables["main_multi_benchmark"]))
        self.assertEqual(6, len(tables["tep_mechanism_ablation"]))
        self.assertEqual(4, len(tables["hydraulic_four_target"]))
        self.assertEqual(8, len(tables["cmapss_rul_matched"]))
        self.assertTrue(any(row["method"] == "GRU w160/c150 pseudo" and row["rmse"] == 18.2840 for row in tables["cmapss_rul_matched"]))

    def test_generate_all_visualizations_writes_expected_figures_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            artifacts = generate_all_visualizations(output_dir)

            for figure_name in EXPECTED_FIGURES:
                figure_path = output_dir / figure_name
                self.assertIn(figure_path, artifacts)
                self.assertTrue(figure_path.exists(), figure_name)
                self.assertGreater(figure_path.stat().st_size, 1000, figure_name)

            report_path = output_dir / "experiment_visualization_report.md"
            self.assertTrue(report_path.exists())
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("# Paper Experiment Result Visualizations", report)
            self.assertIn("main_multi_benchmark_results.png", report)
            self.assertIn("tep_mechanism_ablation.png", report)
            self.assertIn("cmapss_rul_matched_results.png", report)

    def test_render_visualization_report_describes_claim_boundary(self) -> None:
        report = render_visualization_report(Path("knowledge_exports/paper_experiment_visualizations"))

        self.assertIn("matched-protocol", report)
        self.assertIn("SOTA candidate", report)
        self.assertIn("not official universal SOTA", report)
        self.assertIn("PHM score trade-off", report)


if __name__ == "__main__":
    unittest.main()
