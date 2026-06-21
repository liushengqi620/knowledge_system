from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmapss_published_baseline_contract import (
    build_cmapss_published_baseline_contract,
    render_markdown,
    write_cmapss_published_baseline_contract,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class CmapssPublishedBaselineContractTest(unittest.TestCase):
    def test_contract_tracks_local_lstm_but_keeps_exact_reproduction_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = root / "cmapss_native_preprocessing_manifest.json"
            alignment = root / "cmapss_published_baseline_alignment.json"
            _write(
                native,
                {
                    "gates": {
                        "native_fd001_fd004_split_present": True,
                        "terminal_test_unit_records_present": True,
                    }
                },
            )
            _write(
                alignment,
                {
                    "local_protocol_rows": [
                        {
                            "name": "lstm_sequence",
                            "n_seeds": 3,
                            "subsets": ["FD001", "FD002", "FD003", "FD004"],
                            "alignment_status": "published_style_seed_archive_not_exact_reproduction",
                        }
                    ]
                },
            )

            payload = build_cmapss_published_baseline_contract(alignment, native)

            self.assertEqual("contract_complete_reproduction_pending", payload["status"])
            self.assertTrue(payload["gates"]["native_data_contract_present"])
            self.assertTrue(payload["gates"]["local_published_style_lstm_archive_present"])
            self.assertFalse(payload["gates"]["exact_published_reproduction_complete"])
            self.assertFalse(payload["gates"]["matched_budget_complete"])
            self.assertIn("official_or_published_baseline_protocol_pass", payload["missing_gates"])
            rows = {row["id"]: row for row in payload["baseline_contracts"]}
            self.assertTrue(rows["lstm_rul_2017"]["local_seed_archives_present"])
            self.assertTrue(rows["lstm_rul_2017"]["local_scope_covers_required"])
            self.assertFalse(rows["lstm_rul_2017"]["exact_reproduction_ready"])
            self.assertIn("published-style", " ".join(rows["lstm_rul_2017"]["known_not_exact_reasons"]))
            self.assertIn("mdfa_2025", rows)
            self.assertFalse(rows["mdfa_2025"]["exact_reproduction_ready"])
            self.assertIn("local branch archives exist", " ".join(rows["mdfa_2025"]["known_not_exact_reasons"]))
            self.assertIn("Table-4 key-sensor PCA", " ".join(rows["mdfa_2025"]["known_not_exact_reasons"]))

    def test_markdown_and_writer_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_cmapss_published_baseline_contract(output_dir)
            self.assertEqual(
                {
                    output_dir / "cmapss_published_baseline_contract.json",
                    output_dir / "cmapss_published_baseline_contract.md",
                },
                set(written),
            )
            payload = json.loads((output_dir / "cmapss_published_baseline_contract.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
            self.assertIn("C-MAPSS Published Baseline Contract", markdown)
            self.assertIn("contract_complete_reproduction_pending", markdown)
            self.assertIn("lstm_rul_2017", markdown)
            self.assertIn("mdfa_2025", markdown)
            self.assertIn("cmapss_mdfa_source_profile", markdown)
            self.assertIn("exact_reproduction_status", json.dumps(payload))
            self.assertIn("Do not claim literature-wide RUL SOTA", markdown)
            self.assertNotIn("official leaderboard SOTA is proven", markdown)


if __name__ == "__main__":
    unittest.main()
