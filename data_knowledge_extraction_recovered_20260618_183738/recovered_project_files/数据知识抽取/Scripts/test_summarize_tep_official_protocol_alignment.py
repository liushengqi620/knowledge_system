from __future__ import annotations

import unittest

from summarize_tep_official_protocol_alignment import ProtocolEvidence, render_report


class SummarizeTepOfficialProtocolAlignmentTest(unittest.TestCase):
    def test_renders_protocol_boundary_with_matched_results_and_claim_limits(self) -> None:
        evidence = ProtocolEvidence.current()

        report = render_report(evidence)

        self.assertIn("Protocol-aligned claim boundary", report)
        self.assertIn("Strict 22-class", report)
        self.assertIn("0.9549 +/- 0.0023", report)
        self.assertIn("GDN20k-ResidualGatedLagged", report)
        self.assertIn("MTADGAT20k-ResidualGatedLagged", report)
        self.assertIn("not a direct leaderboard claim", report)
        self.assertIn("Do not compare directly", report)
        self.assertIn("external paper's exact split", report)


if __name__ == "__main__":
    unittest.main()
