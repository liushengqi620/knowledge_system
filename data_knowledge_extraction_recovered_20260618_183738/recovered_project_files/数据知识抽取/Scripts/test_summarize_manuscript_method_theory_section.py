from __future__ import annotations

import unittest

from summarize_manuscript_method_theory_section import render_section


class SummarizeManuscriptMethodTheorySectionTest(unittest.TestCase):
    def test_render_section_contains_submission_ready_method_and_theory(self) -> None:
        section = render_section()

        self.assertIn("# Manuscript Method and Theory Section", section)
        self.assertIn("candidate mechanism evidence", section)
        self.assertIn("not causal discovery", section)
        self.assertIn("Anchor and Candidate Challengers", section)
        self.assertIn("p_0(i) = f_0(x_i)", section)
        self.assertIn("p_k(i) = f_k(x_i, r_i, g_i, m_k)", section)

        self.assertIn("Evidence Reliability Estimator", section)
        self.assertIn("z_{i,k}", section)
        self.assertIn("q_psi(i,k)", section)
        self.assertIn("L_{ERE}", section)

        self.assertIn("Candidate-Level Reliability Certificate", section)
        self.assertIn("R_k =", section)
        self.assertIn("A_R =", section)
        self.assertIn("Delta M_k", section)
        self.assertIn("CF_k", section)
        self.assertIn("C_k", section)

        self.assertIn("Deployment Rule", section)
        self.assertIn("p^*(i)", section)
        self.assertIn("falls back to the anchor", section)

        self.assertIn("Proposition", section)
        self.assertIn("empirical low-tail degradation", section)
        self.assertIn("not a distribution-free causal guarantee", section)

        self.assertIn("Why the LLM Cannot Directly Edit Predictions", section)
        self.assertIn("not attention", section)
        self.assertIn("not an edge gate", section)
        self.assertIn("not graph pruning alone", section)

        self.assertIn("Experiment Links", section)
        self.assertIn("0.8532 +/- 0.0339", section)
        self.assertIn("0.8528 +/- 0.0322", section)
        self.assertIn("0.7093 +/- 0.0572", section)
        self.assertIn("12/12 non-degradation", section)


if __name__ == "__main__":
    unittest.main()
