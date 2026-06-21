from __future__ import annotations

import unittest

import numpy as np

from run_kiepgl_multiclass_experiment import (
    align_proba_to_class_ids,
    build_event_ids,
    time_ordered_split_indices,
)


class KIEPGLMulticlassExperimentTests(unittest.TestCase):
    def test_align_proba_to_class_ids_inserts_missing_classes(self) -> None:
        proba = np.array([[0.2, 0.8], [0.7, 0.3]], dtype=float)
        classes = np.array([0, 2], dtype=int)

        aligned = align_proba_to_class_ids(proba, classes, expected_class_ids=[0, 1, 2])

        self.assertEqual(aligned.shape, (2, 3))
        self.assertTrue(np.allclose(aligned[:, 0], proba[:, 0]))
        self.assertTrue(np.allclose(aligned[:, 1], 0.0))
        self.assertTrue(np.allclose(aligned[:, 2], proba[:, 1]))

    def test_time_ordered_split_indices_are_contiguous(self) -> None:
        train, val, test = time_ordered_split_indices(10, test_size=0.2, val_size=0.2)

        self.assertEqual(train.tolist(), [0, 1, 2, 3, 4, 5])
        self.assertEqual(val.tolist(), [6, 7])
        self.assertEqual(test.tolist(), [8, 9])

    def test_build_event_ids_groups_contiguous_abnormal_runs(self) -> None:
        y = np.array([0, 1, 1, 0, 2, 2, 1], dtype=int)
        event_ids = build_event_ids(y)

        self.assertEqual(event_ids.tolist(), ["normal_0", "event_1", "event_1", "normal_3", "event_4", "event_4", "event_6"])


if __name__ == "__main__":
    unittest.main()
