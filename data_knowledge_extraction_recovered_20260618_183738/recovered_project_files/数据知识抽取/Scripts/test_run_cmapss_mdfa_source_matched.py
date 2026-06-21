from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import torch

import numpy as np

from run_cmapss_mdfa_source_matched import (
    MDFA2DRULRegressor,
    MDFARULRegressor,
    _apply_output_calibration,
    _augment_temporal_window,
    _fit_output_calibration,
    load_raw_subset,
    run_experiment,
)


def _write_subset(raw_dir: Path, subset: str, *, train_units: int, test_units: int, cycles: int) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    train_lines = []
    test_lines = []
    for unit in range(1, train_units + 1):
        for cycle in range(1, cycles + 1):
            features = [unit, cycle] + [round((unit * 0.01) + (cycle * 0.001) + (col * 0.0001), 6) for col in range(24)]
            train_lines.append(" ".join(str(value) for value in features) + "\n")
    for unit in range(1, test_units + 1):
        for cycle in range(1, cycles):
            features = [unit, cycle] + [round((unit * 0.02) + (cycle * 0.001) + (col * 0.0001), 6) for col in range(24)]
            test_lines.append(" ".join(str(value) for value in features) + "\n")
    (raw_dir / f"train_{subset}.txt").write_text("".join(train_lines), encoding="utf-8")
    (raw_dir / f"test_{subset}.txt").write_text("".join(test_lines), encoding="utf-8")
    (raw_dir / f"RUL_{subset}.txt").write_text("".join("5\n" for _ in range(test_units)), encoding="utf-8")


