from __future__ import annotations

import unittest

import torch

from run_cmapss_rul_baselines import DEEP_BASELINES, build_deep_model


class RunCmapssRulBaselinesTest(unittest.TestCase):
    def test_lstm_sequence_is_available_as_published_style_deep_baseline(self) -> None:
        self.assertIn("lstm_sequence", DEEP_BASELINES)

        model = build_deep_model("lstm_sequence", n_features=6, hidden_dim=8, layers=1, dropout=0.0)
        with torch.no_grad():
            pred = model(torch.zeros(4, 12, 6))

        self.assertEqual((4,), tuple(pred.shape))
        self.assertTrue(torch.all(pred >= 0.0))
        self.assertTrue(torch.all(pred <= 1.0))


if __name__ == "__main__":
    unittest.main()
