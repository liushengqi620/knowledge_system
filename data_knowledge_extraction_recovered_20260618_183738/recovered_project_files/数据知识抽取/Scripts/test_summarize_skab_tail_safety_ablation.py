from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_skab_tail_safety_ablation import build_tail_safety_report, render_markdown, write_tail_safety_report


def _write_run(path: Path, *, seed: int, class0: float, class1: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "ok",
                "seed": seed,
                "val_metrics": {
                    "per_class": {
                        "0": {"f1": class0, "support": 10},
                        "1": {"f1": class1, "support": 5},
                    }
                },
            }
        ),
        encoding="utf-8",
    )


class SummarizeSkabTailSafetyAblationTest(unittest.TestCase):
    def test_tail_safety_replay_isolates_low_tail_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_root = root / "runs"
            for seed in [42, 43, 44]:
                _write_run(run_root / "no_mechanism" / f"seed{seed}.json", seed=seed, class0=0.80, class1=0.70)
                _write_run(
                    run_root / "candidate" / f"seed{seed}.json",
                    seed=seed,
                    class0=0.86,
                    class1=0.64,
                )
            matrix = root / "matrix.json"
            matrix.write_text(
                json.dumps(
                    {
                        "output_root": str(run_root),
                        "summary": [
                            {
                                "variant": "no_mechanism",
                                "role": "baseline",
                                "n_runs": 3,
                                "test_macro_f1_mean": 0.70,
                                "test_macro_f1_std": 0.01,
                                "mean_val_gain_vs_baseline": 0.0,
                                "min_seed_val_gain_vs_baseline": 0.0,
                                "low_tail_val_f1_gain": 0.0,
                                "low_tail_quantile": 0.10,
                                "baseline_path_jaccard": 1.0,
                                "certificate_thresholds": {"max_low_tail_f1_drop": 0.02},
                            },
                            {
                                "variant": "candidate",
                                "role": "mechanism_gate",
                                "n_runs": 3,
                                "test_macro_f1_mean": 0.76,
                                "test_macro_f1_std": 0.01,
                                "mean_val_gain_vs_baseline": 0.03,
                                "min_seed_val_gain_vs_baseline": 0.02,
                                "low_tail_val_f1_gain": -0.06,
                                "low_tail_quantile": 0.10,
                                "baseline_path_jaccard": 0.5,
                                "certificate_thresholds": {
                                    "min_mean_val_gain": 0.0,
                                    "max_seed_val_drop": 0.01,
                                    "min_baseline_path_jaccard": 0.0,
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_tail_safety_report([matrix])

        candidate = [row for row in report["rows"] if row["variant"] == "candidate"][0]
        self.assertFalse(candidate["guarded_admitted"])
        self.assertTrue(candidate["no_tail_admitted"])
        self.assertTrue(candidate["admission_changed_by_removing_h"])
        self.assertEqual(len(candidate["per_seed_low_tail"]), 3)

    def test_write_tail_safety_report_outputs_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            written = write_tail_safety_report(output_dir)

            self.assertEqual(
                set(written),
                {
                    output_dir / "skab_tail_safety_policy_replay.json",
                    output_dir / "skab_tail_safety_policy_replay.md",
                },
            )
            payload = json.loads((output_dir / "skab_tail_safety_policy_replay.json").read_text(encoding="utf-8"))
            self.assertIn("status", payload)
            markdown = render_markdown(payload)
            self.assertIn("SKAB Tail-Safety Policy Replay", markdown)


if __name__ == "__main__":
    unittest.main()
