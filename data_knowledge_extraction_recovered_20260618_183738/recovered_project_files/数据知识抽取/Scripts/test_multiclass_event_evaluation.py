from __future__ import annotations

import unittest

import numpy as np

from multiclass_event_evaluation import (
    compute_event_level_multiclass_metrics,
    compute_multiclass_metrics,
    compute_path_explanation_metrics,
    summarize_multiclass_event_evaluation,
)


class MulticlassEventEvaluationTests(unittest.TestCase):
    def test_sample_metrics_include_macro_top2_and_wrong_class_alarm_rate(self) -> None:
        y_true = np.array([0, 1, 2, 2, 1])
        proba = np.array(
            [
                [0.80, 0.10, 0.10],
                [0.10, 0.70, 0.20],
                [0.20, 0.60, 0.20],
                [0.20, 0.20, 0.60],
                [0.10, 0.40, 0.50],
            ],
            dtype=float,
        )

        metrics = compute_multiclass_metrics(
            y_true,
            proba,
            class_names=["normal", "temp", "mold"],
            normal_class_id=0,
            top_k=2,
        )

        self.assertGreater(metrics["macro_recall"], 0.0)
        self.assertGreater(metrics["macro_f1"], 0.0)
        self.assertGreater(metrics["top2_accuracy"], metrics["accuracy"])
        self.assertAlmostEqual(metrics["wrong_class_alarm_rate"], 0.5)
        self.assertIn("mold", metrics["per_class"])
        self.assertIn("auc_pr", metrics["per_class"]["temp"])

    def test_event_metrics_score_correct_class_warning_and_lead_time(self) -> None:
        y_true = np.array([1, 1, 0, 2, 2, 0])
        proba = np.array(
            [
                [0.20, 0.70, 0.10],
                [0.20, 0.60, 0.20],
                [0.80, 0.10, 0.10],
                [0.20, 0.30, 0.50],
                [0.20, 0.20, 0.60],
                [0.70, 0.20, 0.10],
            ],
            dtype=float,
        )
        event_ids = np.array(["e1", "e1", "n1", "e2", "e2", "n2"], dtype=object)
        horizons = np.array([5, 2, -1, 6, 1, -1], dtype=float)

        metrics = compute_event_level_multiclass_metrics(
            y_true,
            proba,
            event_ids=event_ids,
            horizons=horizons,
            class_names=["normal", "temp", "mold"],
            normal_class_id=0,
        )

        self.assertAlmostEqual(metrics["event_macro_recall"], 1.0)
        self.assertAlmostEqual(metrics["event_recall"], 1.0)
        self.assertGreater(metrics["average_lead_time"], 0.0)
        self.assertEqual(metrics["missed_event_rate"], 0.0)
        self.assertIn("mold", metrics["per_class_event"])

    def test_path_metrics_measure_hit_rate_and_knowledge_consistency(self) -> None:
        top_paths_by_class = {
            "temperature_flux": [
                {"defect_mechanism": "temperature_flux", "score": 0.8},
                {"defect_mechanism": "mold_level_slag_risk", "score": 0.2},
            ],
            "mold_level_slag_risk": [
                {"defect_mechanism": "mold_level_slag_risk", "score": 0.7}
            ],
            "speed_stopper_flow": [],
        }

        metrics = compute_path_explanation_metrics(
            top_paths_by_class,
            true_classes=["temperature_flux", "mold_level_slag_risk", "speed_stopper_flow"],
        )

        self.assertAlmostEqual(metrics["path_hit_rate"], 2 / 3)
        self.assertAlmostEqual(metrics["knowledge_consistency"], 2 / 3)
        self.assertAlmostEqual(metrics["per_class"]["temperature_flux"]["knowledge_consistency"], 0.5)

    def test_summary_combines_three_metric_layers(self) -> None:
        y_true = np.array([0, 1, 2, 2, 1])
        proba = np.array(
            [
                [0.80, 0.10, 0.10],
                [0.10, 0.70, 0.20],
                [0.20, 0.60, 0.20],
                [0.20, 0.20, 0.60],
                [0.10, 0.40, 0.50],
            ],
            dtype=float,
        )
        summary = summarize_multiclass_event_evaluation(
            y_true,
            proba,
            class_names=["normal", "temp", "mold"],
            event_ids=np.array(["n", "e1", "e2", "e2", "e1"], dtype=object),
            horizons=np.array([-1, 3, 4, 1, 2], dtype=float),
            top_paths_by_class={"temp": [{"defect_mechanism": "temp"}], "mold": [{"defect_mechanism": "mold"}]},
        )

        self.assertIn("sample_multiclass_metrics", summary)
        self.assertIn("event_warning_metrics", summary)
        self.assertIn("path_explanation_metrics", summary)
        self.assertIn("macro_recall", summary["sample_multiclass_metrics"])


if __name__ == "__main__":
    unittest.main()
