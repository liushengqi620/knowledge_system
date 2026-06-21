from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from prepare_anomaly_transformer_skab_official_adapter import build_adapter_payload, write_adapter_artifacts


def _fs_path(path: Path | str) -> str:
    text = str(Path(path).resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _write_run(path: Path, *, anomaly_after: int | None = None, n_rows: int = 80) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for idx in range(n_rows):
        anomaly = 1 if anomaly_after is not None and idx >= anomaly_after else 0
        rows.append(
            {
                "datetime": f"2026-01-01 00:{idx:02d}:00",
                "sensor_a": float(idx),
                "sensor_b": float(idx % 7),
                "anomaly": anomaly,
                "changepoint": 1 if anomaly_after is not None and idx == anomaly_after else 0,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


class PrepareAnomalyTransformerSkabOfficialAdapterTest(unittest.TestCase):
    def test_writes_psm_compatible_files_and_protocol_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_root = root / "dataset"
            extracted = dataset_root / "skab" / "raw" / "extracted" / "SKAB-master" / "data"
            _write_run(extracted / "anomaly-free" / "normal_0.csv")
            _write_run(extracted / "anomaly-free" / "normal_1.csv")
            _write_run(extracted / "other" / "other_0.csv", anomaly_after=50)
            _write_run(extracted / "valve1" / "valve1_0.csv", anomaly_after=40)
            _write_run(extracted / "valve2" / "valve2_0.csv", anomaly_after=45)
            output_root = root / "adapter"

            payload = build_adapter_payload(
                dataset_root,
                output_root,
                seeds=[42],
                win_size=16,
                batch_size=8,
                epochs=1,
            )
            written = write_adapter_artifacts(payload, output_root)

            self.assertEqual(payload["overall_status"], "official_source_adapter_prepared")
            seed_payload = payload["seeds"][0]
            adapter_dir = Path(seed_payload["adapter_dir"])
            for name in [
                "train.csv",
                "val.csv",
                "val_label.csv",
                "test.csv",
                "test_label.csv",
                "train_meta.csv",
                "val_meta.csv",
                "test_meta.csv",
            ]:
                self.assertTrue(os.path.exists(_fs_path(adapter_dir / name)), name)

            train = pd.read_csv(_fs_path(adapter_dir / "train.csv"))
            labels = pd.read_csv(_fs_path(adapter_dir / "test_label.csv"))
            self.assertEqual(list(train.columns[:3]), ["timestamp", "sensor_a", "sensor_b"])
            self.assertEqual(list(labels.columns), ["timestamp", "label"])
            self.assertEqual(seed_payload["row_counts"]["train_positive_rows"], 0)
            self.assertFalse(seed_payload["protocol_alignment"]["official_external_score"])
            self.assertTrue(seed_payload["protocol_alignment"]["requires_solver_patch"])
            self.assertIn("point adjustment", seed_payload["protocol_alignment"]["point_adjustment"])
            self.assertIn("official_unmodified_train_command", seed_payload["commands"])
            self.assertIn("official_unmodified_test_command", seed_payload["commands"])

            expected = {
                output_root / "anomaly_transformer_official_skab_adapter.json",
                output_root / "anomaly_transformer_official_skab_adapter.md",
            }
            self.assertEqual(set(written), expected)
            for path in expected:
                self.assertTrue(os.path.exists(_fs_path(path)), path)
                self.assertGreater(os.stat(_fs_path(path)).st_size, 500, path)


if __name__ == "__main__":
    unittest.main()
