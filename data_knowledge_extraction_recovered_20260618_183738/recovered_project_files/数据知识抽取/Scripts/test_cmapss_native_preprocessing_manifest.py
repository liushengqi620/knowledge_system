from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmapss_native_preprocessing_manifest import (
    build_cmapss_native_preprocessing_manifest,
    render_markdown,
    write_cmapss_native_preprocessing_manifest,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _records() -> list[dict]:
    records = []
    for subset in ("FD001", "FD002", "FD003", "FD004"):
        records.append(
            {
                "record_id": f"{subset}_test_001_0010",
                "subset": subset,
                "split_role": "test",
                "unit": 1,
                "cycle": 10,
                "rul_true": 100.0,
                "rul_pred": 98.0,
            }
        )
    return records


class CmapssNativePreprocessingManifestTest(unittest.TestCase):
    def test_manifest_verifies_native_rul_records_but_keeps_baseline_gate_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            baseline_root = Path(tmp) / "baselines"
            _write(
                run_root / "cmapss_rul_anchorpath_bigru_cls020_w80_e20" / "ms_gse_rpf_cmapss_rul_full_prior-none_seed42.json",
                {
                    "dataset": "cmapss",
                    "target": "rul",
                    "seed": 42,
                    "protocol": "ready_csv_causal_windows_same_backbone",
                    "split_protocol": "FD001-FD004_train_test",
                    "rul_eval_protocol": "terminal_test_unit",
                    "window_size": 80,
                    "diagnostics": {"health_rul_cap": 125.0},
                    "regime_prototype": {"enabled": True},
                    "primary_test_metrics": {"rul_rmse": 12.0, "rul_mae": 8.0, "rul_score": 100.0},
                    "rul_prediction_records": _records(),
                    "rul_subset_metrics": {
                        "enabled": True,
                        "rows": [{"subset": subset, "rul_rmse": 12.0, "rul_score": 25.0} for subset in ("FD001", "FD002", "FD003", "FD004")],
                    },
                },
            )

            payload = build_cmapss_native_preprocessing_manifest(run_root, baseline_root, Path(tmp) / "missing_alignment.json")

            self.assertEqual("native_preprocessing_manifest_partial", payload["status"])
            self.assertTrue(payload["gates"]["native_fd001_fd004_split_present"])
            self.assertTrue(payload["gates"]["terminal_test_unit_records_present"])
            self.assertTrue(payload["gates"]["rul_cap_declared"])
            self.assertFalse(payload["gates"]["published_baseline_alignment_present"])
            self.assertIn("published_baseline_alignment_present", payload["missing_gates"])

    def test_manifest_accepts_materialized_alignment_artifact_without_sota_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            baseline_root = Path(tmp) / "baselines"
            alignment = Path(tmp) / "cmapss_published_baseline_alignment.json"
            _write(
                run_root / "cmapss_rul_anchorpath_bigru_cls020_w80_e20" / "ms_gse_rpf_cmapss_rul_full_prior-none_seed42.json",
                {
                    "dataset": "cmapss",
                    "target": "rul",
                    "seed": 42,
                    "protocol": "ready_csv_causal_windows_same_backbone",
                    "split_protocol": "FD001-FD004_train_test",
                    "rul_eval_protocol": "terminal_test_unit",
                    "window_size": 80,
                    "diagnostics": {"health_rul_cap": 125.0},
                    "regime_prototype": {"enabled": True},
                    "primary_test_metrics": {"rul_rmse": 12.0, "rul_mae": 8.0, "rul_score": 100.0},
                    "rul_prediction_records": _records(),
                    "rul_subset_metrics": {
                        "enabled": True,
                        "rows": [{"subset": subset, "rul_rmse": 12.0, "rul_score": 25.0} for subset in ("FD001", "FD002", "FD003", "FD004")],
                    },
                },
            )
            _write(
                alignment,
                {
                    "gates": {
                        "alignment_artifact_present": True,
                        "published_reproduction_seed_artifacts_present": False,
                        "matched_budget_present": False,
                    },
                    "published_reference_registry": [{"id": "lstm_rul_2017"}],
                },
            )

            payload = build_cmapss_native_preprocessing_manifest(run_root, baseline_root, alignment)

            self.assertEqual("native_preprocessing_manifest_complete", payload["status"])
            self.assertTrue(payload["gates"]["published_baseline_alignment_present"])
            self.assertNotIn("published_baseline_alignment_present", payload["missing_gates"])
            self.assertIn("matched budget", payload["claim_boundary"])

    def test_markdown_and_write_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            written = write_cmapss_native_preprocessing_manifest(output)

            self.assertEqual(
                {output / "cmapss_native_preprocessing_manifest.json", output / "cmapss_native_preprocessing_manifest.md"},
                set(written),
            )
            payload = json.loads((output / "cmapss_native_preprocessing_manifest.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
            self.assertIn("C-MAPSS Native Preprocessing Manifest", markdown)
            self.assertIn("literature-wide SOTA wording", markdown)
            self.assertNotIn("SOTA-candidate", markdown)


if __name__ == "__main__":
    unittest.main()
