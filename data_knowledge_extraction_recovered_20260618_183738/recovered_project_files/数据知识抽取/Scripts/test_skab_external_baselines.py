from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from skab_external_baselines import build_skab_external_prediction_records


class SkabExternalBaselinesTest(unittest.TestCase):
    def test_build_prediction_records_preserves_native_fields(self) -> None:
        meta = pd.DataFrame(
            {
                "run_id": ["valve1_1", "valve1_1", "valve2_3"],
                "run_group": ["valve1", "valve1", "valve2"],
                "sample_index": [7, 8, 9],
                "anomaly": [0, 1, 1],
                "changepoint": [0, 1, 0],
            }
        )
        records = build_skab_external_prediction_records(
            meta,
            np.asarray([0, 1, 1]),
            np.asarray([[0.9, 0.1], [0.2, 0.8], [0.7, 0.3]]),
            np.asarray([0.01, 1.2, 0.4]),
            score_threshold=0.5,
            positive_threshold=0.5,
        )

        self.assertEqual(3, len(records))
        self.assertEqual("skab_valve1_1_00007", records[0]["record_id"])
        self.assertEqual(1, records[1]["y_pred_original"])
        self.assertEqual(0, records[2]["y_pred_original"])
        self.assertEqual(1, records[1]["changepoint"])
        self.assertAlmostEqual(1.2, records[1]["anomaly_score"])
        self.assertAlmostEqual(0.5, records[1]["anomaly_score_threshold"])
        self.assertEqual([0.2, 0.8], records[1]["proba"])


if __name__ == "__main__":
    unittest.main()
