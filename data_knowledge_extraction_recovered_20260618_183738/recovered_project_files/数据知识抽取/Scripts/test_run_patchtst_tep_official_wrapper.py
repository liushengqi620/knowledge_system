from __future__ import annotations

import unittest

import numpy as np
import torch
import torch.nn as nn

from run_patchtst_tep_official_wrapper import (
    OfficialPatchTSTClassifier,
    _target_defect_macro_f1,
    build_patchtst_config,
    summarize_runs,
)


class _FakeOfficialPatchTST(nn.Module):
    def __init__(self, config) -> None:
        super().__init__()
        self.linear = nn.Linear(int(config.enc_in), int(config.enc_in))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x[:, -1:, :])


class RunPatchtstTepOfficialWrapperTest(unittest.TestCase):
    def test_config_validates_patch_and_attention_dimensions(self) -> None:
        config = build_patchtst_config(
            n_features=5,
            window_size=16,
            patch_len=8,
            stride=4,
            d_model=32,
            n_heads=4,
            e_layers=1,
            d_ff=64,
            dropout=0.1,
            fc_dropout=0.1,
            head_dropout=0.1,
            revin=True,
        )

        self.assertEqual(config.enc_in, 5)
        self.assertEqual(config.pred_len, 1)
        self.assertEqual(config.padding_patch, "end")

        with self.assertRaises(ValueError):
            build_patchtst_config(
                n_features=5,
                window_size=16,
                patch_len=20,
                stride=4,
                d_model=32,
                n_heads=4,
                e_layers=1,
                d_ff=64,
                dropout=0.1,
                fc_dropout=0.1,
                head_dropout=0.1,
                revin=True,
            )
        with self.assertRaises(ValueError):
            build_patchtst_config(
                n_features=5,
                window_size=16,
                patch_len=8,
                stride=4,
                d_model=30,
                n_heads=4,
                e_layers=1,
                d_ff=64,
                dropout=0.1,
                fc_dropout=0.1,
                head_dropout=0.1,
                revin=True,
            )

    def test_classifier_forward_uses_official_backbone_output_shape(self) -> None:
        config = build_patchtst_config(
            n_features=5,
            window_size=16,
            patch_len=8,
            stride=4,
            d_model=32,
            n_heads=4,
            e_layers=1,
            d_ff=64,
            dropout=0.1,
            fc_dropout=0.1,
            head_dropout=0.1,
            revin=True,
        )
        model = OfficialPatchTSTClassifier(_FakeOfficialPatchTST, config=config, n_classes=3)
        logits = model(torch.zeros(7, 16, 5))

        self.assertEqual(tuple(logits.shape), (7, 3))
        self.assertIn("official_patchtst", model.model_family)

    def test_target_defect_macro_and_summary_are_finite(self) -> None:
        y_true = np.asarray([0, 1, 1, 2, 2], dtype=np.int64)
        y_pred = np.asarray([0, 1, 0, 2, 1], dtype=np.int64)

        score = _target_defect_macro_f1(y_true, y_pred, 3)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

        summary = summarize_runs(
            [
                {
                    "sample_multiclass_metrics": {"target_defect_macro_f1": score, "macro_f1": 0.5},
                    "event_warning_metrics": {"event_macro_recall": 0.25},
                    "training": {"train_seconds": 1.0},
                },
                {
                    "sample_multiclass_metrics": {"target_defect_macro_f1": 0.0, "macro_f1": 0.25},
                    "event_warning_metrics": {"event_macro_recall": 0.0},
                    "training": {"train_seconds": 2.0},
                },
            ]
        )

        self.assertIn("target_defect_macro_f1", summary)
        self.assertEqual(summary["train_seconds"]["mean"], 1.5)


if __name__ == "__main__":
    unittest.main()
