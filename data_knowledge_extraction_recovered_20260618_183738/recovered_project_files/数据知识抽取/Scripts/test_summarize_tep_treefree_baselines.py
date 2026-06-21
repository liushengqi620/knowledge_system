from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_tep_treefree_baselines import summarize


class TepTreeFreeSummaryTest(unittest.TestCase):
    def test_summary_extracts_full_model_metrics_and_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            full = root / "full.json"
            tcn = root / "tcn.json"
            full.write_text(
                json.dumps(
                    {
                        "summary_table": [
                            {
                                "experiment_name": "full_model",
                                "target_defect_macro_f1_mean": 0.952,
                                "target_defect_macro_f1_std": 0.007,
                                "macro_f1_mean": 0.943,
                                "macro_f1_std": 0.006,
                                "event_macro_recall_mean": 0.841,
                                "event_macro_recall_std": 0.022,
                                "path_hit_rate_mean": 0.714,
                                "path_hit_rate_std": 0.0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            tcn.write_text(
                json.dumps(
                    {
                        "risk_head": "tcn",
                        "tep_prior_mode": "none",
                        "summary_table": [
                            {
                                "experiment_name": "full_model",
                                "target_defect_macro_f1_mean": 0.2645,
                                "target_defect_macro_f1_std": 0.0085,
                                "macro_f1_mean": 0.2526,
                                "macro_f1_std": 0.0082,
                                "event_macro_recall_mean": 0.2857,
                                "event_macro_recall_std": 0.0389,
                                "path_hit_rate_mean": 0.0476,
                                "path_hit_rate_std": 0.0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = summarize(reference=("StrictMechanism", full), variants=[("TCN-NoPrior", tcn)])

        self.assertIn("TCN-NoPrior", report)
        self.assertIn("0.2645 +/- 0.0085", report)
        self.assertIn("-0.6875", report)
        self.assertIn("tree-free", report)


if __name__ == "__main__":
    unittest.main()
