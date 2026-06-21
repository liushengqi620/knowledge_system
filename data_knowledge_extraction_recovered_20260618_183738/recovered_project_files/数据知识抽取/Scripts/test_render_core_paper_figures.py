import tempfile
import unittest
from pathlib import Path

from render_core_paper_figures import CORE_FIGURES, render_all_core_figures


class RenderCorePaperFiguresTest(unittest.TestCase):
    def test_core_figure_specs_cover_method_figures(self):
        figure_ids = [figure.figure_id for figure in CORE_FIGURES]
        self.assertEqual(figure_ids, ["figure1", "figure2", "figure3"])

        titles = [figure.title for figure in CORE_FIGURES]
        self.assertIn("Reliability-Calibrated Mechanism Evidence Fusion", titles[0])
        self.assertIn("Evidence Reliability Admission Loop", titles[1])
        self.assertIn("Anchor-Challenger Deployment Rule", titles[2])

    def test_render_all_core_figures_writes_pdf_svg_png_and_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = render_all_core_figures(output_dir)

            expected = {
                "figure1_reliability_calibrated_mechanism_fusion.pdf",
                "figure1_reliability_calibrated_mechanism_fusion.svg",
                "figure1_reliability_calibrated_mechanism_fusion.png",
                "figure2_evidence_reliability_admission_loop.pdf",
                "figure2_evidence_reliability_admission_loop.svg",
                "figure2_evidence_reliability_admission_loop.png",
                "figure3_anchor_challenger_deployment_rule.pdf",
                "figure3_anchor_challenger_deployment_rule.svg",
                "figure3_anchor_challenger_deployment_rule.png",
                "core_paper_figures_rendered.md",
            }

            self.assertEqual({path.name for path in written}, expected)
            for name in expected:
                path = output_dir / name
                self.assertTrue(path.exists(), name)
                self.assertGreater(path.stat().st_size, 1000, name)

            index_text = (output_dir / "core_paper_figures_rendered.md").read_text(encoding="utf-8")
            self.assertIn("Figure 1", index_text)
            self.assertIn("Figure 2", index_text)
            self.assertIn("Figure 3", index_text)
            self.assertIn("submission-facing", index_text)
            self.assertIn("PDF", index_text)


if __name__ == "__main__":
    unittest.main()
