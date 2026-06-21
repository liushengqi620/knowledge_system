from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmapss_published_baseline_alignment import (
    build_cmapss_published_baseline_alignment,
    render_markdown,
    write_cmapss_published_baseline_alignment,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class CmapssPublishedBaselineAlignmentTest(unittest.TestCase):
    def test_alignment_materializes_local_controls_but_blocks_sota(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native_manifest = root / "cmapss_native_preprocessing_manifest.json"
            matched = root / "cmapss_rul_matched_baselines_summary.json"
            _write(
                native_manifest,
                {
                    "status": "native_preprocessing_manifest_partial",
                    "gates": {
                        "native_fd001_fd004_split_present": True,
                        "terminal_test_unit_records_present": True,
                        "subset_rmse_score_present": True,
                    },
                    "branch_summary": [
                        {
                            "branch": "cmapss_rul_anchorpath_bigru_cls020_w80_e20",
                            "n_seeds": 3,
                            "rul_cap_values": [125.0],
                            "window_sizes": [80],
                            "subsets": ["FD001", "FD002", "FD003", "FD004"],
                            "rmse_mean": 20.4,
                            "score_mean": 7000.0,
                        }
                    ],
                },
            )
            _write(
                matched,
                {
                    "overall": [{"baseline": "gru_sequence", "n_seeds": 3, "rmse_mean": 20.7, "score_mean": 7500.0}],
                    "subset_summary": [{"baseline": "gru_sequence", "subset": subset} for subset in ("FD001", "FD002", "FD003", "FD004")],
                },
            )

            published_style = root / "lstm_candidate_summary.json"
            _write(
                published_style,
                {
                    "overall": [{"baseline": "lstm_sequence", "n_seeds": 3, "rmse_mean": 21.6, "score_mean": 9900.0}],
                    "subset_summary": [{"baseline": "lstm_sequence", "subset": subset} for subset in ("FD001", "FD002", "FD003", "FD004")],
                },
            )

            payload = build_cmapss_published_baseline_alignment(native_manifest, matched, [published_style])

            self.assertEqual("published_baseline_alignment_partial_not_sota_proof", payload["status"])
            self.assertTrue(payload["gates"]["alignment_artifact_present"])
            self.assertTrue(payload["gates"]["local_fd001_fd004_seed_archive_present"])
            self.assertTrue(payload["gates"]["local_matched_baseline_protocol_present"])
            self.assertTrue(payload["gates"]["published_style_candidate_seed_archive_present"])
            self.assertFalse(payload["gates"]["published_reproduction_seed_artifacts_present"])
            self.assertFalse(payload["gates"]["matched_budget_present"])
            self.assertIn("literature_wide_sota_admissible", payload["missing_gates"])
            self.assertIn("reference_only_not_reproduced", json.dumps(payload["published_reference_registry"]))
            self.assertIn("published_style_seed_archive_not_exact_reproduction", json.dumps(payload["local_protocol_rows"]))

    def test_markdown_and_write_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            written = write_cmapss_published_baseline_alignment(output)

            self.assertEqual(
                {output / "cmapss_published_baseline_alignment.json", output / "cmapss_published_baseline_alignment.md"},
                set(written),
            )
            payload = json.loads((output / "cmapss_published_baseline_alignment.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
            self.assertIn("C-MAPSS Published Baseline Alignment", markdown)
            self.assertIn("local matched", markdown.lower())
            self.assertIn("reference_only_not_reproduced", markdown)
            self.assertIn("not_published_reproduction", markdown)
            self.assertNotIn("official universal leaderboard superiority", markdown)


if __name__ == "__main__":
    unittest.main()
