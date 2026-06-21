from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path

from aaai_formal_public_protocol import _fs_path, build_command, build_protocol, formal_run_specs, render_markdown, write_protocol


class AAAIFormalPublicProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = Path("knowledge_exports") / "_tmp_formal_public_protocol_test"
        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_specs_include_skab_strong_llm_gate_and_cmapss_rul(self) -> None:
        specs = {spec.name: spec for spec in formal_run_specs()}

        self.assertEqual(
            set(specs),
            {
                "skab_strong_anchor",
                "skab_llm_condition_candidate_gate",
                "cmapss_original_rul_anchor",
                "cmapss_rul_direct_regime_tempmix",
                "cmapss_rul_direct_regime_bitempmix",
                "cmapss_rul_anchorpath_bigru_cls020",
            },
        )
        self.assertIn("--window-size", specs["skab_strong_anchor"].flags)
        self.assertIn("48", specs["skab_strong_anchor"].flags)
        self.assertIn("--epochs", specs["skab_strong_anchor"].flags)
        self.assertIn("40", specs["skab_strong_anchor"].flags)
        self.assertIn("--llm-condition-verifier-target", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("candidate_gate", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("--llm-condition-verifier-weight", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("0.05", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("--use-candidate-prior-admission", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("--candidate-prior-admission-target", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("proposal_feature", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("--candidate-coverage-fraction", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("0.10", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("--use-llm-condition-verifier-validation-admission", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("--llm-condition-verifier-min-val-gain", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertIn("0.01", specs["skab_llm_condition_candidate_gate"].flags)
        self.assertEqual(specs["cmapss_original_rul_anchor"].target, "rul")
        self.assertEqual(specs["cmapss_original_rul_anchor"].expected_metric, "rul_rmse")
        self.assertIn("--cmapss-target", specs["cmapss_original_rul_anchor"].flags)
        self.assertIn("rul", specs["cmapss_original_rul_anchor"].flags)
        self.assertEqual(specs["cmapss_original_rul_anchor"].output_subdir, "cmapss_original_rul_terminal_anchor_w48_e20")
        self.assertEqual(specs["cmapss_rul_direct_regime_tempmix"].target, "rul")
        self.assertEqual(specs["cmapss_rul_direct_regime_tempmix"].expected_metric, "rul_rmse")
        self.assertIn("--rul-loss-weight", specs["cmapss_rul_direct_regime_tempmix"].flags)
        self.assertIn("--use-regime-prototype-residuals", specs["cmapss_rul_direct_regime_tempmix"].flags)
        self.assertIn("--use-temporal-mixer", specs["cmapss_rul_direct_regime_tempmix"].flags)
        self.assertEqual(specs["cmapss_rul_direct_regime_bitempmix"].target, "rul")
        self.assertIn("--temporal-encoder-mode", specs["cmapss_rul_direct_regime_bitempmix"].flags)
        self.assertIn("multi_scale_bidirectional", specs["cmapss_rul_direct_regime_bitempmix"].flags)
        self.assertEqual(specs["cmapss_rul_anchorpath_bigru_cls020"].target, "rul")
        self.assertIn("--temporal-mixer-type", specs["cmapss_rul_anchorpath_bigru_cls020"].flags)
        self.assertIn("bigru", specs["cmapss_rul_anchorpath_bigru_cls020"].flags)
        self.assertIn("--classification-loss-weight", specs["cmapss_rul_anchorpath_bigru_cls020"].flags)
        self.assertIn("0.20", specs["cmapss_rul_anchorpath_bigru_cls020"].flags)
        self.assertIn("--use-rul-temporal-anchor-fusion", specs["cmapss_rul_anchorpath_bigru_cls020"].flags)

    def test_build_command_uses_run_public_ms_gse_rpf_experiment(self) -> None:
        spec = {item.name: item for item in formal_run_specs()}["skab_llm_condition_candidate_gate"]
        command = build_command(spec, seeds="42,43,44", output_root=Path("runs"), python_executable="python", device="cpu")
        joined = " ".join(command)

        self.assertIn("Scripts", command[2])
        self.assertIn("run_public_ms_gse_rpf_experiment.py", command[2])
        self.assertIn("--ready-root knowledge_exports/public_benchmark_ready_llm_live_skab", joined)
        self.assertIn("--seeds 42,43,44", joined)
        self.assertIn("--llm-condition-verifier-target candidate_gate", joined)

    def test_protocol_writes_markdown_and_keeps_smoke_out_of_formal_claims(self) -> None:
        protocol = build_protocol(seeds="42,43,44", output_root=self.output_dir / "runs", device="cpu")
        written = write_protocol(protocol, self.output_dir)
        report = render_markdown(protocol)

        self.assertEqual(
            {path.name for path in written},
            {"aaai_formal_public_protocol.json", "aaai_formal_public_protocol.md"},
        )
        self.assertIn("C-MAPSS paper results use original RUL regression", report)
        self.assertIn("Smoke runs are debugging evidence only", report)
        self.assertIn("skab_llm_condition_candidate_gate", report)
        self.assertNotIn("degradation-stage labels from RUL windows", report)
        self.assertNotIn("sk-", report)

    def test_only_filters_formal_runs_and_rejects_unknown_names(self) -> None:
        protocol = build_protocol(
            seeds="42,43,44",
            output_root=self.output_dir / "runs",
            device="cpu",
            only=["skab_strong_anchor"],
        )

        self.assertEqual(protocol["selected_runs"], ["skab_strong_anchor"])
        self.assertEqual([row["name"] for row in protocol["runs"]], ["skab_strong_anchor"])
        with self.assertRaises(ValueError):
            formal_run_specs(only=["missing_protocol"])

    def test_status_detects_completed_seed_files(self) -> None:
        spec = {item.name: item for item in formal_run_specs()}["skab_strong_anchor"]
        output_root = self.output_dir / "runs"
        run_dir = output_root / spec.output_subdir
        os.makedirs(_fs_path(run_dir), exist_ok=True)
        result_path = run_dir / "ms_gse_rpf_skab_anomaly_full_prior-none_seed42.json"
        with open(_fs_path(result_path), "w", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "seed": 42,
                        "status": "ok",
                        "primary_test_metrics": {"macro_f1": 0.8123},
                    }
                )
            )

        protocol = build_protocol(seeds="42,43", output_root=output_root, device="cpu", only=["skab_strong_anchor"])
        status = protocol["runs"][0]["status"]

        self.assertFalse(status["complete"])
        self.assertEqual(status["completed_seeds"], [42])
        self.assertEqual(status["missing_seeds"], [43])
        self.assertAlmostEqual(status["metric_mean"], 0.8123)


if __name__ == "__main__":
    unittest.main()
