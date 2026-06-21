from __future__ import annotations

import unittest

from summarize_manuscript_full_draft_v1 import render_draft_v1


class SummarizeManuscriptFullDraftV1Test(unittest.TestCase):
    def test_render_draft_v1_contains_expanded_submission_narrative(self) -> None:
        draft = render_draft_v1()

        self.assertIn("# Reliability-Calibrated Mechanism Evidence Fusion", draft)
        self.assertIn("## Abstract", draft)
        self.assertIn("## 1. Introduction", draft)
        self.assertIn("industrial logs usually do not contain interventions", draft)
        self.assertIn("candidate mechanism evidence", draft)
        self.assertIn("## 2. Related Work", draft)
        self.assertIn("industrial fault diagnosis", draft)
        self.assertIn("graph-based time-series diagnosis", draft)
        self.assertIn("LLM-assisted scientific reasoning", draft)

        self.assertIn("## 3. Problem Setup", draft)
        self.assertIn("p_0(i) = f_0(x_i)", draft)
        self.assertIn("p_k(i) = f_k(x_i, r_i, g_i, m_k)", draft)
        self.assertIn("## 4. Method", draft)
        self.assertIn("Evidence Reliability Estimator", draft)
        self.assertIn("R_k =", draft)
        self.assertIn("A_R =", draft)
        self.assertIn("p^*(i)", draft)
        self.assertIn("LLM verifier", draft)

        self.assertIn("## 5. Theory and Claim Boundary", draft)
        self.assertIn("empirical low-tail safety", draft)
        self.assertIn("not a distribution-free causal guarantee", draft)
        self.assertIn("## 6. Experiments", draft)
        self.assertIn("Table 1", draft)
        self.assertIn("Table 2", draft)
        self.assertIn("Figure 1", draft)
        self.assertIn("paper_final_tables.md", draft)
        self.assertIn("paper_core_figures.md", draft)
        self.assertIn("paper_protocol_sota_audit.md", draft)

        self.assertIn("0.9549 +/- 0.0023", draft)
        self.assertIn("0.8532 +/- 0.0339", draft)
        self.assertIn("12/12 non-degradation", draft)
        self.assertIn("## 7. Limitations", draft)
        self.assertIn("not universal official SOTA", draft)
        self.assertIn("## 8. Submission Checklist", draft)
        self.assertIn("camera-ready figures", draft)
        self.assertIn("exact external protocol alignment", draft)
        self.assertGreater(len(draft.split()), 1400)


if __name__ == "__main__":
    unittest.main()
