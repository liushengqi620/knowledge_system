from __future__ import annotations

import unittest

from summarize_paper_core_figures import render_figures


class SummarizePaperCoreFiguresTest(unittest.TestCase):
    def test_render_figures_contains_three_submission_ready_mermaid_figures(self) -> None:
        report = render_figures()

        self.assertIn("# Core Paper Figures", report)
        self.assertIn("Figure 1. Reliability-Calibrated Mechanism Evidence Fusion", report)
        self.assertIn("```mermaid", report)
        self.assertIn("Strong Anchor Model", report)
        self.assertIn("Expert Knowledge", report)
        self.assertIn("LLM Weak-Class Verifier", report)
        self.assertIn("Lagged Statistical Relations", report)
        self.assertIn("Residual Dynamics", report)
        self.assertIn("Evidence Reliability Estimator", report)
        self.assertIn("Admitted Mechanism Evidence", report)

        self.assertIn("Figure 2. Evidence Reliability Admission Loop", report)
        self.assertIn("Delta M_k", report)
        self.assertIn("Q_alpha", report)
        self.assertIn("CF_k", report)
        self.assertIn("C_k", report)
        self.assertIn("R_k", report)
        self.assertIn("A_R", report)
        self.assertIn("Reject or fallback", report)

        self.assertIn("Figure 3. Anchor-Challenger Deployment Rule", report)
        self.assertIn("p_0(i)", report)
        self.assertIn("p_k(i)", report)
        self.assertIn("q_psi(i,k)", report)
        self.assertIn("p^*(i)", report)
        self.assertIn("Fallback to anchor", report)

        self.assertIn("Caption:", report)
        self.assertIn("Where to use:", report)
        self.assertIn("Method section", report)
        self.assertIn("Ablation section", report)


if __name__ == "__main__":
    unittest.main()
