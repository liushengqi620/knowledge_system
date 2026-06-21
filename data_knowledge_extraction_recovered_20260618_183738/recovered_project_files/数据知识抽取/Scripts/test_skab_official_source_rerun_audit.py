from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skab_official_source_rerun_audit import (
    build_skab_official_source_rerun_audit,
    render_markdown,
    write_skab_official_source_rerun_audit,
)


class SkabOfficialSourceRerunAuditTest(unittest.TestCase):
    def test_t2_family_source_rerun_recomputes_official_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_skab_official_source_rerun_audit(output_dir=Path(tmp))

            self.assertEqual("official_skab_source_rerun_audit_partial", payload["status"])
            gates = payload["gates"]
            self.assertTrue(gates["official_skab_repository_extracted"])
            self.assertTrue(gates["official_notebook_sources_present"])
            self.assertTrue(gates["official_core_sources_present"])
            self.assertTrue(gates["source_rerun_t2_family_recomputed"])
            self.assertTrue(gates["source_rerun_frozen_records_materialized"])
            self.assertEqual(
                bool(payload["python_status"]["compatible"]),
                gates["current_python_matches_official_constraint"],
            )
            self.assertFalse(gates["official_notebooks_rerun_from_source"])

            rows = {row["method"]: row for row in payload["source_rerun_rows"]}
            self.assertTrue({"T2", "T2-q"}.issubset(set(rows)))
            self.assertAlmostEqual(0.6598, rows["T2"]["metrics"]["f1"], places=4)
            self.assertAlmostEqual(19.21, rows["T2"]["metrics"]["far_percent"], places=2)
            self.assertAlmostEqual(42.60, rows["T2"]["metrics"]["mar_percent"], places=2)
            self.assertAlmostEqual(0.7581, rows["T2-q"]["metrics"]["f1"], places=4)
            self.assertTrue(rows["T2"]["matches_expected_leaderboard"])
            self.assertTrue(rows["T2-q"]["matches_expected_leaderboard"])
            self.assertTrue((Path(tmp) / rows["T2"]["record_file"]).exists())
            self.assertEqual(64, len(rows["T2"]["record_sha256"]))
            if "Isolation_Forest" in rows:
                self.assertAlmostEqual(0.2868, rows["Isolation_Forest"]["metrics"]["f1"], places=4)
                self.assertTrue(rows["Isolation_Forest"]["matches_expected_leaderboard"])
            if "MSET" in rows:
                self.assertAlmostEqual(0.7800, rows["MSET"]["metrics"]["f1"], places=4)
                self.assertTrue(rows["MSET"]["matches_expected_leaderboard"])
            if "Vanilla_AE" in rows:
                self.assertAlmostEqual(0.3938, rows["Vanilla_AE"]["metrics"]["f1"], places=4)
                self.assertTrue(rows["Vanilla_AE"]["matches_expected_leaderboard"])
            if "Conv_AE" in rows:
                self.assertAlmostEqual(0.7842, rows["Conv_AE"]["metrics"]["f1"], places=4)
                self.assertTrue(rows["Conv_AE"]["matches_expected_leaderboard"])
            if "LSTM_AE" in rows:
                self.assertAlmostEqual(0.7515, rows["LSTM_AE"]["metrics"]["f1"], places=4)
                self.assertFalse(rows["LSTM_AE"]["matches_expected_leaderboard"])
                self.assertLessEqual(rows["LSTM_AE"]["claim_boundary"].count("Preserved from a prior pinned"), 1)
            if "MSCRED" in rows:
                self.assertAlmostEqual(0.3382, rows["MSCRED"]["metrics"]["f1"], places=4)
                self.assertFalse(rows["MSCRED"]["matches_expected_leaderboard"])
                self.assertIn("compatibility", rows["MSCRED"]["claim_boundary"].lower())
            if "Vanilla_LSTM" in rows:
                self.assertAlmostEqual(0.5111, rows["Vanilla_LSTM"]["metrics"]["f1"], places=4)
                self.assertFalse(rows["Vanilla_LSTM"]["matches_expected_leaderboard"])
                self.assertLessEqual(rows["Vanilla_LSTM"]["claim_boundary"].count("Preserved from a prior pinned"), 1)

            dependency = {row["method"]: row for row in payload["dependency_rows"]}
            if not gates["tensorflow_available_for_deep_official_notebooks"]:
                self.assertIn("tensorflow", dependency["Conv_AE"]["missing_dependencies"])
            self.assertIn("arimafd", dependency["Arima_anomaly_detection"]["missing_dependencies"])

    def test_markdown_and_writer_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_skab_official_source_rerun_audit(output_dir)
            self.assertEqual(
                {output_dir / "skab_official_source_rerun_audit.json", output_dir / "skab_official_source_rerun_audit.md"},
                set(written),
            )
            payload = json.loads((output_dir / "skab_official_source_rerun_audit.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)

            self.assertIn("SKAB Official Source Rerun Audit", markdown)
            self.assertIn("T2-q", markdown)
            if any(row["method"] == "LSTM_AE" for row in payload["source_rerun_rows"]):
                self.assertIn("LSTM_AE", markdown)
            if any(row["method"] == "MSCRED" for row in payload["source_rerun_rows"]):
                self.assertIn("Unmatched Source Rerun Rows", markdown)
                self.assertIn("MSCRED", markdown)
            self.assertIn("Source-Rerun Delta Audit", markdown)
            self.assertIn("source_rerun_t2_family_recomputed", markdown)
            self.assertIn("tensorflow", markdown)
            self.assertIn("partial source-rerun evidence", markdown)
            self.assertNotIn("official SOTA", markdown)


if __name__ == "__main__":
    unittest.main()
