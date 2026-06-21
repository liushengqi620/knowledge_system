from __future__ import annotations

import unittest

from summarize_cmapss_results import _tail_guarded_ere_value


class SummarizeCmapssResultsTest(unittest.TestCase):
    def test_tail_guarded_ere_keeps_ere_when_candidate_is_not_plain_contextual(self) -> None:
        run = {
            "ere_reliability_routing": {"macro_f1": 0.82},
            "safe_benefit_stable_evidence_routing": {"macro_f1": 0.80},
            "ere_reliability_route": {
                "coverage_guard_status": "fallback_to_candidate",
                "coverage_guard_candidate_name": "unweighted_contextual_residual_correction",
            },
        }

        value, mode = _tail_guarded_ere_value(run)

        self.assertEqual(value, 0.82)
        self.assertEqual(mode, "ere")

    def test_tail_guarded_ere_falls_back_for_plain_contextual_weak_margin(self) -> None:
        run = {
            "ere_reliability_routing": {"macro_f1": 0.79},
            "safe_benefit_stable_evidence_routing": {"macro_f1": 0.80},
            "ere_reliability_route": {
                "coverage_guard_status": "fallback_to_candidate",
                "coverage_guard_reason": "weak_reliability_margin",
                "coverage_guard_candidate_name": "contextual_residual_correction",
            },
        }

        value, mode = _tail_guarded_ere_value(run)

        self.assertEqual(value, 0.80)
        self.assertEqual(mode, "safe_benefit")


if __name__ == "__main__":
    unittest.main()
