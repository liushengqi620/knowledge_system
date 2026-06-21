from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from summarize_tep_matched_baselines import BaselineSpec, summarize


class SummarizeTepMatchedBaselinesTest(unittest.TestCase):
    def test_summarizes_summary_table_and_sequence_ablation_variants(self) -> None:
        root = Path.cwd() / "tmp_tests" / f"tep_matched_{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        strict = root / "strict.json"
        seq = root / "seq.json"
        strict.write_text(
            json.dumps(
                {
                    "summary_table": [
                        {
                            "experiment_name": "full_model",
                            "target_defect_macro_f1_mean": 0.9549,
                            "target_defect_macro_f1_std": 0.0023,
                            "macro_f1_mean": 0.9459,
                            "macro_f1_std": 0.0021,
                            "event_macro_recall_mean": 0.9048,
                            "event_macro_recall_std": 0.0,
                            "path_hit_rate_mean": 0.7143,
                            "path_hit_rate_std": 0.0,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        seq.write_text(
            json.dumps(
                {
                    "model_name": "tcn",
                    "summary": {
                        "no_graph": {
                            "n_runs": 3,
                            "target_defect_macro_f1_mean": 0.5754,
                            "target_defect_macro_f1_std": 0.0141,
                            "macro_f1_mean": 0.5564,
                            "macro_f1_std": 0.0149,
                            "event_macro_recall_mean": 0.6667,
                            "event_macro_recall_std": 0.0,
                            "path_hit_rate_mean": 0.0,
                            "path_hit_rate_std": 0.0,
                        },
                        "residual_gated_lagged": {
                            "n_runs": 3,
                            "target_defect_macro_f1_mean": 0.6034,
                            "target_defect_macro_f1_std": 0.0096,
                            "macro_f1_mean": 0.5846,
                            "macro_f1_std": 0.0104,
                            "event_macro_recall_mean": 0.6667,
                            "event_macro_recall_std": 0.0389,
                            "path_hit_rate_mean": 0.0,
                            "path_hit_rate_std": 0.0,
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

        report = summarize(
            reference=BaselineSpec(label="StrictMechanism", path=strict),
            baselines=[
                BaselineSpec(label="TCN-NoGraph", path=seq, variant="no_graph"),
                BaselineSpec(label="TCN-ResidualGated", path=seq, variant="residual_gated_lagged"),
            ],
        )

        self.assertIn("StrictMechanism", report)
        self.assertIn("TCN-ResidualGated", report)
        self.assertIn("0.6034 +/- 0.0096", report)
        self.assertIn("+0.0280", report)
        self.assertIn("-0.3515", report)
        self.assertIn("matched TEP protocol", report)

    def test_accepts_manual_metric_records_for_missing_reference_files(self) -> None:
        report = summarize(
            reference=BaselineSpec(
                label="StrictMechanism",
                manual_metrics={
                    "target_defect_macro_f1_mean": 0.9549,
                    "target_defect_macro_f1_std": 0.0023,
                },
            ),
            baselines=[
                BaselineSpec(
                    label="PublishedTCN",
                    manual_metrics={
                        "target_defect_macro_f1_mean": 0.2645,
                        "target_defect_macro_f1_std": 0.0085,
                    },
                )
            ],
        )

        self.assertIn("PublishedTCN", report)
        self.assertIn("0.2645 +/- 0.0085", report)
        self.assertIn("-0.6904", report)


if __name__ == "__main__":
    unittest.main()
