from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from summarize_tep_ablation_table import summarize


def _write_run_file(path: Path, target_values: list[float]) -> None:
    path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "status": "ok",
                        "sample_multiclass_metrics": {
                            "target_defect_macro_f1": target,
                            "macro_f1": target - 0.01,
                        },
                        "event_warning_metrics": {
                            "event_macro_recall": 0.80 + idx * 0.02,
                        },
                        "path_explanation_metrics": {
                            "path_hit_rate": 0.70,
                        },
                    }
                    for idx, target in enumerate(target_values)
                ],
                "summary_table": [
                    {
                        "experiment_name": "full_model",
                        "target_defect_macro_f1_mean": 0.0,
                        "target_defect_macro_f1_std": 0.0,
                        "macro_f1_mean": 0.0,
                        "macro_f1_std": 0.0,
                        "event_macro_recall_mean": 0.0,
                        "event_macro_recall_std": 0.0,
                        "path_hit_rate_mean": 0.0,
                        "path_hit_rate_std": 0.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


class SummarizeTepAblationTableTest(unittest.TestCase):
    def test_combines_split_seed_files_from_runs_before_summary_fallback(self) -> None:
        root = Path.cwd() / "tmp_tests" / f"tep_ablation_{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        full_seed42 = root / "full_seed42.json"
        full_seed43_44 = root / "full_seed43_44.json"
        ablation = root / "ablation.json"
        _write_run_file(full_seed42, [0.96])
        _write_run_file(full_seed43_44, [0.94, 0.95])
        _write_run_file(ablation, [0.90, 0.91, 0.92])

        report = summarize(
            [
                ("Full", [full_seed42, full_seed43_44]),
                ("NoPairwise", [ablation]),
            ]
        )

        self.assertIn("| Full | 0.9500 +/- 0.0082 | +0.0000 |", report)
        self.assertIn("| NoPairwise | 0.9100 +/- 0.0082 | -0.0400 |", report)
        self.assertIn("n=3", report)
        self.assertIn("full_seed42.json + full_seed43_44.json", report)


if __name__ == "__main__":
    unittest.main()
