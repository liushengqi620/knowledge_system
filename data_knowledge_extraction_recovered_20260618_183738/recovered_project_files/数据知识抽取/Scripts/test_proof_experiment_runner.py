from __future__ import annotations

import json
import uuid
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from proof_experiment_runner import (
    apply_robustness_transform,
    build_proof_experiment_specs,
    run_proof_experiments,
    summarize_runs,
)


class ProofExperimentRunnerTests(unittest.TestCase):
    def test_quick_specs_cover_core_proof_categories(self) -> None:
        specs = build_proof_experiment_specs("quick")
        categories = {spec.category for spec in specs}
        names = {spec.name for spec in specs}

        self.assertIn("main", categories)
        self.assertIn("event_delay", categories)
        self.assertIn("knowledge_graph", categories)
        self.assertIn("dynamic_graph", categories)
        self.assertIn("robustness", categories)
        self.assertIn("full_model", names)
        self.assertIn("no_event_mil_point_label", names)
        self.assertIn("missing_10pct", names)

    def test_robustness_transform_is_deterministic_and_respects_feature_cols(self) -> None:
        df = pd.DataFrame(
            {
                "a": np.arange(20, dtype=float),
                "b": np.arange(20, dtype=float) * 2.0,
                "label": [0, 1] * 10,
            }
        )

        first = apply_robustness_transform(df, ["a", "b"], {"kind": "missing", "rate": 0.2}, seed=7)
        second = apply_robustness_transform(df, ["a", "b"], {"kind": "missing", "rate": 0.2}, seed=7)

        self.assertTrue(first[["a", "b"]].equals(second[["a", "b"]]))
        self.assertTrue(first["label"].equals(df["label"]))
        self.assertGreater(int(first[["a", "b"]].isna().sum().sum()), 0)

    def test_summarize_runs_extracts_prediction_event_and_evidence_metrics(self) -> None:
        rows = [
            {
                "experiment_name": "full_model",
                "category": "main",
                "status": "ok",
                "pr_auc_test": 0.8,
                "f1_defect_test_tuned": 0.6,
                "precision_defect_test_tuned": 0.5,
                "recall_defect_test_tuned": 0.75,
                "roc_auc_test": 0.85,
                "mil_event_metrics": {"enabled": True, "bag_recall": 0.7, "false_alarm_rate_point": 0.1},
                "fault_outputs": {"mode": "auxiliary_subfault_heads"},
                "knowledge_candidate_registry": {"updated": 3},
                "dynamic_graph_evidence": {"edge_evidence_sources": ["rule_prior", "task_occlusion"]},
            },
            {
                "experiment_name": "full_model",
                "category": "main",
                "status": "ok",
                "pr_auc_test": 0.6,
                "f1_defect_test_tuned": 0.4,
                "precision_defect_test_tuned": 0.3,
                "recall_defect_test_tuned": 0.5,
                "roc_auc_test": 0.65,
                "mil_event_metrics": {"enabled": True, "bag_recall": 0.5, "false_alarm_rate_point": 0.2},
                "fault_outputs": {"mode": "auxiliary_subfault_heads"},
                "knowledge_candidate_registry": {"updated": 1},
                "dynamic_graph_evidence": {"edge_evidence_sources": ["rule_prior"]},
            },
        ]

        summary = summarize_runs(rows)

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["experiment_name"], "full_model")
        self.assertAlmostEqual(summary[0]["pr_auc_test_mean"], 0.7)
        self.assertAlmostEqual(summary[0]["mil_bag_recall_mean"], 0.6)
        self.assertAlmostEqual(summary[0]["mil_false_alarm_rate_point_mean"], 0.15)
        self.assertEqual(summary[0]["candidate_registry_updated_total"], 4)
        self.assertEqual(summary[0]["evidence_source_count_max"], 2)

    def test_run_proof_experiments_with_fake_runner_saves_json_and_csv(self) -> None:
        df = pd.DataFrame({"a": np.arange(30, dtype=float), "b": np.arange(30, dtype=float) * 0.1})
        root = Path(__file__).resolve().parents[1]
        output_path = root / "knowledge_exports" / "_test_proof_experiments" / f"{uuid.uuid4().hex}.json"

        def fake_runner(run_df, feature_cols, cfg, project_root):
            return {
                "status": "ok",
                "pr_auc_test": 0.7 + 0.01 * int(cfg["random_state"]),
                "f1_defect_test_tuned": 0.6,
                "precision_defect_test_tuned": 0.5,
                "recall_defect_test_tuned": 0.8,
                "roc_auc_test": 0.75,
                "mil_event_metrics": {"enabled": bool(cfg.get("paper_event_supervision_enabled", True)), "bag_recall": 0.5},
                "fault_outputs": {"mode": "auxiliary_subfault_heads"},
                "knowledge_candidate_registry": {"updated": 2},
                "dynamic_graph_evidence": {"edge_evidence_sources": ["rule_prior"]},
            }

        try:
            out = run_proof_experiments(
                df,
                ["a", "b"],
                {
                    "random_state": 1,
                    "paper_experiment_seeds": [1],
                    "proof_experiment_output_path": str(output_path),
                    "paper_mlp_epochs": 1,
                },
                root,
                profile="quick",
                max_rows=20,
                paper_runner=fake_runner,
            )

            self.assertEqual(out["status"], "ok")
            self.assertTrue(output_path.is_file())
            self.assertTrue(output_path.with_suffix(".summary.csv").is_file())
            saved = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("runs", saved)
            self.assertIn("summary_table", saved)
            self.assertGreaterEqual(len(saved["runs"]), 5)
        finally:
            if output_path.with_suffix(".summary.csv").exists():
                output_path.with_suffix(".summary.csv").unlink()
            if output_path.exists():
                output_path.unlink()
            if output_path.parent.exists() and not any(output_path.parent.iterdir()):
                output_path.parent.rmdir()


if __name__ == "__main__":
    unittest.main()
