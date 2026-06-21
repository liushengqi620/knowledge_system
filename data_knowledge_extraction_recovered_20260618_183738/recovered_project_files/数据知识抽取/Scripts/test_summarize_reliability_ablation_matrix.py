from __future__ import annotations

import unittest

from Scripts.summarize_reliability_ablation_matrix import current_ablation_rows, render_report


class SummarizeReliabilityAblationMatrixTest(unittest.TestCase):
    def test_renders_theory_critical_ablation_status_and_next_runs(self) -> None:
        report = render_report(current_ablation_rows())

        self.assertIn("# Theory-Critical Reliability Ablation Matrix", report)
        self.assertIn("reliability_theory_model.md", report)
        self.assertIn("reliability_term_evidence_table.md", report)
        self.assertIn("low-tail guard", report)
        self.assertIn("Covered", report)
        self.assertIn("counterfactual-free admission", report)
        self.assertIn("Partial", report)
        self.assertIn("attention/edge-gate replacement", report)
        self.assertIn("Missing", report)
        self.assertIn("all LLM edges without reliability filtering", report)
        self.assertIn("Run next", report)
        self.assertIn("AAAI blocking", report)
        self.assertIn("no-low-tail", report)
        self.assertIn("no-counterfactual", report)


if __name__ == "__main__":
    unittest.main()
