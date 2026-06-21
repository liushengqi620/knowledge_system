from __future__ import annotations

import unittest

from summarize_manuscript_full_draft import render_draft


class SummarizeManuscriptFullDraftTest(unittest.TestCase):
    def test_render_draft_contains_submission_level_paper_skeleton(self) -> None:
        draft = render_draft()

        self.assertIn("# Reliability-Calibrated Mechanism Evidence Fusion", draft)
        self.assertIn("## Abstract", draft)
        self.assertIn("non-interventional industrial time-series", draft)
        self.assertIn("candidate mechanism evidence", draft)
        self.assertIn("## 1. Introduction", draft)
        self.assertIn("cannot simply replace causality with correlation", draft)
        self.assertIn("## 2. Related Work Positioning", draft)
        self.assertIn("## 3. Problem Formulation", draft)
        self.assertIn("p_0(i) = f_0(x_i)", draft)
        self.assertIn("p_k(i) = f_k(x_i, r_i, g_i, m_k)", draft)
        self.assertIn("## 4. Method", draft)
        self.assertIn("Evidence Reliability Estimator", draft)
        self.assertIn("R_k =", draft)
        self.assertIn("A_R =", draft)
        self.assertIn("p^*(i)", draft)
        self.assertIn("## 5. Theoretical Claim Boundary", draft)
        self.assertIn("not a distribution-free causal guarantee", draft)
        self.assertIn("## 6. Experiments", draft)
        self.assertIn("TEP", draft)
        self.assertIn("SKAB", draft)
        self.assertIn("Hydraulic", draft)
        self.assertIn("C-MAPSS", draft)
        self.assertIn("0.9549 +/- 0.0023", draft)
        self.assertIn("0.8532 +/- 0.0339", draft)
        self.assertIn("## 7. Ablation and Reliability Analysis", draft)
        self.assertIn("prior-only", draft)
        self.assertIn("all-edge", draft)
        self.assertIn("GRU w80/cap125 RMSE `20.7559`", draft)
        self.assertIn("GRU w160/cap150 RMSE `18.0617`", draft)
        self.assertIn("pseudo-terminal validation rerun RMSE `18.2840`", draft)
        self.assertIn("PHM score favors GRU w80/cap150 by `408.20`", draft)
        self.assertIn("AnchorPath w80/cap150 RMSE `18.6666` is not admitted", draft)
        self.assertIn("## 8. Limitations", draft)
        self.assertIn("## 9. Current Missing Pieces Before Submission", draft)
        self.assertIn("exact external protocol alignment", draft)
        self.assertIn("## Artifact Map", draft)
        self.assertIn("manuscript_method_theory_section.md", draft)
        self.assertIn("final_reliability_ablation_table.md", draft)


if __name__ == "__main__":
    unittest.main()
