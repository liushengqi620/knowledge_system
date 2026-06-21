from __future__ import annotations

import unittest

from skab_source_rerun_delta_audit import build_skab_source_rerun_delta_audit, render_markdown


class SkabSourceRerunDeltaAuditTest(unittest.TestCase):
    def test_delta_audit_attributes_unmatched_source_rows_to_prediction_variance(self) -> None:
        payload = build_skab_source_rerun_delta_audit()

        self.assertEqual("source_rerun_delta_profile_complete", payload["status"])
        self.assertEqual([], payload["missing_delta_methods"])
        self.assertTrue(payload["gates"]["source_rerun_audit_present"])
        self.assertTrue(payload["gates"]["unmatched_methods_covered"])
        self.assertTrue(payload["gates"]["records_present_for_all_methods"])
        self.assertTrue(payload["gates"]["record_sets_identical_for_unmatched_methods"])
        self.assertTrue(payload["gates"]["labels_identical_for_unmatched_methods"])
        self.assertTrue(payload["gates"]["deltas_attributed_to_predictions"])

        rows = {row["method"]: row for row in payload["rows"]}
        self.assertEqual({"LSTM_AE", "MSCRED", "Vanilla_LSTM"}, set(rows))
        for method, row in rows.items():
            self.assertEqual("prediction_delta_only", row["status"], method)
            self.assertTrue(row["record_set_identical"], method)
            self.assertTrue(row["y_true_identical_on_common"], method)
            self.assertEqual(0, row["repository_only_count"], method)
            self.assertEqual(0, row["source_only_count"], method)
            self.assertGreater(row["prediction_disagreement_count_on_common"], 0, method)
            self.assertIn("prediction differences", row["interpretation"])

        self.assertAlmostEqual(0.9092, rows["LSTM_AE"]["prediction_agreement_rate_on_common"], places=4)
        self.assertAlmostEqual(0.9749, rows["MSCRED"]["prediction_agreement_rate_on_common"], places=4)
        self.assertAlmostEqual(0.9485, rows["Vanilla_LSTM"]["prediction_agreement_rate_on_common"], places=4)

    def test_markdown_keeps_claim_boundary(self) -> None:
        markdown = render_markdown(build_skab_source_rerun_delta_audit())

        self.assertIn("# SKAB Source-Rerun Delta Audit", markdown)
        self.assertIn("source_rerun_delta_profile_complete", markdown)
        self.assertIn("prediction_delta_only", markdown)
        self.assertIn("does not convert unmatched source reruns into official leaderboard matches", markdown)


if __name__ == "__main__":
    unittest.main()
