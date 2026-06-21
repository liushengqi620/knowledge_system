from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skab_official_baseline_gate import (
    build_skab_official_baseline_gate,
    render_markdown,
    write_skab_official_baseline_gate,
)


class SkabOfficialBaselineGateTest(unittest.TestCase):
    def test_gate_separates_fair_records_from_official_reproduction(self) -> None:
        payload = build_skab_official_baseline_gate()

        self.assertEqual("skab_official_baseline_gate_not_closed", payload["status"])
        gates = payload["gates"]
        self.assertTrue(gates["style_baseline_frozen_records_present"])
        self.assertTrue(gates["official_repo_provenance_present"])
        self.assertTrue(gates["anomaly_transformer_official_source_adapter_present"])
        self.assertTrue(gates["anomaly_transformer_official_source_wrapper_present"])
        self.assertTrue(gates["official_source_wrapper_frozen_prediction_records_present"])
        self.assertTrue(gates["skab_official_repository_artifacts_present"])
        self.assertTrue(gates["skab_official_precomputed_outlier_baselines_recomputed"])
        self.assertTrue(gates["skab_official_partial_source_rerun_evidence_present"])
        self.assertFalse(gates["skab_official_repository_notebook_baselines_reproduced"])
        self.assertFalse(gates["safe_to_flip_skab_official_baseline_gate"])

        methods = {row["method"]: row for row in payload["style_baseline_rows"]}
        self.assertEqual({"usad", "tranad"}, set(methods))
        self.assertEqual(3, methods["usad"]["n_seeds"])
        self.assertEqual(3, methods["tranad"]["frozen_prediction_seed_count"])

        official = payload["official_source_rows"][0]
        self.assertEqual("anomaly_transformer_official_source_wrapper", official["method"])
        self.assertTrue(official["official_source_used"])
        self.assertFalse(official["official_external_score"])
        self.assertTrue(official["frozen_prediction_records_present"])
        self.assertIn("not an official", official["claim_boundary"])

        repository_rows = {row["method"]: row for row in payload["official_repository_precomputed_rows"]}
        self.assertIn("Conv_AE", repository_rows)
        self.assertAlmostEqual(0.7838, repository_rows["Conv_AE"]["f1"], places=4)
        self.assertTrue(repository_rows["Conv_AE"]["matches_expected_leaderboard"])
        self.assertIn("notebook/source rerun", repository_rows["Conv_AE"]["claim_boundary"])

        source_rows = {row["method"]: row for row in payload["official_source_rerun_rows"]}
        self.assertTrue({"T2", "T2-q"}.issubset(set(source_rows)))
        self.assertAlmostEqual(0.7581, source_rows["T2-q"]["f1"], places=4)
        self.assertTrue(source_rows["T2-q"]["matches_expected_leaderboard"])
        if "Conv_AE" in source_rows:
            self.assertAlmostEqual(0.7842, source_rows["Conv_AE"]["f1"], places=4)
            self.assertTrue(source_rows["Conv_AE"]["matches_expected_leaderboard"])
        if "Vanilla_AE" in source_rows:
            self.assertAlmostEqual(0.3938, source_rows["Vanilla_AE"]["f1"], places=4)
            self.assertTrue(source_rows["Vanilla_AE"]["matches_expected_leaderboard"])
        if "LSTM_AE" in source_rows:
            self.assertAlmostEqual(0.7515, source_rows["LSTM_AE"]["f1"], places=4)
            self.assertFalse(source_rows["LSTM_AE"]["matches_expected_leaderboard"])
        if "MSCRED" in source_rows:
            self.assertAlmostEqual(0.3382, source_rows["MSCRED"]["f1"], places=4)
            self.assertFalse(source_rows["MSCRED"]["matches_expected_leaderboard"])
        if "Vanilla_LSTM" in source_rows:
            self.assertAlmostEqual(0.5111, source_rows["Vanilla_LSTM"]["f1"], places=4)
            self.assertFalse(source_rows["Vanilla_LSTM"]["matches_expected_leaderboard"])
        self.assertIn("full official leaderboard", source_rows["T2-q"]["claim_boundary"])
        self.assertIn("official_notebooks_rerun_from_source", payload["official_source_rerun_blockers"])
        delta_audit = payload["official_source_rerun_delta_audit"]
        if delta_audit.get("explained"):
            self.assertNotIn("source_rerun_leaderboard_deltas_explained", payload["official_source_rerun_blockers"])
            self.assertEqual("source_rerun_delta_profile_complete", delta_audit["status"])
        if "MSCRED" in source_rows:
            self.assertIn("MSCRED", payload["official_source_rerun_unmatched_methods"])

    def test_markdown_and_writer_are_claim_safe(self) -> None:
        payload = build_skab_official_baseline_gate()
        markdown = render_markdown(payload)

        self.assertIn("# SKAB Official Baseline Gate", markdown)
        self.assertIn("skab_official_baseline_gate_not_closed", markdown)
        self.assertIn("official_source_wrapper_frozen_prediction_records_present", markdown)
        self.assertIn("skab_official_precomputed_outlier_baselines_recomputed", markdown)
        self.assertIn("skab_official_partial_source_rerun_evidence_present", markdown)
        self.assertIn("skab_official_repository_notebook_baselines_reproduced", markdown)
        self.assertIn("official-source Anomaly Transformer wrapper", markdown)
        self.assertIn("Official Repository Precomputed Rows", markdown)
        self.assertIn("Official Notebook/Core Source Rerun Rows", markdown)
        self.assertIn("Source rerun delta audit", markdown)
        self.assertIn("T2-q", markdown)
        self.assertIn("Conv_AE", markdown)
        self.assertNotIn("SOTA-candidate", markdown)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_skab_official_baseline_gate(output_dir)
            self.assertEqual(
                {output_dir / "skab_official_baseline_gate.json", output_dir / "skab_official_baseline_gate.md"},
                set(written),
            )
            saved = json.loads((output_dir / "skab_official_baseline_gate.json").read_text(encoding="utf-8"))
            self.assertEqual("skab_official_baseline_gate_not_closed", saved["status"])


if __name__ == "__main__":
    unittest.main()
