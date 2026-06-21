from __future__ import annotations

import unittest

import numpy as np
import torch
import torch.nn as nn

from run_graph_wavenet_tep_official_wrapper import (
    OfficialGraphWaveNetClassifier,
    _target_defect_macro_f1,
    patch_official_graph_wavenet_conv1d_modules,
    summarize_runs,
)


class _FakeOfficialGraphWaveNet(nn.Module):
    def __init__(
        self,
        device,
        num_nodes,
        dropout=0.1,
        supports=None,
        gcn_bool=True,
        addaptadj=True,
        aptinit=None,
        in_dim=1,
        out_dim=16,
        residual_channels=16,
        dilation_channels=16,
        skip_channels=64,
        end_channels=128,
        blocks=2,
        layers=2,
    ) -> None:
        super().__init__()
        self.out_dim = int(out_dim)
        self.num_nodes = int(num_nodes)
        self.nodevec1 = nn.Parameter(torch.randn(int(num_nodes), 4, device=device))
        self.nodevec2 = nn.Parameter(torch.randn(4, int(num_nodes), device=device))
        self.gate_convs = nn.ModuleList()
        self.residual_convs = nn.ModuleList()
        self.skip_convs = nn.ModuleList()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x.new_zeros((x.shape[0], self.out_dim, self.num_nodes, 1))


class _PatchTarget(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.gate_convs = nn.ModuleList([nn.Conv1d(3, 5, kernel_size=(1, 2), dilation=2)])
        self.residual_convs = nn.ModuleList([nn.Conv1d(5, 3, kernel_size=(1, 1))])
        self.skip_convs = nn.ModuleList([nn.Conv1d(5, 7, kernel_size=(1, 1))])


class RunGraphWaveNetTepOfficialWrapperTest(unittest.TestCase):
    def test_conv1d_compatibility_patch_replaces_modules(self) -> None:
        target = _PatchTarget()
        original = target.gate_convs[0].weight.detach().clone()

        diag = patch_official_graph_wavenet_conv1d_modules(target)

        self.assertTrue(diag["enabled"])
        self.assertIsInstance(target.gate_convs[0], nn.Conv2d)
        self.assertEqual(tuple(target.gate_convs[0].weight.shape), tuple(original.shape))
        self.assertTrue(torch.allclose(target.gate_convs[0].weight, original))
        self.assertEqual(diag["patched_module_counts"]["gate_convs"], 1)

    def test_classifier_forward_uses_official_backbone_contract(self) -> None:
        device = torch.device("cpu")
        model = OfficialGraphWaveNetClassifier(
            _FakeOfficialGraphWaveNet,
            device=device,
            num_nodes=6,
            n_classes=4,
            encoder_dim=8,
            residual_channels=8,
            dilation_channels=8,
            skip_channels=16,
            end_channels=32,
            blocks=1,
            layers=1,
        )
        logits = model(torch.zeros(5, 12, 6))

        self.assertEqual(tuple(logits.shape), (5, 4))
        self.assertIn("official_graph_wavenet", model.model_family)
        self.assertFalse(model.compatibility_patch["enabled"])

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
