from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from build_kiepgl_hierarchical_dataset_v6 import build_kiepgl_hierarchical_dataset_v6
from run_kiepgl_multiclass_experiment import combine_hierarchical_probabilities


class KIEPGLHierarchicalTests(unittest.TestCase):
    def test_v6_builder_adds_risk_and_subtype_labels(self) -> None:
        root = Path(__file__).resolve().parent.parent / "knowledge_exports" / f"_test_v6_{uuid.uuid4().hex}"
        input_dir = root / "v5"
        output_dir = root / "v6"
        try:
            input_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "sample_id": ["n_late", "t_late", "m_late"],
                    "event_bag_id": ["n", "t", "m"],
                    "precursor_stage": ["late", "late", "late"],
                    "cast_speed_mean_mean": [1.0, 1.2, 1.4],
                }
            ).to_csv(input_dir / "X_event_precursor_windows.csv", index=False, encoding="utf-8-sig")
            pd.DataFrame(
                {
                    "sample_id": ["n_late", "t_late", "m_late"],
                    "event_bag_id": ["n", "t", "m"],
                    "precursor_stage": ["late", "late", "late"],
                    "event_quality_class_id": [0, 1, 2],
                    "event_quality_class": ["no_quality_abnormal", "temperature_flux", "mold_level_slag_risk"],
                    "event_is_abnormal": [0, 1, 1],
                }
            ).to_csv(input_dir / "y_event_bag_label.csv", index=False, encoding="utf-8-sig")
            (input_dir / "class_name_mapping.json").write_text(
                json.dumps(
                    {
                        "primary_label_column": "event_quality_class_id",
                        "classes": [
                            {"class_id": 0, "class_name": "no_quality_abnormal"},
                            {"class_id": 1, "class_name": "temperature_flux"},
                            {"class_id": 2, "class_name": "mold_level_slag_risk"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_kiepgl_hierarchical_dataset_v6(input_dir, output_dir)
            y_out = pd.read_csv(output_dir / "y_hierarchical_event_label.csv", encoding="utf-8-sig")

            self.assertEqual(summary["dataset_version"], "v6_kiepgl_hierarchical_event_bag")
            self.assertEqual(y_out["risk_label"].astype(int).tolist(), [0, 1, 1])
            self.assertTrue(pd.isna(y_out.loc[0, "subtype_label"]))
            self.assertEqual(y_out.loc[1:, "subtype_label"].astype(int).tolist(), [1, 2])
            self.assertEqual(
                y_out["hierarchical_sample_role"].tolist(),
                ["risk_negative", "risk_positive_subtype", "risk_positive_subtype"],
            )
            self.assertTrue((output_dir / "X_event_precursor_windows.csv").is_file())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_combine_hierarchical_probabilities_preserves_risk_and_subtype_mass(self) -> None:
        risk_probability = np.array([0.25, 0.80], dtype=float)
        subtype_probability = np.array([[0.70, 0.30], [0.10, 0.90]], dtype=float)

        combined = combine_hierarchical_probabilities(
            risk_probability,
            subtype_probability,
            subtype_class_ids=[1, 3],
            expected_class_ids=[0, 1, 2, 3],
        )

        self.assertEqual(combined.shape, (2, 4))
        self.assertTrue(np.allclose(combined.sum(axis=1), 1.0))
        self.assertTrue(np.allclose(combined[:, 0], [0.75, 0.20]))
        self.assertTrue(np.allclose(combined[:, 1], [0.25 * 0.70, 0.80 * 0.10]))
        self.assertTrue(np.allclose(combined[:, 2], [0.0, 0.0]))
        self.assertTrue(np.allclose(combined[:, 3], [0.25 * 0.30, 0.80 * 0.90]))


if __name__ == "__main__":
    unittest.main()
