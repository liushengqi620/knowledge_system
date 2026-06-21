from __future__ import annotations

import unittest

from cmapss_exact_native_gap_audit import build_cmapss_exact_native_gap_audit, render_markdown


class CmapssExactNativeGapAuditTest(unittest.TestCase):
    def test_gap_audit_separates_score_evidence_from_exact_protocol_blockers(self) -> None:
        payload = build_cmapss_exact_native_gap_audit()

        self.assertEqual("cmapss_exact_native_gap_protocol_budget_pending", payload["status"])
        self.assertEqual(
            ["official_or_published_baseline_protocol", "matched_budget"],
            payload["exact_gate_missing_gates"],
        )
        gates = payload["gates"]
        self.assertTrue(gates["native_exact_nonbaseline_fields_pass"])
        self.assertTrue(gates["published_contract_materialized"])
        self.assertTrue(gates["mdfa_open_source_profile_materialized"])
        self.assertTrue(gates["mdfa_local_full_branch_archive_present"])
        self.assertTrue(gates["mdfa_score_gap_quantified"])
        self.assertFalse(gates["exact_published_reproduction_complete"])
        self.assertFalse(gates["matched_budget_complete"])
        self.assertFalse(gates["mdfa_exact_source_policy_verified"])
        self.assertFalse(gates["official_sota_admissible"])

        requirements = {row["requirement"]: row for row in payload["requirement_rows"]}
        self.assertEqual("pass", requirements["native C-MAPSS task/split/preprocessing/metric"]["status"])
        self.assertEqual("partial", requirements["MDFA local four-subset archive"]["status"])
        self.assertEqual("blocked", requirements["matched training budget"]["status"])

        subsets = {row["subset"]: row for row in payload["mdfa_subset_gaps"]}
        self.assertGreater(subsets["FD001"]["gap_current_minus_reference"], 0.0)
        self.assertGreater(subsets["FD003"]["gap_current_minus_reference"], 0.0)
        self.assertLess(subsets["FD002"]["gap_current_minus_reference"], 0.0)
        self.assertLess(subsets["FD004"]["gap_current_minus_reference"], 0.0)

    def test_mdfa_external_source_resolution_identifies_unresolved_fields(self) -> None:
        payload = build_cmapss_exact_native_gap_audit()
        resolution = {row["field"]: row for row in payload["mdfa_external_source_resolution"]}

        self.assertEqual("machine_readable", resolution["training hyperparameters"]["status"])
        self.assertEqual("machine_readable", resolution["MDFA architecture"]["status"])
        self.assertEqual("machine_readable", resolution["key sensors"]["status"])
        self.assertEqual(
            "not_machine_readable",
            resolution["PCA threshold or per-subset component count"]["status"],
        )
        self.assertEqual(
            "not_available_from_article_page",
            resolution["source code or supplementary reproduction package"]["status"],
        )
        self.assertIn("https://www.mdpi.com/2076-3417/15/17/9813", resolution["training hyperparameters"]["source"])

    def test_markdown_is_claim_safe(self) -> None:
        markdown = render_markdown(build_cmapss_exact_native_gap_audit())

        self.assertIn("# C-MAPSS Exact-Native Gap Audit", markdown)
        self.assertIn("official_or_published_baseline_protocol, matched_budget", markdown)
        self.assertIn("MDFA local four-subset archive", markdown)
        self.assertIn("## MDFA External Source Resolution", markdown)
        self.assertIn("PCA threshold or per-subset component count", markdown)
        self.assertIn("source code or supplementary reproduction package", markdown)
        self.assertIn("https://www.mdpi.com/2076-3417/15/17/9813", markdown)
        self.assertIn("not exact MDFA reproduction", markdown)
        self.assertIn("does not authorize official or literature-wide SOTA wording", markdown)


if __name__ == "__main__":
    unittest.main()
