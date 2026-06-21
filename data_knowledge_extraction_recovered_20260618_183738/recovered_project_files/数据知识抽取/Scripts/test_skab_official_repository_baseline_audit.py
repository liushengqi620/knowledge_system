from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skab_official_repository_baseline_audit import (
    build_skab_official_repository_baseline_audit,
    render_markdown,
    write_skab_official_repository_baseline_audit,
)


class SkabOfficialRepositoryBaselineAuditTest(unittest.TestCase):
    def test_official_precomputed_rows_recompute_readme_leaderboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_skab_official_repository_baseline_audit(output_dir=Path(tmp))

            self.assertEqual("official_skab_precomputed_baseline_audit_partial", payload["status"])
            gates = payload["gates"]
            self.assertTrue(gates["official_skab_repository_extracted"])
            self.assertTrue(gates["official_notebooks_present"])
            self.assertTrue(gates["official_core_modules_present"])
            self.assertTrue(gates["official_result_pickles_present"])
            self.assertTrue(gates["official_result_pickles_align_to_raw_data"])
            self.assertTrue(gates["official_outlier_leaderboard_recomputed"])
            self.assertTrue(gates["official_frozen_prediction_records_materialized"])
            self.assertFalse(gates["official_notebooks_rerun_from_source"])

            rows = {row["method"]: row for row in payload["method_rows"]}
            self.assertGreaterEqual(len(rows), 10)
            self.assertAlmostEqual(0.7838, rows["Conv_AE"]["metrics"]["f1"], places=4)
            self.assertAlmostEqual(13.55, rows["Conv_AE"]["metrics"]["far_percent"], places=2)
            self.assertAlmostEqual(28.02, rows["Conv_AE"]["metrics"]["mar_percent"], places=2)
            self.assertTrue(rows["Conv_AE"]["matches_expected_leaderboard"])
            self.assertTrue((Path(tmp) / rows["Conv_AE"]["record_file"]).exists())
            self.assertEqual(64, len(rows["Conv_AE"]["record_sha256"]))

    def test_markdown_and_writer_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_skab_official_repository_baseline_audit(output_dir)
            self.assertEqual(
                {output_dir / "skab_official_repository_baseline_audit.json", output_dir / "skab_official_repository_baseline_audit.md"},
                set(written),
            )
            payload = json.loads((output_dir / "skab_official_repository_baseline_audit.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
            self.assertIn("SKAB Official Repository Baseline Audit", markdown)
            self.assertIn("official_notebooks_rerun_from_source", markdown)
            self.assertIn("blocked", markdown)
            self.assertIn("Conv_AE", markdown)
            self.assertNotIn("official SOTA", markdown)


if __name__ == "__main__":
    unittest.main()
