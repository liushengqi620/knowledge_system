from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_aaai_efficiency_audit import (
    build_efficiency_report,
    render_markdown,
    summarize_tep_sequence_file,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class SummarizeAaaiEfficiencyAuditTest(unittest.TestCase):
    def test_tep_sequence_file_marks_legacy_and_measured_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "legacy.json"
            measured = root / "measured.json"
            base_result = {
                "sample_multiclass_metrics": {"target_defect_macro_f1": 0.5},
                "train_diagnostics": {"device": "cuda"},
            }
            timed_result = {
                "sample_multiclass_metrics": {"target_defect_macro_f1": 0.6},
                "train_diagnostics": {
                    "device": "cuda",
                    "parameters": 123,
                    "train_seconds": 4.0,
                    "train_samples_per_second": 100.0,
                    "test_inference_seconds": 0.02,
                    "test_inference_samples_per_second": 5000.0,
                },
            }
            _write_json(legacy, {"records": [{"variant": "no_graph", "seed": 42, "result": base_result}]})
            _write_json(measured, {"records": [{"variant": "no_graph", "seed": 42, "result": timed_result}]})

            legacy_rows = summarize_tep_sequence_file(legacy, branch_prefix="Legacy", variants=("no_graph",))
            measured_rows = summarize_tep_sequence_file(measured, branch_prefix="Measured", variants=("no_graph",))

            self.assertEqual(legacy_rows[0]["status"], "needs_timed_rerun")
            self.assertEqual(measured_rows[0]["status"], "measured")
            self.assertEqual(measured_rows[0]["parameters_mean"], 123.0)
            self.assertEqual(measured_rows[0]["test_inference_samples_per_second_mean"], 5000.0)

    def test_public_efficiency_report_renders_missing_tep_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            formal = root / "runs"
            export = root / "exports"
            public_dir = formal / "skab_strong_anchor_w48_e40"
            _write_json(
                public_dir / "ms_gse_rpf_skab_anomaly_full_prior-none_seed42.json",
                {
                    "seed": 42,
                    "primary_test_metrics": {"macro_f1": 0.8},
                    "efficiency": {
                        "parameters": 10,
                        "train_seconds": 2.0,
                        "train_samples_per_second": 50.0,
                        "test_inference_seconds": 0.1,
                        "test_inference_samples_per_second": 1000.0,
                    },
                },
            )
            report = build_efficiency_report(formal_run_root=formal, export_dir=export)
            rendered = render_markdown(report)

            self.assertIn("AAAI Efficiency Audit", rendered)
            self.assertIn("SKAB", rendered)
            self.assertIn("measured", rendered)
            self.assertIn("missing", rendered)
            self.assertIn("TEP full-budget legacy rows", rendered)
            self.assertIn("--variants no_graph,residual_gated_lagged", rendered)
            self.assertIn("tep_gdn_20k_e10_timed.json", rendered)

    def test_full_timed_tep_runs_omit_smoke_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export = root / "exports"
            timed_result = {
                "sample_multiclass_metrics": {"target_defect_macro_f1": 0.6},
                "train_diagnostics": {
                    "device": "cuda",
                    "parameters": 123,
                    "train_seconds": 4.0,
                    "train_samples_per_second": 100.0,
                    "test_inference_seconds": 0.02,
                    "test_inference_samples_per_second": 5000.0,
                },
            }
            timed_records = [
                {"variant": "no_graph", "seed": 42, "result": timed_result},
                {"variant": "residual_gated_lagged", "seed": 42, "result": timed_result},
            ]
            _write_json(export / "tep_gdn_20k_e10_timed.json", {"records": timed_records})
            _write_json(export / "tep_mtad_20k_e10_timed.json", {"records": timed_records})
            _write_json(export / "tep_gdn_efficiency_smoke.json", {"records": timed_records})

            report = build_efficiency_report(formal_run_root=root / "runs", export_dir=export)
            rendered = render_markdown(report)

            branches = [row["branch"] for row in report["rows"]]
            self.assertIn("GDN20k:no_graph", branches)
            self.assertIn("MTADGAT20k:residual_gated_lagged", branches)
            self.assertNotIn("GDN600TimingSmoke:no_graph", branches)
            self.assertNotIn("GDN600TimingSmoke", rendered)
            self.assertIn("Smoke timing rows are omitted", rendered)


if __name__ == "__main__":
    unittest.main()
