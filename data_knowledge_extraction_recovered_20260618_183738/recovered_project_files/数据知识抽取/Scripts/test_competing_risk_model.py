from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from competing_risk_event_model import (
    COMPETING_RISK_CAUSE_GROUPS,
    CompetingRiskEventModel,
    build_candidate_cause_mask,
    stage_ids_from_series,
)


class CompetingRiskEventModelTests(unittest.TestCase):
    def test_candidate_cause_mask_supports_mixed_partial_labels(self) -> None:
        y = pd.DataFrame(
            {
                "quality_abnormal_groups": [
                    "no_quality_abnormal",
                    "temperature_flux;mold_level_slag_risk",
                    "process_fluctuation",
                ],
                "event_quality_class_id": [0, 1, 3],
            }
        )

        mask = build_candidate_cause_mask(y)

        self.assertEqual(mask.shape, (3, len(COMPETING_RISK_CAUSE_GROUPS)))
        self.assertEqual(mask[0].sum(), 0)
        self.assertEqual(mask[1, COMPETING_RISK_CAUSE_GROUPS.index("temperature_flux")], 1)
        self.assertEqual(mask[1, COMPETING_RISK_CAUSE_GROUPS.index("mold_level_slag_risk")], 1)
        self.assertEqual(mask[2, COMPETING_RISK_CAUSE_GROUPS.index("process_fluctuation")], 1)

    def test_competing_risk_model_outputs_cause_and_stage_probabilities(self) -> None:
        x = np.asarray(
            [
                [0.0, 0.0],
                [0.1, 0.2],
                [1.0, 0.5],
                [1.2, 0.7],
                [2.0, 1.0],
                [2.2, 1.1],
                [3.0, 1.4],
                [3.2, 1.5],
                [4.0, 2.0],
                [4.2, 2.2],
            ],
            dtype=np.float32,
        )
        y = pd.DataFrame(
            {
                "quality_abnormal_groups": [
                    "no_quality_abnormal",
                    "no_quality_abnormal",
                    "temperature_flux",
                    "temperature_flux",
                    "mold_level_slag_risk",
                    "mold_level_slag_risk",
                    "process_fluctuation",
                    "process_fluctuation",
                    "temperature_flux;mold_level_slag_risk",
                    "temperature_flux;mold_level_slag_risk",
                ],
                "event_quality_class_id": [0, 0, 1, 1, 2, 2, 3, 3, 1, 2],
                "precursor_stage": ["late", "mid", "late", "mid", "late", "mid", "late", "mid", "early", "early"],
            }
        )
        candidate_mask = build_candidate_cause_mask(y)
        stage_ids = stage_ids_from_series(y["precursor_stage"])
        risk_label = (pd.to_numeric(y["event_quality_class_id"], errors="coerce").fillna(0).astype(int).to_numpy() != 0).astype(int)

        model = CompetingRiskEventModel(max_epochs=10, hidden_dim=12, random_state=7)
        model.fit(x, candidate_mask, stage_ids, risk_label)
        pred = model.predict_proba(x)

        self.assertEqual(pred["class_probabilities"].shape, (len(x), 6))
        self.assertEqual(pred["stage_probabilities"].shape, (len(x), 3))
        self.assertEqual(pred["joint_probabilities"].shape, (len(x), 1 + 5 * 3))
        self.assertTrue(np.allclose(pred["class_probabilities"].sum(axis=1), 1.0, atol=1e-5))
        self.assertTrue(np.all(pred["risk_probability"] >= 0.0))
        self.assertTrue(np.all(pred["risk_probability"] <= 1.0))


if __name__ == "__main__":
    unittest.main()
