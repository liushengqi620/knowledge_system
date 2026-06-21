from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_skab_cf_subset_smoke import build_summary, render_markdown, write_summary


def _write_result(path: Path, *, seed: int, macro: float, gain: float, cfmax: float = 0.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "ok",
                "seed": seed,
                "macro_f1_delta": gain,
                "dynamic_llm_kg": {"metrics": {"macro_f1": macro}},
                "dynamic_edges": [{"source": "A", "target": "B", "lag": 1}],
                "edge_policy": {
                    "admitted": True,
                    "n_kept_edges": 1,
                    "validation_macro_f1_gain": 0.02,
                    "counterfactual_max_macro_drop": cfmax,
                    "counterfactual_passing_modes": ["reverse_direction"] if cfmax else [],
                },
            }
        ),
        encoding="utf-8",
    )


class SummarizeSkabCfSubsetSmokeTest(unittest.TestCase):
    def test_build_summary_aggregates_three_branches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            branch_dirs = {
                "cf_standard": root / "cf",
                "no_cf": root / "no_cf",
                "cf_consistency": root / "cf_consistency",
            }
            for branch, directory in branch_dirs.items():
                _write_result(directory / "seed42.json", seed=42, macro=0.8, gain=0.02, cfmax=0.03 if branch != "no_cf" else 0.0)

            report = build_summary(seeds=[42], branch_dirs=branch_dirs)

        self.assertEqual(report["status"], "complete_smoke")
        self.assertEqual(report["aggregates"]["cf_standard"]["n"], 1)
        self.assertIn("cf_minus_no_cf_test_macro_f1", report)
        self.assertIn("CF/no-CF", render_markdown(report))

    def test_write_summary_outputs_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            written = write_summary(Path(tmpdir))

            self.assertEqual(len(written), 2)
            self.assertTrue((Path(tmpdir) / "skab_cf_subset_smoke_summary.json").exists())


if __name__ == "__main__":
    unittest.main()
