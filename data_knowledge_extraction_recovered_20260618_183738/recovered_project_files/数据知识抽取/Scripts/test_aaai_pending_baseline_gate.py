from __future__ import annotations

import json
import os
import re
import shutil
import unittest
from pathlib import Path

from aaai_experiment_execution_manifest import build_manifest
from aaai_pending_baseline_gate import build_pending_baseline_gate, render_pending_baseline_markdown


def _fs_path(path: Path | str) -> str:
    text = str(Path(path).resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


class AaaiPendingBaselineGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = Path("knowledge_exports") / "_tmp_aaai_pending_baseline_gate_test"
        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_build_gate_writes_pending_alignment_artifacts(self) -> None:
        written = build_pending_baseline_gate(
            output_dir=self.output_dir,
            manifest=build_manifest(),
        )

        expected = {
            self.output_dir / "aaai_pending_baseline_gate.json",
            self.output_dir / "aaai_pending_baseline_gate.md",
        }
        self.assertEqual(set(written), expected)
        for path in expected:
            self.assertTrue(os.path.exists(_fs_path(path)), path)
            self.assertGreater(os.stat(_fs_path(path)).st_size, 1000, path)

        with open(_fs_path(self.output_dir / "aaai_pending_baseline_gate.json"), encoding="utf-8") as handle:
            payload = json.load(handle)
        pending = {item["name"]: item for item in payload["pending_baselines"]}
        controls = {item["name"]: item for item in payload["materialized_external_controls"]}
        self.assertFalse(pending)
        self.assertEqual(set(controls), {"PatchTST", "Anomaly Transformer", "Graph WaveNet"})
        self.assertEqual(payload["overall_status"], "no_pending_baselines")
        self.assertIn("official-source adapted controls", payload["claim_rule"])

        for name, item in controls.items():
            self.assertEqual(item["runner_status"], "official_source_adapted_budget_probe_available", name)
            self.assertEqual(item["score_status"], "matched_protocol_control_scored", name)
            self.assertFalse(item["official_external_score"], name)
            self.assertIn("claim_gate", item)
            self.assertIn("official_task", item)
            self.assertIn("official_paper_url", item)
            self.assertIn("official_repo_url", item)
            self.assertIn("official_repo_snapshot_status", item)
            self.assertIn("official_repo_checkout_status", item)
            self.assertIn("official_repo_protocol_wrapper_status", item)
            self.assertIn("comparison_admissibility", item)
            self.assertIn("score_artifact", item)
            self.assertIn("Scripts/", item["command_template"])

    def test_markdown_is_submission_safe_and_actionable(self) -> None:
        payload = {
            "overall_status": "blocked_by_unimplemented_external_runners",
            "claim_rule": "pending baselines are unscored alignment obligations",
            "pending_baselines": [
                {
                    "name": "PatchTST",
                    "family": "temporal sequence",
                    "official_task": "long-term time-series forecasting and representation learning",
                    "official_repo_snapshot_status": "repo_head_resolved",
                    "official_repo_checkout_status": "checkout_verified",
                    "datasets": ["TEP", "SKAB"],
                    "runner_status": "blocked_unimplemented_runner",
                    "score_status": "unscored",
                    "checks": ["protocol_alignment_required"],
                    "input_contract": "same train/validation/test units",
                    "output_contract": "seed-level predictions, config hash",
                    "claim_gate": "no public comparison claim",
                    "alignment_artifact": "knowledge_exports/aaai_external_baseline_alignment_decision/aaai_external_baseline_alignment_decision.json",
                    "command_template": "python Scripts/protocol_aligned_external_baseline_runner.py --dataset TEP --model PatchTST",
                    "blocking_reasons": ["implementation_required"],
                    "required_runner_contract": [
                        "accept declared dataset and seed arguments",
                        "write validation and test predictions",
                    ],
                }
            ],
            "materialized_external_controls": [],
        }

        markdown = render_pending_baseline_markdown(payload)

        self.assertIn("AAAI Pending Baseline Alignment Gate", markdown)
        self.assertIn("PatchTST", markdown)
        self.assertIn("repo_head_resolved", markdown)
        self.assertIn("checkout_verified", markdown)
        self.assertIn("blocked_unimplemented_runner", markdown)
        self.assertIn("seed-level predictions", markdown)
        self.assertIn("config hash", markdown)
        self.assertIn("protocol_aligned_external_baseline_runner.py", markdown)
        self.assertIn("no public comparison claim", markdown)
        self.assertNotIn("SOTA" + "-candidate", markdown)
        self.assertNotIn("camera" + "-ready", markdown)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9]{12,}", markdown))


if __name__ == "__main__":
    unittest.main()