class RunCmapssMdfaSourceMatchedTest(unittest.TestCase):
    def test_temporal_level_diff_augmentation_adds_velocity_channels(self) -> None:
        window = np.asarray([[1.0, 3.0], [2.0, 5.0], [4.0, 6.0]], dtype=np.float32)
        augmented = _augment_temporal_window(window, "level_diff")

        self.assertEqual((3, 4), tuple(augmented.shape))
        np.testing.assert_allclose(augmented[:, :2], window)
        np.testing.assert_allclose(
            augmented[:, 2:],
            np.asarray([[0.0, 0.0], [1.0, 2.0], [2.0, 1.0]], dtype=np.float32),
        )

    def test_validation_affine_output_calibration_is_guarded(self) -> None:
        y_val = np.asarray([10.0, 20.0, 30.0], dtype=np.float32)
        pred = np.asarray([5.0, 10.0, 15.0], dtype=np.float32)

        calibration = _fit_output_calibration(
            policy="affine_val",
            y_val=y_val,
            val_pred=pred,
            rul_cap=125.0,
            min_val_rmse_delta=0.0,
        )

        self.assertTrue(calibration["applied"])
        self.assertGreater(calibration["val_rmse_delta"], 0.0)
        calibrated = _apply_output_calibration(np.asarray([6.0], dtype=np.float32), calibration)
        self.assertAlmostEqual(12.0, float(calibrated[0]), places=4)

        blocked = _fit_output_calibration(
            policy="affine_val",
            y_val=y_val,
            val_pred=pred,
            rul_cap=125.0,
            min_val_rmse_delta=100.0,
        )
        self.assertFalse(blocked["applied"])
        self.assertEqual("validation_rmse_delta_guard_failed", blocked["reason"])

    def test_model_forward_returns_normalized_rul(self) -> None:
        model = MDFARULRegressor(n_features=5, hidden_dim=8, dropout=0.0)
        with torch.no_grad():
            pred = model(torch.zeros(3, 10, 5))
        self.assertEqual((3,), tuple(pred.shape))
        self.assertTrue(torch.all(pred >= 0.0))
        self.assertTrue(torch.all(pred <= 1.0))

        source_model = MDFA2DRULRegressor(n_features=5, hidden_dim=8, dropout=0.0)
        with torch.no_grad():
            source_pred = source_model(torch.zeros(3, 10, 5))
        self.assertEqual((3,), tuple(source_pred.shape))
        self.assertTrue(torch.all(source_pred >= 0.0))
        self.assertTrue(torch.all(source_pred <= 1.0))

    def test_source_matched_runner_smoke_writes_prediction_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            output_dir = root / "out"
            _write_subset(raw_dir, "FD001", train_units=6, test_units=4, cycles=6)

            loaded = load_raw_subset(raw_dir, "FD001")
            self.assertEqual(6, len(set(loaded.train[:, 0].astype(int))))
            self.assertEqual(4, len(loaded.test_rul))

            summary = run_experiment(
                raw_dir=raw_dir,
                output_dir=output_dir,
                subsets=["FD001"],
                seeds=[7],
                window_size=3,
                pca_variance=0.95,
                feature_policy="mdfa_key_sensors_pca",
                val_fraction=0.34,
                max_train_windows=12,
                max_val_windows=6,
                rul_cap=20.0,
                cap_eval_rul=True,
                device="cpu",
                epochs=2,
                batch_size=4,
                learning_rate=0.001,
                hidden_dim=8,
                dropout=0.0,
                conv_formulation="source_2d",
                lr_scheduler="none",
                snapshot_ensemble_k=2,
                snapshot_ensemble_min_val_rmse_delta=0.0,
            )

            self.assertEqual("source_matched_candidate_not_exact_reproduction", summary["status"])
            self.assertEqual(4, summary["n_prediction_records"])
            self.assertTrue((output_dir / "cmapss_mdfa_source_matched_seed7.json").exists())
            self.assertTrue((output_dir / "cmapss_mdfa_source_matched_seed7_FD001.json").exists())
            self.assertTrue((output_dir / "cmapss_mdfa_source_matched_summary.json").exists())
            self.assertTrue(summary["run_complete"])
            self.assertEqual(1, summary["completed_subset_seed_count"])
            self.assertEqual(1, summary["expected_subset_seed_count"])
            self.assertIn("rul_rmse", summary["overall_metrics"])
            self.assertEqual("FD001", summary["subset_seed_rows"][0]["subset"])
            subset_path = output_dir / "cmapss_mdfa_source_matched_seed7_FD001.json"
            subset_payload = json.loads(subset_path.read_text(encoding="utf-8"))
            self.assertEqual("FD001", subset_payload["run_config"]["subset"])
            self.assertEqual("source_2d", subset_payload["run_config"]["conv_formulation"])
            self.assertEqual("mdfa_key_sensors_pca", subset_payload["run_config"]["feature_policy"])
            self.assertEqual("level", subset_payload["run_config"]["temporal_feature_mode"])
            self.assertEqual(subset_payload["pca_feature_dim"], subset_payload["model_input_feature_dim"])
            self.assertEqual("none", subset_payload["run_config"]["output_calibration"])
            self.assertEqual(2, subset_payload["run_config"]["snapshot_ensemble_k"])
            self.assertIn("snapshot_ensemble", subset_payload["diagnostics"])
            self.assertEqual(2, subset_payload["diagnostics"]["snapshot_ensemble"]["requested_k"])
            self.assertIn("member_val_rmses", subset_payload["diagnostics"]["snapshot_ensemble"])
            self.assertEqual(["s11", "s2", "s3", "s7", "s12", "s8", "s9", "s20", "s21"], subset_payload["selected_feature_names"])
            self.assertEqual("none", subset_payload["run_config"]["lr_scheduler"])
            self.assertIn("base_primary_test_metrics", subset_payload)
            self.assertIn("validation_prediction_records", subset_payload)
            self.assertTrue(subset_payload["validation_prediction_records"])
            self.assertEqual("validation", subset_payload["validation_prediction_records"][0]["split_role"])
            self.assertIn("rul_pred_base", subset_payload["rul_prediction_records"][0])
            subset_payload["cache_sentinel"] = "reuse-me"
            subset_path.write_text(json.dumps(subset_payload), encoding="utf-8")

            run_experiment(
                raw_dir=raw_dir,
                output_dir=output_dir,
                subsets=["FD001"],
                seeds=[7],
                window_size=3,
                pca_variance=0.95,
                feature_policy="mdfa_key_sensors_pca",
                val_fraction=0.34,
                max_train_windows=12,
                max_val_windows=6,
                rul_cap=20.0,
                cap_eval_rul=True,
                device="cpu",
                epochs=2,
                batch_size=4,
                learning_rate=0.001,
                hidden_dim=8,
                dropout=0.0,
                conv_formulation="source_2d",
                lr_scheduler="none",
                snapshot_ensemble_k=2,
                snapshot_ensemble_min_val_rmse_delta=0.0,
                resume=True,
            )
            resumed_seed = json.loads((output_dir / "cmapss_mdfa_source_matched_seed7.json").read_text(encoding="utf-8"))
            self.assertEqual("reuse-me", resumed_seed["subsets"][0]["cache_sentinel"])


if __name__ == "__main__":
    unittest.main()
