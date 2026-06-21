from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from tep_single_edge_validation_probe import (
    _aggregate_probe_records,
    _passes_pre_cf,
    _validation_metrics,
    build_measured_probe_plan,
    build_probe_feature_block,
    build_single_edge_features,
    lagged_series_by_run,
)


class TepSingleEdgeValidationProbeTest(unittest.TestCase):
    def test_lagged_series_by_run_does_not_cross_run_boundaries(self) -> None:
        meta = pd.DataFrame(
            {
                "source_split": ["train", "train", "train", "train", "train"],
                "source_file": ["run_a", "run_a", "run_a", "run_b", "run_b"],
                "sample_index": [0, 1, 2, 0, 1],
            }
        )
        values = np.asarray([10.0, 11.0, 12.0, 20.0, 21.0])

        lagged = lagged_series_by_run(values, meta, lag=1)

        np.testing.assert_allclose(lagged, np.asarray([10.0, 10.0, 11.0, 20.0, 20.0]))

    def test_build_single_edge_features_uses_run_local_lag_and_delta_terms(self) -> None:
        meta = pd.DataFrame(
            {
                "source_split": ["train", "train", "train", "train"],
                "source_file": ["run_a", "run_a", "run_b", "run_b"],
                "sample_index": [0, 1, 0, 1],
            }
        )
        x = pd.DataFrame(
            {
                "xmeas_1": [1.0, 2.0, 100.0, 101.0],
                "xmeas_2": [3.0, 5.0, 200.0, 205.0],
            }
        )
        edge = {"edge_id": "e_x1_x2_lag1", "source": "xmeas_1", "target": "xmeas_2", "lag": 1}

        features = build_single_edge_features(x, meta, edge)

        self.assertEqual(
            list(features.columns),
            [
                "e_x1_x2_lag1__src_lag",
                "e_x1_x2_lag1__target",
                "e_x1_x2_lag1__delta",
                "e_x1_x2_lag1__abs_delta",
                "e_x1_x2_lag1__product",
            ],
        )
        np.testing.assert_allclose(features["e_x1_x2_lag1__src_lag"].to_numpy(), [1.0, 1.0, 100.0, 100.0])
        np.testing.assert_allclose(features["e_x1_x2_lag1__delta"].to_numpy(), [2.0, 4.0, 100.0, 105.0])

    def test_build_probe_feature_block_concatenates_multiple_edges(self) -> None:
        meta = pd.DataFrame(
            {
                "source_split": ["train", "train"],
                "source_file": ["run_a", "run_a"],
                "sample_index": [0, 1],
            }
        )
        x = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0], "c": [5.0, 6.0]})
        edges = [
            {"edge_id": "e_ab", "source": "a", "target": "b", "lag": 1},
            {"edge_id": "e_bc", "source": "b", "target": "c", "lag": 0},
        ]

        features = build_probe_feature_block(x, meta, edges)

        self.assertEqual(features.shape, (2, 10))
        self.assertIn("e_ab__delta", features.columns)
        self.assertIn("e_bc__product", features.columns)

    def test_validation_metrics_report_target_low_tail_far_and_mar(self) -> None:
        y_true = np.asarray([0, 0, 1, 1, 2, 2])
        proba = np.asarray(
            [
                [0.9, 0.1, 0.0],
                [0.8, 0.2, 0.0],
                [0.0, 0.9, 0.1],
                [0.0, 0.8, 0.2],
                [0.0, 0.1, 0.9],
                [0.0, 0.2, 0.8],
            ]
        )

        metrics = _validation_metrics(y_true, proba)

        self.assertAlmostEqual(metrics["target_defect_macro_f1"], 1.0)
        self.assertAlmostEqual(metrics["low_tail_f1"], 1.0)
        self.assertAlmostEqual(metrics["far"], 0.0)
        self.assertAlmostEqual(metrics["mar"], 0.0)

    def test_pre_cf_gate_blocks_negative_gain_even_if_cf_would_be_high(self) -> None:
        row = {
            "validation_gain": -0.01,
            "low_tail_delta": 0.1,
            "far_delta": 0.0,
            "mar_delta": 0.0,
            "cf_sensitivity": 0.99,
        }

        self.assertFalse(_passes_pre_cf(row, {"min_validation_gain": 0.0, "min_low_tail_delta": -0.002, "max_far_delta": 0.005, "max_mar_delta": 0.005}))

    def test_aggregate_probe_records_keeps_single_edge_admission_fields(self) -> None:
        rows = [
            {
                "edge_id": "e1",
                "source_family": "expert",
                "target_group": "reactor",
                "lag_group": "lag1",
                "validation_gain": 0.01,
                "low_tail_delta": 0.0,
                "far_delta": 0.0,
                "mar_delta": 0.0,
                "cf_sensitivity": 0.2,
            },
            {
                "edge_id": "e1",
                "source_family": "expert",
                "target_group": "reactor",
                "lag_group": "lag1",
                "validation_gain": 0.03,
                "low_tail_delta": 0.02,
                "far_delta": 0.001,
                "mar_delta": 0.0,
                "cf_sensitivity": 0.4,
            },
        ]

        aggregated = _aggregate_probe_records(rows)

        self.assertEqual(len(aggregated), 1)
        self.assertEqual(aggregated[0]["probe_level"], "single_edge")
        self.assertEqual(aggregated[0]["edge_ids"], ["e1"])
        self.assertAlmostEqual(aggregated[0]["validation_gain"], 0.02)
        self.assertAlmostEqual(aggregated[0]["cf_sensitivity"], 0.3)

    def test_aggregate_probe_records_keeps_group_probe_fields(self) -> None:
        rows = [
            {
                "probe_id": "source_family:expert",
                "probe_level": "source_family",
                "probe_key": "expert",
                "edge_ids": ["e1", "e2"],
                "n_edges": 2,
                "source_family": "expert",
                "validation_gain": 0.01,
                "low_tail_delta": 0.0,
                "far_delta": 0.0,
                "mar_delta": 0.0,
                "cf_sensitivity": None,
            },
            {
                "probe_id": "source_family:expert",
                "probe_level": "source_family",
                "probe_key": "expert",
                "edge_ids": ["e1", "e2"],
                "n_edges": 2,
                "source_family": "expert",
                "validation_gain": 0.03,
                "low_tail_delta": 0.02,
                "far_delta": 0.0,
                "mar_delta": 0.0,
                "cf_sensitivity": 0.5,
            },
        ]

        aggregated = _aggregate_probe_records(rows)

        self.assertEqual(aggregated[0]["probe_level"], "source_family")
        self.assertEqual(aggregated[0]["probe_key"], "expert")
        self.assertEqual(aggregated[0]["edge_ids"], ["e1", "e2"])
        self.assertEqual(aggregated[0]["n_edges"], 2)
        self.assertAlmostEqual(aggregated[0]["validation_gain"], 0.02)
        self.assertAlmostEqual(aggregated[0]["cf_sensitivity"], 0.5)

    def test_measured_probe_plan_supports_group_levels_and_single_limit(self) -> None:
        edges = [
            {"edge_id": "e1", "source_family": "expert", "target_group": "reactor", "lag_group": "lag1"},
            {"edge_id": "e2", "source_family": "llm", "target_group": "feed", "lag_group": "lag2"},
            {"edge_id": "e3", "source_family": "expert", "target_group": "feed", "lag_group": "lag1"},
        ]

        plan = build_measured_probe_plan(
            edges,
            probe_levels=["source_family", "single_edge"],
            max_single_edge_probes=2,
        )

        self.assertEqual(len([row for row in plan if row["probe_level"] == "source_family"]), 2)
        self.assertEqual(len([row for row in plan if row["probe_level"] == "single_edge"]), 2)


if __name__ == "__main__":
    unittest.main()
