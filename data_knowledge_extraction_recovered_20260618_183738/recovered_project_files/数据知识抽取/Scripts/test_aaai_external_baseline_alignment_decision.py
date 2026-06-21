from __future__ import annotations

import json
import os
import re
import shutil
import unittest
from pathlib import Path

from aaai_experiment_execution_manifest import build_manifest
from aaai_external_baseline_alignment_decision import (
    build_alignment_decision_payload,
    build_external_baseline_alignment_decision,
    render_alignment_decision_markdown,
)


def _fs_path(path: Path | str) -> str:
    text = str(Path(path).resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


class AaaiExternalBaselineAlignmentDecisionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = Path("knowledge_exports") / "_tmp_external_alignment_decision_test"
        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_payload_covers_official_source_adapted_controls(self) -> None:
        payload = build_alignment_decision_payload(manifest=build_manifest())
        rows = {item["name"]: item for item in payload["rows"]}

        self.assertEqual(set(rows), {"PatchTST", "Anomaly Transformer", "Graph WaveNet"})
        self.assertEqual(payload["overall_status"], "official_source_adapted_controls_materialized")
        self.assertFalse(payload["missing_manifest_rows"])
        self.assertFalse(payload["pending_exact_external_score_rows"])
        for name, row in rows.items():
            self.assertEqual(row["manifest_status"], "materialized_official_source_adapted_control", name)
            self.assertEqual(row["comparison_admissibility"], "not_admissible_as_official_external_score", name)
            self.assertIn(row["local_adapter_status"], {"local_three_seed_probe_available", "local_probe_available", "not_materialized"}, name)
            self.assertIn("local_adapter_artifacts", row, name)
            self.assertIn("official_repo_snapshot", row, name)
            self.assertIn("artifact", row["official_repo_snapshot"], name)
            self.assertFalse(row["official_repo_snapshot"]["official_external_score"], name)
            self.assertIn("official_repo_checkout", row, name)
            self.assertIn("artifact", row["official_repo_checkout"], name)
            self.assertFalse(row["official_repo_checkout"]["official_external_score"], name)
            self.assertTrue(row["paper_url"].startswith("https://"), name)
            self.assertTrue(row["repo_url"].startswith("https://github.com/"), name)
            self.assertGreaterEqual(len(row["protocol_mismatches"]), 3, name)
            self.assertGreaterEqual(len(row["runner_contract"]), 3, name)

        self.assertIn("patch", " ".join(rows["PatchTST"]["core_mechanism"]).lower())
        self.assertGreaterEqual(len(rows["PatchTST"]["local_adapter_artifacts"]), 2)
        patch_artifact_paths = {item["path"] for item in rows["PatchTST"]["local_adapter_artifacts"]}
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_probe.json",
            patch_artifact_paths,
        )
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_budget_probe.json",
            patch_artifact_paths,
        )
        self.assertIn("association", " ".join(rows["Anomaly Transformer"]["core_mechanism"]).lower())
        anomaly_artifact_paths = {
            item["path"] for item in rows["Anomaly Transformer"]["local_adapter_artifacts"]
        }
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/skab_anomaly_transformer_3seed_probe.json",
            anomaly_artifact_paths,
        )
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_adapter/anomaly_transformer_official_skab_adapter.json",
            anomaly_artifact_paths,
        )
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_probe.json",
            anomaly_artifact_paths,
        )
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json",
            anomaly_artifact_paths,
        )
        self.assertIn(
            "knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_skab_3seed_alignment_artifact.json",
            anomaly_artifact_paths,
        )
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/skab_anomaly_transformer_smoke.json",
            anomaly_artifact_paths,
        )
        self.assertIn("adaptive", " ".join(rows["Graph WaveNet"]["core_mechanism"]).lower())
        graph_artifact_paths = {item["path"] for item in rows["Graph WaveNet"]["local_adapter_artifacts"]}
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_probe.json",
            graph_artifact_paths,
        )
        self.assertIn(
            "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_budget_probe.json",
            graph_artifact_paths,
        )

    def test_writes_json_and_markdown_with_safe_claim_boundary(self) -> None:
        written = build_external_baseline_alignment_decision(
            self.output_dir,
            manifest=build_manifest(),
        )
        expected = {
            self.output_dir / "aaai_external_baseline_alignment_decision.json",
            self.output_dir / "aaai_external_baseline_alignment_decision.md",
        }
        self.assertEqual(set(written), expected)
        for path in expected:
            self.assertTrue(os.path.exists(_fs_path(path)), path)
            self.assertGreater(os.stat(_fs_path(path)).st_size, 1000, path)

        with open(_fs_path(self.output_dir / "aaai_external_baseline_alignment_decision.json"), encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["claim_gate"].count("official external comparison scores"), 1)

        markdown = render_alignment_decision_markdown(payload)
        self.assertIn("AAAI External Baseline Alignment Decision", markdown)
        self.assertIn("https://openreview.net/forum?id=Jbdc0vTOcol", markdown)
        self.assertIn("https://github.com/thuml/Anomaly-Transformer", markdown)
        self.assertIn("https://www.ijcai.org/proceedings/2019/264", markdown)
        self.assertIn("Official repo snapshot", markdown)
        self.assertIn("Official repo checkout", markdown)
        self.assertIn("not_admissible_as_official_external_score", markdown)
        self.assertNotIn("SOTA" + "-candidate", markdown)
        self.assertNotIn("camera" + "-ready", markdown)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9]{12,}", markdown))


if __name__ == "__main__":
    unittest.main()
