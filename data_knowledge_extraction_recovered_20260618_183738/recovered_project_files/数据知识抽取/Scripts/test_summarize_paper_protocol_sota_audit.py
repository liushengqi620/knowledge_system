from __future__ import annotations

import unittest

from summarize_paper_protocol_sota_audit import render_audit


class SummarizePaperProtocolSotaAuditTest(unittest.TestCase):
    def test_render_audit_contains_dataset_level_claim_boundaries(self) -> None:
        report = render_audit()

        self.assertIn("# Paper Protocol and SOTA Claim Audit", report)
        self.assertIn("method evidence", report)
        self.assertIn("official SOTA", report)
        self.assertIn("not true causal graph discovery", report)

        self.assertIn("## Dataset Claim Matrix", report)
        self.assertIn("TEP", report)
        self.assertIn("strict 22-class matched protocol", report)
        self.assertIn("0.9549 +/- 0.0023", report)
        self.assertIn("exact external protocol reproduction", report)

        self.assertIn("SKAB", report)
        self.assertIn("0.8532 +/- 0.0339", report)
        self.assertIn("official repository-level implementation alignment", report)
        self.assertIn("USAD", report)
        self.assertIn("TranAD", report)
        self.assertIn("GDN", report)
        self.assertIn("MTAD-GAT", report)

        self.assertIn("Hydraulic", report)
        self.assertIn("near-ceiling non-degradation", report)
        self.assertIn("C-MAPSS", report)
        self.assertIn("GRU RMSE `18.0617`", report)
        self.assertIn("pseudo-terminal validation rerun RMSE `18.2840`", report)
        self.assertIn("PHM score favors w80/cap150 by `408.20`", report)
        self.assertIn("AnchorPath path fusion is not admitted", report)
        self.assertIn("AnchorPath RMSE `18.6666`", report)
        self.assertIn("compatible published C-MAPSS RUL baselines", report)

        self.assertIn("## Verified External Source Snapshot", report)
        self.assertIn("FDDBenchmark", report)
        self.assertIn("10.7910/DVN/6C3JR1", report)
        self.assertIn("10.24432/C5CW21", report)
        self.assertIn("NASA Open Data", report)

        self.assertIn("## Baseline Alignment Decision Matrix", report)
        self.assertIn("Anomaly Transformer", report)
        self.assertIn("PatchTST", report)
        self.assertIn("TimesNet", report)
        self.assertIn("iTransformer", report)
        self.assertIn("not a direct anomaly/FDD protocol", report)

        self.assertIn("## Safe vs Unsafe Wording", report)
        self.assertIn("Safe wording", report)
        self.assertIn("Unsafe wording", report)
        self.assertIn("universal official SOTA", report)

        self.assertIn("## Reproduction Gate Checklist", report)
        self.assertIn("split", report)
        self.assertIn("preprocessing", report)
        self.assertIn("metric definition", report)
        self.assertIn("threshold tuning", report)
        self.assertIn("delay handling", report)

        self.assertIn("## Paper Integration", report)
        self.assertIn("experiments and limitations", report)
        self.assertIn("paper_final_tables.md", report)


if __name__ == "__main__":
    unittest.main()
