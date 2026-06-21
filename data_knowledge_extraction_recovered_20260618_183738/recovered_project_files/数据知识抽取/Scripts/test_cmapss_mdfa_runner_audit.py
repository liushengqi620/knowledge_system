from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmapss_mdfa_runner_audit import build_cmapss_mdfa_runner_audit, render_markdown, write_cmapss_mdfa_runner_audit


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class CmapssMdfaRunnerAuditTest(unittest.TestCase):
    def test_audit_accepts_smoke_archive_but_blocks_full_reproduction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            runner = root / "run_cmapss_mdfa_source_matched.py"
            runner.write_text("print('runner')\n", encoding="utf-8")
            _write_json(
                run_dir / "cmapss_mdfa_source_matched_summary.json",
                {
                    "status": "source_matched_candidate_not_exact_reproduction",
                    "n_prediction_records": 707,
                    "overall_metrics": {"rul_rmse": 55.0, "rul_score": 123.0},
                    "subset_seed_rows": [
                        {"subset": subset, "seed": 42}
                        for subset in ("FD001", "FD002", "FD003", "FD004")
                    ],
                },
            )
            _write_json(
                run_dir / "cmapss_mdfa_source_matched_seed42.json",
                {
                    "seed": 42,
                    "subsets": [
                        {
                            "subset": subset,
                            "test_windows": n,
                            "train_windows": 512,
                            "alignment_status": "source_matched_candidate_not_exact_reproduction",
                            "diagnostics": {
                                "epochs": 1,
                                "batch_size": 32,
                                "learning_rate": 0.0001,
                                "dropout": 0.3,
                                "dilation_rates": [1, 2, 4],
                            },
                            "rul_prediction_records": [{} for _ in range(n)],
                        }
                        for subset, n in {"FD001": 100, "FD002": 259, "FD003": 100, "FD004": 248}.items()
                    ],
                },
            )

            payload = build_cmapss_mdfa_runner_audit(run_dir, runner)

            self.assertEqual("smoke_runner_materialized_full_budget_pending", payload["status"])
            self.assertTrue(payload["gates"]["runner_code_present"])
            self.assertTrue(payload["gates"]["smoke_all_subsets_present"])
            self.assertTrue(payload["gates"]["smoke_terminal_prediction_records_present"])
            self.assertTrue(payload["gates"]["smoke_claim_safe"])
            self.assertFalse(payload["gates"]["full_three_seed_archive_present"])
            self.assertFalse(payload["gates"]["full_source_budget_100epoch_present"])
            self.assertFalse(payload["gates"]["safe_to_promote_mdfa_to_exact_reproduction"])
            self.assertIn("full_source_budget_100epoch_present", payload["missing_gates"])

    def test_writer_and_markdown_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            run_dir = Path(tmp) / "run"
            runner = Path(tmp) / "runner.py"
            runner.write_text("# runner\n", encoding="utf-8")
            _write_json(
                run_dir / "cmapss_mdfa_source_matched_summary.json",
                {
                    "status": "source_matched_candidate_not_exact_reproduction",
                    "n_prediction_records": 0,
                    "subset_seed_rows": [],
                },
            )
            written = write_cmapss_mdfa_runner_audit(output_dir, run_dir, runner)
            self.assertEqual(
                {output_dir / "cmapss_mdfa_runner_audit.json", output_dir / "cmapss_mdfa_runner_audit.md"},
                set(written),
            )
            payload = json.loads((output_dir / "cmapss_mdfa_runner_audit.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
            self.assertIn("C-MAPSS MDFA Runner Audit", markdown)
            self.assertIn("smoke_runner_materialized_full_budget_pending", markdown)
            self.assertIn("safe_to_promote_mdfa_to_exact_reproduction", markdown)
            self.assertNotIn("official C-MAPSS SOTA is proven", markdown)


if __name__ == "__main__":
    unittest.main()
