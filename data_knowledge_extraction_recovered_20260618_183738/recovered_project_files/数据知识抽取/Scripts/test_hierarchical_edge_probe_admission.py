from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path

from hierarchical_edge_probe_admission import (
    admit_edges_from_probe_results,
    build_default_hierarchical_artifact,
    build_frozen_tep_candidate_pool,
    build_probe_plan,
    evaluate_probe_row,
)


def _fs_path(path: Path | str) -> str:
    text = str(Path(path).resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


class HierarchicalEdgeProbeAdmissionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = Path("knowledge_exports") / "_tmp_hierarchical_edge_probe_admission_test"
        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_frozen_pool_and_probe_plan_include_source_target_lag_and_single_levels(self) -> None:
        edges = build_frozen_tep_candidate_pool()
        plan = build_probe_plan(edges)

        self.assertGreater(len(edges), 20)
        self.assertIn("expert", {edge["source_family"] for edge in edges})
        self.assertIn("llm", {edge["source_family"] for edge in edges})
        self.assertIn("source_family", {row["probe_level"] for row in plan})
        self.assertIn("target_group", {row["probe_level"] for row in plan})
        self.assertIn("lag_group", {row["probe_level"] for row in plan})
        self.assertIn("single_edge", {row["probe_level"] for row in plan})

    def test_validation_gain_gate_runs_before_cf_guard(self) -> None:
        rejected = evaluate_probe_row(
            {
                "probe_id": "single_edge:e1",
                "probe_level": "single_edge",
                "edge_ids": ["e1"],
                "validation_gain": -0.01,
                "low_tail_delta": 0.05,
                "far_delta": 0.0,
                "mar_delta": 0.0,
                "cf_sensitivity": 0.99,
            }
        )

        self.assertFalse(rejected["admitted"])
        self.assertEqual(rejected["stage_reached"], "validation_gain")
        self.assertFalse(rejected["cf_evaluated"])
        self.assertIn("validation_gain_not_positive", rejected["reject_reasons"])

    def test_only_single_edges_that_pass_ordered_gates_are_admitted(self) -> None:
        edges = [
            {"edge_id": "good", "source_family": "expert", "source": "a", "target": "b", "lag": 1},
            {"edge_id": "harmful", "source_family": "llm", "source": "c", "target": "d", "lag": 2},
        ]
        result = admit_edges_from_probe_results(
            edges,
            [
                {
                    "probe_id": "single_edge:good",
                    "probe_level": "single_edge",
                    "edge_ids": ["good"],
                    "validation_gain": 0.01,
                    "low_tail_delta": 0.0,
                    "far_delta": 0.0,
                    "mar_delta": 0.0,
                    "cf_sensitivity": 0.1,
                },
                {
                    "probe_id": "single_edge:harmful",
                    "probe_level": "single_edge",
                    "edge_ids": ["harmful"],
                    "validation_gain": 0.02,
                    "low_tail_delta": -0.5,
                    "far_delta": 0.0,
                    "mar_delta": 0.0,
                    "cf_sensitivity": 0.99,
                },
            ],
        )

        self.assertEqual(result["n_validation_admitted_edges"], 1)
        self.assertEqual(result["validation_admitted_edges"][0]["edge_id"], "good")
        harmful = [row for row in result["probe_results"] if row["probe_id"] == "single_edge:harmful"][0]
        self.assertFalse(harmful["admitted"])
        self.assertFalse(harmful["cf_evaluated"])
        self.assertIn("low_tail_harm", harmful["reject_reasons"])

    def test_default_artifact_writes_plan_without_admitting_unmeasured_edges(self) -> None:
        written = build_default_hierarchical_artifact(self.output_dir)

        expected = {
            self.output_dir / "hierarchical_edge_probe_admission.json",
            self.output_dir / "hierarchical_edge_probe_admission.md",
        }
        self.assertEqual(set(written), expected)
        with open(_fs_path(self.output_dir / "hierarchical_edge_probe_admission.json"), encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["artifact_status"], "probe_plan_only_no_validation_scores")
        self.assertEqual(payload["n_validation_admitted_edges"], 0)
        self.assertIn("validation_gain", payload["gate_order"][0])
        self.assertIn("CF guard is evaluated only after validation gain", Path(_fs_path(self.output_dir / "hierarchical_edge_probe_admission.md")).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
