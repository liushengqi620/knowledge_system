from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skab_native_metric_audit import build_skab_native_metric_audit, render_markdown, write_skab_native_metric_audit


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class SkabNativeMetricAuditTest(unittest.TestCase):
    def test_audit_keeps_formal_model_partial_without_frozen_predictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            formal = root / "skab_strong_anchor_w48_e40"
            _write(
                formal / "ms_gse_rpf_skab_anomaly_full_prior-none_seed42.json",
                {
                    "dataset": "skab",
                    "target": "anomaly",
                    "seed": 42,
                    "test_size": 100,
                    "positive_threshold": 0.48,
                    "primary_test_metrics": {"macro_f1": 0.8, "positive_f1": 0.7},
                    "thresholded_test_metrics": {"macro_f1": 0.82, "positive_f1": 0.72},
                },
            )
            external = root / "external.json"
            _write(
                external,
                {
                    "baseline": "official_source_adapter",
                    "runs": [
                        {
                            "seed": 42,
                            "matched_row_level": {
                                "metrics": {"macro_f1": 0.51},
                                "protocol": {
                                    "binary": {
                                        "f1": 0.36,
                                        "far_percent": 50.0,
                                        "mar_percent": 40.0,
                                    },
                                    "point_adjusted": {"f1": 1.0},
                                    "right_window_changepoint": {"window_steps": 60},
                                },
                                "threshold": {"threshold": 0.1},
                            },
                        }
                    ],
                },
            )

            payload = build_skab_native_metric_audit([formal], [external])

            self.assertEqual("native_metric_audit_partial", payload["status"])
            self.assertFalse(payload["gates"]["proposed_frozen_prediction_archive"])
            self.assertFalse(payload["gates"]["proposed_changepoint_event_window_scored"])
            self.assertTrue(payload["gates"]["external_protocol_controls_present"])
            self.assertIn("proposed_frozen_prediction_archive", payload["missing_gates"])

    def test_audit_recomputes_point_metrics_from_formal_prediction_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            formal = root / "skab_strong_anchor_w48_e40"
            _write(
                formal / "ms_gse_rpf_skab_anomaly_full_prior-none_seed42.json",
                {
                    "dataset": "skab",
                    "target": "anomaly",
                    "seed": 42,
                    "test_size": 4,
                    "positive_threshold": 0.50,
                    "primary_test_metrics": {"macro_f1": 0.0, "positive_f1": 0.0},
                    "classification_prediction_records": [
                        {"y_true_original": 0, "y_pred_original": 0, "run_id": "a", "changepoint": 0},
                        {"y_true_original": 0, "y_pred_original": 1, "run_id": "a", "changepoint": 0},
                        {"y_true_original": 1, "y_pred_original": 1, "run_id": "b", "changepoint": 1},
                        {"y_true_original": 1, "y_pred_original": 0, "run_id": "b", "changepoint": 0},
                    ],
                },
            )

            payload = build_skab_native_metric_audit([formal], [])

            self.assertEqual("native_metric_audit_partial", payload["status"])
            self.assertTrue(payload["gates"]["proposed_frozen_prediction_archive"])
            self.assertTrue(payload["gates"]["proposed_point_metrics_recomputable"])
            self.assertTrue(payload["gates"]["proposed_changepoint_event_window_scored"])
            row = payload["branch_summary"][0]
            self.assertAlmostEqual(float(row["far_percent_mean"]), 50.0)
            self.assertAlmostEqual(float(row["mar_percent_mean"]), 50.0)
            self.assertAlmostEqual(float(row["changepoint_event_recall_mean"]), 1.0)

    def test_algorithmic_only_can_be_selected_as_native_audited_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            strong = root / "skab_strong_anchor_w48_e40"
            algorithmic = root / "a0_algorithmic_only"
            base_payload = {
                "dataset": "skab",
                "target": "anomaly",
                "test_size": 4,
                "positive_threshold": 0.50,
                "classification_prediction_records": [
                    {"y_true_original": 0, "y_pred_original": 0, "run_id": "a", "row_index": 0, "changepoint": 0},
                    {"y_true_original": 0, "y_pred_original": 1, "run_id": "a", "row_index": 1, "changepoint": 0},
                    {"y_true_original": 1, "y_pred_original": 1, "run_id": "b", "row_index": 2, "changepoint": 1},
                    {"y_true_original": 1, "y_pred_original": 0, "run_id": "b", "row_index": 3, "changepoint": 0},
                ],
            }
            _write(strong / "ms_gse_rpf_skab_anomaly_full_prior-none_seed42.json", {**base_payload, "seed": 42})
            _write(
                algorithmic / "ms_gse_rpf_skab_anomaly_full_prior-alg-edge_pool_s0p05_seed42.json",
                {
                    **base_payload,
                    "seed": 42,
                    "classification_prediction_records": [
                        {"y_true_original": 0, "y_pred_original": 0, "run_id": "a", "row_index": 0, "changepoint": 0},
                        {"y_true_original": 0, "y_pred_original": 0, "run_id": "a", "row_index": 1, "changepoint": 0},
                        {"y_true_original": 1, "y_pred_original": 1, "run_id": "b", "row_index": 2, "changepoint": 1},
                        {"y_true_original": 1, "y_pred_original": 1, "run_id": "b", "row_index": 3, "changepoint": 0},
                    ],
                },
            )

            payload = build_skab_native_metric_audit([strong, algorithmic], [])

            self.assertEqual("a0_algorithmic_only", payload["decision"]["current_native_audited_branch"])
            self.assertFalse(payload["decision"]["llm_condition_deployed_as_accuracy_branch"])
            self.assertIn("algorithmic-only branch", payload["decision"]["rationale"])
            self.assertTrue(payload["gates"]["proposed_frozen_prediction_archive"])

    def test_audit_recomputes_external_baseline_metrics_from_prediction_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            external = root / "external.json"
            _write(
                external,
                {
                    "runs": [
                        {
                            "seed": 42,
                            "usad": {
                                "metrics": {"macro_f1": 0.0},
                                "protocol": {
                                    "binary": {"f1": 0.0, "far_percent": 0.0, "mar_percent": 0.0},
                                    "right_window_changepoint": {"window_steps": 60},
                                },
                                "threshold_tuning": {"threshold": 0.5},
                                "prediction_records": [
                                    {"y_true_original": 0, "y_pred_original": 0, "run_id": "r1", "row_index": 0, "changepoint": 0},
                                    {"y_true_original": 0, "y_pred_original": 1, "run_id": "r1", "row_index": 1, "changepoint": 0},
                                    {"y_true_original": 1, "y_pred_original": 1, "run_id": "r2", "row_index": 2, "changepoint": 1},
                                    {"y_true_original": 1, "y_pred_original": 0, "run_id": "r2", "row_index": 3, "changepoint": 0},
                                ],
                            },
                        }
                    ]
                },
            )

            payload = build_skab_native_metric_audit([], [external])

            summary = {row["branch"]: row for row in payload["branch_summary"]}
            self.assertIn("usad", summary)
            self.assertTrue(summary["usad"]["has_frozen_prediction_archive"])
            self.assertTrue(summary["usad"]["has_changepoint_event_window"])
            self.assertAlmostEqual(float(summary["usad"]["far_percent_mean"]), 50.0)
            self.assertAlmostEqual(float(summary["usad"]["mar_percent_mean"]), 50.0)
            self.assertAlmostEqual(float(summary["usad"]["changepoint_event_recall_mean"]), 1.0)

    def test_markdown_and_write_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            written = write_skab_native_metric_audit(output)

            self.assertEqual({output / "skab_native_metric_audit.json", output / "skab_native_metric_audit.md"}, set(written))
            payload = json.loads((output / "skab_native_metric_audit.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
            self.assertIn("SKAB Native Metric Audit", markdown)
            self.assertIn("not an official leaderboard result", markdown)
            self.assertNotIn("SOTA-candidate", markdown)


if __name__ == "__main__":
    unittest.main()
