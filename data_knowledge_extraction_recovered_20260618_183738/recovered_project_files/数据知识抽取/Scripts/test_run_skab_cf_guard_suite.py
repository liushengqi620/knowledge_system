from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path

from Scripts.run_skab_cf_guard_suite import SuiteConfig, build_jobs, render_summary


class RunSkabCfGuardSuiteTest(unittest.TestCase):
    def test_builds_resume_safe_jobs_and_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / f"cf_guard_suite_{uuid.uuid4().hex}"
            exports = root / "exports"
            exports.mkdir(parents=True, exist_ok=True)
            source = exports / "public_benchmark_skab_dynamic_llm_api_seed42_e8_learned_reliability_probe2_t045_k4.json"
            source.write_text('{"dynamic_edges": []}', encoding="utf-8")
            done = exports / "public_benchmark_skab_dynamic_llm_api_seed42_e3_cf_guard_reverse_lag_random_probe1.json"
            done.write_text('{"status": "ok"}', encoding="utf-8")

            config = SuiteConfig(
                exports_dir=exports,
                seeds=(42,),
                sequence_epochs=3,
                probe_epochs=1,
                guard_modes=("reverse_direction", "lag_shift", "random_target"),
                min_macro_drop=0.01,
                edge_reliability_threshold=0.45,
                max_far_increase_percent=1.0,
                hidden_dim=32,
                batch_size=512,
            )

            jobs = build_jobs(config)

            self.assertEqual(len(jobs), 1)
            self.assertTrue(jobs[0].is_complete)
            self.assertIn("--edge-counterfactual-guard-modes", jobs[0].command)
            self.assertIn("reverse_direction", jobs[0].command)
            self.assertIn("lag_shift", jobs[0].command)
            self.assertIn("random_target", jobs[0].command)
            self.assertEqual(jobs[0].source_edges_file, source)
            self.assertEqual(jobs[0].output_file, done)

    def test_missing_source_edges_file_falls_back_to_live_api_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exports = Path(tmpdir) / "exports"
            exports.mkdir(parents=True, exist_ok=True)
            config = SuiteConfig(
                exports_dir=exports,
                seeds=(42,),
                sequence_epochs=3,
                probe_epochs=1,
                guard_modes=("reverse_direction",),
                min_macro_drop=0.01,
                edge_reliability_threshold=0.45,
                max_far_increase_percent=1.0,
                hidden_dim=32,
                batch_size=512,
            )

            jobs = build_jobs(config)

            self.assertFalse(jobs[0].source_edges_file.exists())
            self.assertNotIn("--dynamic-edges-file", jobs[0].command)

    def test_summary_reports_cf_guard_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / f"cf_guard_summary_{uuid.uuid4().hex}"
            exports = root / "exports"
            exports.mkdir(parents=True, exist_ok=True)
            source = exports / "public_benchmark_skab_dynamic_llm_api_seed42_e8_learned_reliability_probe2_t045_k4.json"
            source.write_text('{"dynamic_edges": []}', encoding="utf-8")
            result = exports / "public_benchmark_skab_dynamic_llm_api_seed42_e3_cf_guard_reverse_probe1.json"
            result.write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "seed": 42,
                        "baseline": {"metrics": {"macro_f1": 0.86}},
                        "dynamic_llm_kg": {
                            "metrics": {"macro_f1": 0.87},
                            "protocol": {"binary": {"f1": 0.83, "far_percent": 12.0, "mar_percent": 11.0}},
                        },
                        "macro_f1_delta": 0.01,
                        "edge_policy": {
                            "n_input_edges": 4,
                            "n_kept_edges": 1,
                            "validation_macro_f1_gain": 0.02,
                            "n_rejected_by_validation_gain_guard": 0,
                            "n_rejected_by_far_guard": 2,
                            "n_rejected_by_counterfactual_guard": 1,
                            "counterfactual_guard_modes": ["reverse_direction"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            config = SuiteConfig(
                exports_dir=exports,
                seeds=(42,),
                sequence_epochs=3,
                probe_epochs=1,
                guard_modes=("reverse_direction",),
                min_macro_drop=0.01,
                edge_reliability_threshold=0.45,
                max_far_increase_percent=1.0,
                hidden_dim=32,
                batch_size=512,
            )

            report = render_summary(build_jobs(config))

            self.assertIn("# SKAB CF-Guarded Admission Suite", report)
            self.assertIn("0.8700", report)
            self.assertIn("+0.0100", report)
            self.assertIn("CF Rejects", report)
            self.assertIn("Val Gain", report)
            self.assertIn("resume-safe", report)


if __name__ == "__main__":
    unittest.main()
