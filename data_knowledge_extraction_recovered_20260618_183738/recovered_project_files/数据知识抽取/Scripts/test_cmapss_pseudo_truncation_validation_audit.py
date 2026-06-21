from __future__ import annotations

import unittest

import pandas as pd

from cmapss_pseudo_truncation_validation_audit import (
    build_pseudo_terminal_indices,
    parse_candidate,
    render_markdown,
    summarize_candidate_runs,
)


class CmapssPseudoTruncationValidationAuditTest(unittest.TestCase):
    def test_build_pseudo_terminal_indices_selects_train_unit_cutoffs(self) -> None:
        meta = pd.DataFrame(
            [
                {"subset": "FD001", "unit": 1, "rul": 120.0},
                {"subset": "FD001", "unit": 1, "rul": 80.0},
                {"subset": "FD001", "unit": 1, "rul": 50.0},
                {"subset": "FD001", "unit": 2, "rul": 110.0},
                {"subset": "FD001", "unit": 2, "rul": 75.0},
                {"subset": "FD001", "unit": 2, "rul": 30.0},
            ]
        )

        selected = build_pseudo_terminal_indices(meta, [0, 1, 2, 3, 4, 5], target_ruls=[80, 50])

        self.assertEqual([1, 2, 4, 5], selected.tolist())

    def test_parse_candidate_and_summary_keep_cap_window_fields(self) -> None:
        parsed = parse_candidate("gru_w160_cap150")

        self.assertEqual("gru_sequence", parsed["baseline"])
        self.assertEqual(160, parsed["window_size"])
        self.assertEqual(150.0, parsed["rul_cap"])

        rows = [
            {
                "candidate": "gru_w160_cap150",
                "seed": 42,
                "window_size": 160,
                "rul_cap": 150.0,
                "pseudo_val_metrics": {"rul_rmse": 16.0, "rul_score": 100.0},
                "official_test_metrics": {"rul_rmse": 18.0, "rul_score": 200.0},
                "fit_seconds": 1.0,
            },
            {
                "candidate": "gru_w160_cap150",
                "seed": 43,
                "window_size": 160,
                "rul_cap": 150.0,
                "pseudo_val_metrics": {"rul_rmse": 18.0, "rul_score": 120.0},
                "official_test_metrics": {"rul_rmse": 20.0, "rul_score": 260.0},
                "fit_seconds": 3.0,
            },
        ]

        summary = summarize_candidate_runs(rows)

        self.assertEqual(1, len(summary))
        self.assertEqual("gru_w160_cap150", summary[0]["candidate"])
        self.assertEqual(17.0, summary[0]["pseudo_val_rmse_mean"])
        self.assertEqual(19.0, summary[0]["official_test_rmse_mean"])
        self.assertEqual(2.0, summary[0]["fit_seconds_mean"])

    def test_markdown_discloses_score_tradeoff(self) -> None:
        payload = {
            "version": "test",
            "status": "pseudo_truncation_validation_complete_with_score_tradeoff",
            "claim_boundary": "RMSE-oriented selection; score trade-offs must be reported.",
            "seeds": [42],
            "target_ruls": [20, 50],
            "summary": [
                {
                    "candidate": "gru_w160_cap150",
                    "n_seeds": 1,
                    "rul_cap": 150.0,
                    "window_size": 160,
                    "pseudo_val_rmse_mean": 16.0,
                    "pseudo_val_rmse_std": 0.0,
                    "pseudo_val_score_mean": 100.0,
                    "official_test_rmse_mean": 18.0,
                    "official_test_rmse_std": 0.0,
                    "official_test_score_mean": 300.0,
                },
                {
                    "candidate": "gru_w80_cap150",
                    "n_seeds": 1,
                    "rul_cap": 150.0,
                    "window_size": 80,
                    "pseudo_val_rmse_mean": 17.0,
                    "pseudo_val_rmse_std": 0.0,
                    "pseudo_val_score_mean": 120.0,
                    "official_test_rmse_mean": 19.0,
                    "official_test_rmse_std": 0.0,
                    "official_test_score_mean": 250.0,
                },
            ],
            "selected_by_pseudo_validation": {"candidate": "gru_w160_cap150"},
            "best_by_official_test": {"candidate": "gru_w160_cap150"},
            "selected_by_pseudo_validation_score": {"candidate": "gru_w160_cap150"},
            "best_by_official_test_score": {"candidate": "gru_w80_cap150"},
            "official_score_tradeoff": {"score_gap": 50.0},
            "gates": {
                "pseudo_rmse_selection_matches_best_test_rmse": True,
                "pseudo_score_selection_matches_best_test_score": False,
            },
            "next_actions": ["Evaluate path fusion on the same panel."],
        }

        markdown = render_markdown(payload)

        self.assertIn("complete_with_score_tradeoff", markdown)
        self.assertIn("Selected by pseudo-validation RMSE", markdown)
        self.assertIn("Best by official-test PHM score audit", markdown)
        self.assertIn("score trade-off", markdown)
        self.assertIn("closed", markdown)


if __name__ == "__main__":
    unittest.main()
