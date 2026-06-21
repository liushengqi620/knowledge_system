from __future__ import annotations

import unittest

from Scripts.summarize_reliability_theory_model import ReliabilityTheorySpec, render_report


class SummarizeReliabilityTheoryModelTest(unittest.TestCase):
    def test_renders_paper_ready_reliability_theory_and_objection_answers(self) -> None:
        report = render_report(ReliabilityTheorySpec.current())

        self.assertIn("# Reliability-Certified Evidence Admission Model", report)
        self.assertIn("non-interventional industrial time series", report)
        self.assertIn("z_{i,k} = 1", report)
        self.assertIn("L_{ERE}", report)
        self.assertIn("R_k =", report)
        self.assertIn("A_R = {k", report)
        self.assertIn("not an attention weight", report)
        self.assertIn("not an edge gate", report)
        self.assertIn("not graph pruning alone", report)
        self.assertIn("prevents harmful LLM edges", report)
        self.assertIn("counterfactual perturbation verifies decision relevance", report)
        self.assertIn("low-tail non-degradation", report)
        self.assertIn("TEP", report)
        self.assertIn("SKAB", report)
        self.assertIn("C-MAPSS", report)


if __name__ == "__main__":
    unittest.main()
