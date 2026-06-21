from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from build_tep_fault_dataset import build_tep_fault_dataset
from run_kiepgl_multiclass_experiment import split_indices_from_metadata


def _write_matrix(path: Path, rows: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(" ".join(str(value) for value in row) for row in rows),
        encoding="utf-8",
    )


class TepDatasetAdapterTest(unittest.TestCase):
    def test_builds_dataset_from_mixed_orientation_dat_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tep_raw"
            train = source / "train"
            test = source / "test"
            normal_transposed = [[float(i * 10 + j) for j in range(3)] for i in range(52)]
            faulty = [[float(i + j) for j in range(52)] for i in range(4)]
            _write_matrix(train / "d00.dat", normal_transposed)
            _write_matrix(train / "d01.dat", faulty)
            _write_matrix(test / "d00_te.dat", faulty)
            _write_matrix(test / "d01_te.dat", faulty)

            summary = build_tep_fault_dataset(
                source,
                root / "out",
                train_dir_name="train",
                test_dir_name="test",
                test_fault_onset=2,
            )

            x = pd.read_csv(root / "out" / "X_process_features.csv")
            y = pd.read_csv(root / "out" / "y_quality_label.csv")
            self.assertEqual(summary["n_rows"], 15)
            self.assertEqual(summary["n_x_features"], 52)
            self.assertEqual(x.shape, (15, 53))
            self.assertEqual(int((y["event_quality_class_id"] == 0).sum()), 9)
            self.assertEqual(int((y["event_quality_class_id"] == 1).sum()), 6)
            self.assertEqual(set(y["split_role"]), {"train", "test"})

    def test_split_indices_from_metadata_holds_out_validation_from_training_rows(self) -> None:
        y = pd.DataFrame(
            {
                "split_role": ["train"] * 10 + ["test"] * 4,
                "event_quality_class_id": [0, 1] * 5 + [0, 1, 0, 1],
            }
        )
        train_idx, val_idx, test_idx = split_indices_from_metadata(y, val_fraction=0.2)

        self.assertEqual(train_idx.tolist(), list(range(8)))
        self.assertEqual(val_idx.tolist(), [8, 9])
        self.assertEqual(test_idx.tolist(), [10, 11, 12, 13])


if __name__ == "__main__":
    unittest.main()
