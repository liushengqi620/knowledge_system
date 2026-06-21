from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from run_public_ms_gse_rpf_experiment import _resolve_external_candidate_scales
from run_public_ms_gse_rpf_experiment import build_classification_prediction_records


class RunPublicMsGseRpfSourceComplexityTest(unittest.TestCase):
    def test_resolve_external_candidate_scales_preserves_requested_scales_by_default(self) -> None:
        expert, llm, default, diag = _resolve_external_candidate_scales(
            expert_scale=1.0,
            llm_scale=0.7,
            default_scale=0.85,
            disable_source_complexity_penalty=False,
        )

        self.assertEqual(expert, 1.0)
        self.assertEqual(llm, 0.7)
        self.assertEqual(default, 0.85)
        self.assertTrue(diag["enabled"])
        self.assertFalse(diag["disabled_for_ablation"])

    def test_disable_source_complexity_penalty_sets_all_family_scales_to_one(self) -> None:
        expert, llm, default, diag = _resolve_external_candidate_scales(
            expert_scale=0.4,
            llm_scale=0.3,
            default_scale=0.2,
            disable_source_complexity_penalty=True,
        )

        self.assertEqual((expert, llm, default), (1.0, 1.0, 1.0))
        self.assertFalse(diag["enabled"])
        self.assertTrue(diag["disabled_for_ablation"])
        self.assertEqual(diag["requested_scales"]["llm"], 0.3)

    def test_build_classification_prediction_records_preserves_skab_native_fields(self) -> None:
        meta = pd.DataFrame(
            {
                "record_id": ["a", "b"],
                "run_id": ["run_1", "run_1"],
                "run_group": ["valve1", "valve1"],
                "datetime": ["2020-01-01 00:00:00", "2020-01-01 00:00:01"],
                "anomaly": [0, 1],
                "changepoint": [0, 1],
            }
        )
        records = build_classification_prediction_records(
            meta,
            np.asarray([0, 1], dtype=np.int64),
            np.asarray([0, 1], dtype=np.int64),
            np.asarray([[0.60, 0.40], [0.45, 0.55]], dtype=float),
            class_id_mapping={"0": 0, "1": 1},
            positive_threshold=0.50,
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["y_pred_original"], 0)
        self.assertEqual(records[1]["y_pred_original"], 1)
        self.assertEqual(records[1]["positive_score"], 0.55)
        self.assertEqual(records[1]["positive_threshold"], 0.50)
        self.assertEqual(records[1]["run_id"], "run_1")
        self.assertEqual(records[1]["changepoint"], 1)
        self.assertEqual(records[1]["proba"], [0.45, 0.55])


if __name__ == "__main__":
    unittest.main()
