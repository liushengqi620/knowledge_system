from __future__ import annotations

import json
import os
import re
import shutil
import unittest
from pathlib import Path

from protocol_aligned_external_baseline_runner import build_runner_plan, main


def _fs_path(path: Path | str) -> str:
    text = str(Path(path).resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


class ProtocolAlignedExternalBaselineRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("knowledge_exports") / "_tmp_protocol_aligned_external_runner_test"
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_builds_executable_tep_patchtst_plan_with_claim_boundary(self) -> None:
        plan = build_runner_plan(
            dataset="TEP",
            model="PatchTST",
            seed=42,
            protocol="matched",
            validation_only_thresholds=True,
            output=self.root / "patchtst.json",
            alignment_output=self.root / "patchtst_alignment.json",
        )

        self.assertEqual(plan["schema"], "aaai_external_baseline_protocol_runner_v1")
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["dataset"], "TEP")
        self.assertEqual(plan["normalized_model"], "patchtst")
        self.assertEqual(plan["seeds"], [42])
        self.assertTrue(plan["runner_contract"]["writes_alignment_artifact_with_hash"])
        self.assertFalse(plan["runner_contract"]["official_external_score"])
        self.assertIn("local matched-adapter artifacts only", plan["claim_boundary"])
        self.assertIn("not produce an official external", plan["claim_boundary"])
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9]{12,}", json.dumps(plan)))

    def test_dry_run_cli_writes_plan_without_training(self) -> None:
        plan_path = self.root / "dry_run_plan.json"

        main(
            [
                "--dataset",
                "TEP",
                "--model",
                "Graph WaveNet",
                "--seed",
                "42",
                "--protocol",
                "matched",
                "--validation-only-thresholds",
                "--output",
                str(self.root / "graph_wavenet.json"),
                "--alignment-output",
                str(self.root / "graph_wavenet_alignment.json"),
                "--plan-output",
                str(plan_path),
                "--dry-run",
            ]
        )

        self.assertTrue(os.path.exists(_fs_path(plan_path)))
        with open(_fs_path(plan_path), encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["normalized_model"], "graph_wavenet")
        self.assertEqual(payload["result_path"], str(self.root / "graph_wavenet.json"))
        self.assertEqual(payload["alignment_artifact_path"], str(self.root / "graph_wavenet_alignment.json"))

    def test_unsupported_pair_is_explicitly_non_executable(self) -> None:
        plan = build_runner_plan(
            dataset="SKAB",
            model="PatchTST",
            seed=42,
            protocol="matched",
            validation_only_thresholds=True,
        )

        self.assertEqual(plan["status"], "unsupported_protocol_pair")
        self.assertFalse(plan["supported_local_adapter"])
        self.assertIn("No faithful local adapter runner", plan["unsupported_reason"])
        self.assertFalse(plan["runner_contract"]["official_external_score"])

    def test_skab_anomaly_transformer_plan_is_executable_local_adapter(self) -> None:
        plan = build_runner_plan(
            dataset="SKAB",
            model="Anomaly Transformer",
            seed=42,
            protocol="matched",
            validation_only_thresholds=True,
            output=self.root / "skab_anomaly_transformer.json",
            alignment_output=self.root / "skab_anomaly_transformer_alignment.json",
        )

        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["dataset"], "SKAB")
        self.assertEqual(plan["normalized_model"], "anomaly_transformer")
        self.assertTrue(plan["supported_local_adapter"])
        self.assertIn("dataset_root", plan["execution"])
        self.assertFalse(plan["runner_contract"]["official_external_score"])


if __name__ == "__main__":
    unittest.main()
