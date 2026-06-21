from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from run_anomaly_transformer_skab_official_wrapper import (
    _aggregate_rows,
    _build_prediction_records,
    _classification_metrics,
    _summarize_skab_protocol_from_predictions,
    _tune_threshold,
)


class RunAnomalyTransformerSkabOfficialWrapperTest(unittest.TestCase):
    def test_row_aggregation_and_validation_threshold_are_finite(self) -> None:
        scores = np.asarray([[0.1, 0.2, 0.9], [0.4, 0.8, 0.3]], dtype=np.float64)
        indices = np.asarray([[0, 1, 2], [1, 2, 3]], dtype=np.int64)
        row_scores = _aggregate_rows(scores, indices, 4, method="max")

        self.assertTrue(np.all(np.isfinite(row_scores)))
        self.assertEqual(row_scores.tolist(), [0.1, 0.4, 0.9, 0.3])

        labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
        threshold = _tune_threshold(labels, row_scores)
        metrics = _classification_metrics(labels, row_scores, threshold["threshold"])

        self.assertIn("threshold", threshold)
        self.assertGreaterEqual(metrics["binary_f1"], 0.0)
        self.assertLessEqual(metrics["binary_f1"], 1.0)

    def test_prediction_records_are_native_audit_ready(self) -> None:
        labels = np.asarray([0, 1, 0], dtype=np.int64)
        scores = np.asarray([0.1, 0.8, 0.3], dtype=np.float64)
        threshold = {"threshold": 0.25, "scale": 0.1}
        meta = pd.DataFrame(
            [
                {"run_id": "run_a", "sample_index": 0, "run_group": "normal", "anomaly": 0, "changepoint": 0},
                {"run_id": "run_a", "sample_index": 1, "run_group": "normal", "anomaly": 1, "changepoint": 1},
                {"run_id": "run_b", "sample_index": 0, "run_group": "fault", "anomaly": 0, "changepoint": 0},
            ]
        )

        records = _build_prediction_records(labels=labels, scores=scores, threshold_info=threshold, meta=meta)

        self.assertEqual(3, len(records))
        self.assertEqual(0, records[0]["y_true_original"])
        self.assertEqual(0, records[0]["y_pred_original"])
        self.assertEqual(1, records[1]["y_pred_original"])
        self.assertEqual("run_a", records[1]["run_id"])
        self.assertEqual(1, records[1]["changepoint"])
        self.assertIn("proba", records[0])
        self.assertAlmostEqual(0.25, records[0]["anomaly_score_threshold"])
        self.assertGreater(records[0]["positive_threshold"], 0.5)

        protocol = _summarize_skab_protocol_from_predictions(
            labels,
            np.asarray([record["y_pred_original"] for record in records], dtype=np.int64),
            meta,
        )
        self.assertAlmostEqual(50.0, protocol["binary"]["far_percent"])
        self.assertAlmostEqual(0.0, protocol["binary"]["mar_percent"])
        self.assertEqual(1, protocol["right_window_changepoint"]["detected_runs"])


if __name__ == "__main__":
    unittest.main()
