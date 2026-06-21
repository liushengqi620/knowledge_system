from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from summarize_skab_msfg_pruning_ablation import summarize


class SummarizeSkabMsfgPruningAblationTest(unittest.TestCase):
    def test_summarizes_modes_and_deltas_against_original(self) -> None:
        root = Path.cwd() / "tmp_tests" / f"skab_pruning_summary_{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        path = root / "runs.json"
        path.write_text(
            json.dumps(
                {
                    "runs": [
                        {
                            "seed": 1,
                            "mode": "original_full_msfg",
                            "macro_f1": 0.50,
                            "point_adjusted_f1": 0.60,
                            "far_percent": 20.0,
                            "fusion": {"n_fused_edges": 10},
                        },
                        {
                            "seed": 2,
                            "mode": "original_full_msfg",
                            "macro_f1": 0.70,
                            "point_adjusted_f1": 0.80,
                            "far_percent": 10.0,
                            "fusion": {"n_fused_edges": 12},
                        },
                        {
                            "seed": 1,
                            "mode": "full_pruned_kg",
                            "macro_f1": 0.80,
                            "point_adjusted_f1": 0.85,
                            "far_percent": 5.0,
                            "fusion": {"n_fused_edges": 8},
                        },
                        {
                            "seed": 2,
                            "mode": "full_pruned_kg",
                            "macro_f1": 0.90,
                            "point_adjusted_f1": 0.95,
                            "far_percent": 4.0,
                            "fusion": {"n_fused_edges": 8},
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        report = summarize([path])

        self.assertIn("original_full_msfg", report)
        self.assertIn("0.6000 +/- 0.1000", report)
        self.assertIn("full_pruned_kg", report)
        self.assertIn("0.8500 +/- 0.0500", report)
        self.assertIn("+0.2500", report)
        self.assertIn("n=2", report)


if __name__ == "__main__":
    unittest.main()
