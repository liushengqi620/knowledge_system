from __future__ import annotations

import unittest

from aaai_readiness_audit import DatasetEvidence, classify_dataset, render_report


class AaaiReadinessAuditTest(unittest.TestCase):
    def test_high_score_without_strong_external_baselines_is_not_sota_ready(self) -> None:
        evidence = DatasetEvidence(
            dataset="TEP",
            task="22-class process fault diagnosis",
            main=0.9122,
            proposed=0.9549,
            delta=0.0427,
            strong_baselines=[],
            protocol_gap="needs matched GDN/Transformer/TCN baselines under the same strict split",
            evidence_role="primary mechanism benchmark",
        )

        audit = classify_dataset(evidence)

        self.assertEqual(audit["claim_level"], "method-evidence")
        self.assertIn("missing strong baselines", audit["missing_evidence"])
        self.assertIn("strict split", audit["missing_evidence"])
        self.assertNotIn("SOTA", audit["claim"])

    def test_positive_result_with_two_strong_baselines_is_sota_candidate(self) -> None:
        evidence = DatasetEvidence(
            dataset="Hydraulic",
            task="four-target state diagnosis",
            main=0.9773,
            proposed=0.9784,
            delta=0.0011,
            strong_baselines=["published_table", "reimplemented_tcn"],
            protocol_gap="",
            evidence_role="supporting industrial diagnosis benchmark",
        )

        audit = classify_dataset(evidence)

        self.assertEqual(audit["claim_level"], "sota-candidate")
        self.assertIn("candidate", audit["claim"])
        self.assertEqual(audit["missing_evidence"], "none")

    def test_negative_transfer_dataset_is_safety_evidence(self) -> None:
        evidence = DatasetEvidence(
            dataset="C-MAPSS",
            task="degradation-stage diagnosis",
            main=0.7972,
            proposed=0.8010,
            delta=0.0038,
            strong_baselines=[],
            protocol_gap="needs stronger degradation-stage baselines",
            evidence_role="negative-transfer safety benchmark",
        )

        audit = classify_dataset(evidence)

        self.assertEqual(audit["claim_level"], "safety-evidence")
        self.assertIn("non-degradation", audit["claim"])

    def test_original_rul_dataset_supports_lower_is_better_method_evidence(self) -> None:
        evidence = DatasetEvidence(
            dataset="C-MAPSS",
            task="original terminal RUL regression",
            main=20.7559,
            proposed=18.0617,
            delta=-2.6942,
            strong_baselines=["histgb", "gru"],
            protocol_gap="needs compatible published C-MAPSS RUL baselines; pseudo-terminal validation rerun RMSE 18.2840 and PHM score trade-off disclosed",
            evidence_role="original-task RUL transfer benchmark with cap/window repair, pseudo-terminal RMSE support, PHM score trade-off, and closed path fusion; lower metric is better",
        )

        audit = classify_dataset(evidence)

        self.assertEqual(audit["claim_level"], "method-evidence")
        self.assertIn("method contribution", audit["claim"])
        self.assertIn("pseudo-terminal validation rerun RMSE 18.2840", audit["missing_evidence"])

    def test_render_report_contains_next_actions(self) -> None:
        report = render_report(
            [
                DatasetEvidence(
                    dataset="SKAB",
                    task="binary anomaly detection",
                    main=0.8343,
                    proposed=0.8532,
                    delta=0.0189,
                    strong_baselines=["usad", "tranad"],
                    protocol_gap="official GDN/MTAD-GAT replication still missing",
                    evidence_role="LLM graph reliability benchmark",
                )
            ]
        )

        self.assertIn("# AAAI/SOTA Readiness Audit", report)
        self.assertIn("SKAB", report)
        self.assertIn("official GDN/MTAD-GAT", report)
        self.assertIn("Next Action", report)


if __name__ == "__main__":
    unittest.main()
