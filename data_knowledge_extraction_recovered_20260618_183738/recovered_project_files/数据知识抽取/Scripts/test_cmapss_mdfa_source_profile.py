from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmapss_mdfa_source_profile import (
    build_cmapss_mdfa_source_profile,
    render_markdown,
    write_cmapss_mdfa_source_profile,
)


def _write_units(path: Path, n_units: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for unit in range(1, n_units + 1):
        rows.append(f"{unit} 1 0.0 0.0 100.0 1.0\n")
    path.write_text("".join(rows), encoding="utf-8")


def _write_rul(path: Path, n_units: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join("50\n" for _ in range(n_units)), encoding="utf-8")


class CmapssMdfaSourceProfileTest(unittest.TestCase):
    def test_profile_reconciles_raw_counts_against_mdfa_table_not_readme_typo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            readme = """
Data Set: FD001
Train trjectories: 100
Test trajectories: 100
Conditions: ONE
Fault Modes: ONE
Data Set: FD002
Train trjectories: 260
Test trajectories: 259
Conditions: SIX
Fault Modes: ONE
Data Set: FD003
Train trjectories: 100
Test trajectories: 100
Conditions: ONE
Fault Modes: TWO
Data Set: FD004
Train trjectories: 248
Test trajectories: 249
Conditions: SIX
Fault Modes: TWO
"""
            (raw_dir / "readme.txt").write_text(readme, encoding="utf-8")
            counts = {"FD001": (100, 100), "FD002": (260, 259), "FD003": (100, 100), "FD004": (249, 248)}
            for subset, (train_units, test_units) in counts.items():
                _write_units(raw_dir / f"train_{subset}.txt", train_units)
                _write_units(raw_dir / f"test_{subset}.txt", test_units)
                _write_rul(raw_dir / f"RUL_{subset}.txt", test_units)

            payload = build_cmapss_mdfa_source_profile(raw_dir)

            self.assertEqual("source_profile_count_reconciled_runner_pending", payload["status"])
            self.assertTrue(payload["gates"]["open_fulltext_protocol_available"])
            self.assertTrue(payload["gates"]["mdfa_piecewise_rul_cap_machine_readable"])
            self.assertTrue(payload["gates"]["mdfa_table4_key_sensors_machine_readable"])
            self.assertTrue(payload["gates"]["local_raw_files_present"])
            self.assertTrue(payload["gates"]["local_unit_counts_match_mdfa_table"])
            self.assertTrue(payload["gates"]["local_rul_rows_match_test_units"])
            self.assertFalse(payload["gates"]["readme_counts_match_local_files"])
            self.assertTrue(payload["gates"]["source_matched_runner_code_present"])
            self.assertFalse(payload["gates"]["full_source_matched_prediction_archive_present"])
            self.assertFalse(payload["gates"]["exact_test_label_policy_machine_readable"])
            self.assertFalse(payload["gates"]["safe_to_promote_mdfa_to_exact_reproduction"])
            self.assertIn("readme_counts_match_local_files", payload["missing_gates"])
            self.assertIn("full_source_matched_prediction_archive_present", payload["missing_gates"])
            key_sensors = {row["source_code"]: row["local_sensor"] for row in payload["table4_key_sensor_mapping"]}
            self.assertEqual("s11", key_sensors["Ps30"])
            self.assertEqual("s2", key_sensors["T24"])
            self.assertEqual("s21", key_sensors["W32"])
            self.assertEqual("FD004", payload["readme_count_inconsistencies"][0]["subset"])

            rows = {row["subset"]: row for row in payload["local_count_reconciliation"]}
            self.assertEqual(249, rows["FD004"]["local_train_units"])
            self.assertEqual(248, rows["FD004"]["local_test_units"])
            self.assertEqual(249, rows["FD004"]["mdfa_train_units"])
            self.assertEqual(248, rows["FD004"]["mdfa_test_units"])

    def test_writer_and_markdown_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            raw_dir = Path(tmp) / "raw"
            for subset, (train_units, test_units) in {
                "FD001": (100, 100),
                "FD002": (260, 259),
                "FD003": (100, 100),
                "FD004": (249, 248),
            }.items():
                _write_units(raw_dir / f"train_{subset}.txt", train_units)
                _write_units(raw_dir / f"test_{subset}.txt", test_units)
                _write_rul(raw_dir / f"RUL_{subset}.txt", test_units)
            (raw_dir / "readme.txt").write_text("", encoding="utf-8")

            written = write_cmapss_mdfa_source_profile(output_dir, raw_dir)
            self.assertEqual(
                {
                    output_dir / "cmapss_mdfa_source_profile.json",
                    output_dir / "cmapss_mdfa_source_profile.md",
                },
                set(written),
            )
            payload = json.loads((output_dir / "cmapss_mdfa_source_profile.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
            self.assertIn("C-MAPSS MDFA Source Profile", markdown)
            self.assertIn("window=30", markdown)
            self.assertIn("dilation rates 1, 2, 4", markdown)
            self.assertIn("Table 4 Key Sensor Mapping", markdown)
            self.assertIn("Ps30", markdown)
            self.assertIn("mdfa_key_sensors_pca", markdown)
            self.assertIn("test-label scoring policy", markdown)
            self.assertIn("safe_to_promote_mdfa_to_exact_reproduction", markdown)
            self.assertNotIn("official C-MAPSS SOTA is proven", markdown)


if __name__ == "__main__":
    unittest.main()
