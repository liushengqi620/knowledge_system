from __future__ import annotations

import unittest

from summarize_paper_final_tables import render_tables


class SummarizePaperFinalTablesTest(unittest.TestCase):
    def test_render_tables_contains_compressed_manuscript_tables(self) -> None:
        report = render_tables()

        self.assertIn("# Paper Final Tables", report)
        self.assertIn("Table 1. Main Multi-Benchmark Results", report)
        self.assertIn("TEP", report)
        self.assertIn("0.9549 +/- 0.0023", report)
        self.assertIn("SKAB", report)
        self.assertIn("0.8532 +/- 0.0339", report)
        self.assertIn("Hydraulic", report)
        self.assertIn("C-MAPSS", report)

        self.assertIn("Table 2. Reliability Evidence Ablation", report)
        self.assertIn("prior-only", report)
        self.assertIn("all-edge", report)
        self.assertIn("CF-guarded", report)
        self.assertIn("original-task RUL", report)
        self.assertIn("GRU w80/cap125 RMSE 20.7559 -> GRU w160/cap150 RMSE 18.0617", report)
        self.assertIn("pseudo-terminal validation rerun RMSE 18.2840", report)
        self.assertIn("PHM score favors GRU w80/cap150 by 408.20", report)
        self.assertIn("AnchorPath w80/cap150 RMSE 18.6666 is not admitted", report)
        self.assertIn("not an attention weight", report)

        self.assertIn("Table 3. TEP Mechanism Ablation", report)
        self.assertIn("No expert graph / no sequence graph", report)
        self.assertIn("0.7432 +/- 0.0102", report)
        self.assertIn("No LLM graph", report)
        self.assertIn("0.9337 +/- 0.0229", report)
        self.assertIn("All edges / no sequence reliability pruning", report)

        self.assertIn("Table 4. TEP Matched Strong Baselines", report)
        self.assertIn("TCN20k-ResidualGatedLagged", report)
        self.assertIn("GRU20k-ResidualGatedLagged", report)
        self.assertIn("FT20k-ResidualGatedLagged", report)
        self.assertIn("GDN20k-ResidualGatedLagged", report)
        self.assertIn("MTADGAT20k-ResidualGatedLagged", report)

        self.assertIn("Table 5. Claim Boundary and Paper Use", report)
        self.assertIn("SOTA candidate only under matched protocol", report)
        self.assertIn("not universal official SOTA", report)
        self.assertIn("Table 6. Efficiency Audit", report)
        self.assertIn("llm_condition_candidate_gate", report)
        self.assertIn("GDN20k no/residual", report)
        self.assertIn("MTADGAT20k no/residual", report)
        self.assertIn("Where to use:", report)
        self.assertIn("main experiment section", report)


if __name__ == "__main__":
    unittest.main()
