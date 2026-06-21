from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from run_skab_dynamic_llm_graph_experiment import (
    _apply_counterfactual_guard,
    _apply_validation_gain_guard,
    _filter_edges_by_reliability,
    _load_dynamic_edges_file,
    _perturb_edges,
)


class RunSkabDynamicLlmGraphExperimentTest(unittest.TestCase):
    def test_load_dynamic_edges_file_reads_saved_experiment_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "result.json"
            path.write_text(
                json.dumps({"dynamic_edges": [{"source": "Current", "target": "Pressure", "reliability": 0.7}]}),
                encoding="utf-8",
            )

            edges, diag = _load_dynamic_edges_file(path, max_edges=4)

        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["source"], "Current")
        self.assertEqual(diag["status"], "ok")

    def test_load_dynamic_edges_file_reads_candidate_edges_from_cf_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cf_result.json"
            path.write_text(
                json.dumps(
                    {
                        "dynamic_edges": [],
                        "candidate_dynamic_edges": [
                            {"source": "Current", "target": "Pressure", "reliability": 0.7}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            edges, diag = _load_dynamic_edges_file(path, max_edges=4)

        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["target"], "Pressure")
        self.assertEqual(diag["status"], "ok")

    def test_filter_edges_by_reliability_is_strict_and_reports_counts(self) -> None:
        edges, diag = _filter_edges_by_reliability(
            [
                {"source": "Current", "target": "Pressure", "reliability": 0.7},
                {"source": "Voltage", "target": "Current", "reliability": 0.2},
            ],
            threshold=0.45,
        )

        self.assertEqual(len(edges), 1)
        self.assertEqual(diag["n_rejected_by_reliability"], 1)
        self.assertEqual(diag["n_kept_after_reliability"], 1)

    def test_validation_gain_guard_rejects_negative_validation_gain(self) -> None:
        admitted, diag = _apply_validation_gain_guard(
            baseline={"validation_metrics": {"macro_f1": 0.70}},
            candidate={"validation_metrics": {"macro_f1": 0.65}},
            min_macro_gain=0.0,
            n_edges=4,
        )

        self.assertFalse(admitted)
        self.assertEqual(diag["n_rejected_by_validation_gain_guard"], 4)
        self.assertLess(diag["validation_macro_f1_gain"], 0.0)

    def test_counterfactual_perturbations_change_edge_structure(self) -> None:
        edges = [{"source": "Current", "target": "Pressure", "lag": 1, "reliability": 0.7}]

        reverse = _perturb_edges(edges, mode="reverse_direction", allowed_features=["Current", "Pressure", "Voltage"])
        lag = _perturb_edges(edges, mode="lag_shift", allowed_features=["Current", "Pressure", "Voltage"])
        random_target = _perturb_edges(edges, mode="random_target", allowed_features=["Current", "Pressure", "Voltage"])

        self.assertEqual(reverse[0]["source"], "Pressure")
        self.assertEqual(reverse[0]["target"], "Current")
        self.assertEqual(lag[0]["lag"], 2)
        self.assertNotEqual(random_target[0]["target"], "Pressure")

    def test_counterfactual_guard_can_require_multiple_passing_modes(self) -> None:
        calls = []

        def fake_train(**kwargs):
            calls.append(kwargs["dynamic_llm_edges"][0]["mode"])
            values = {"good": 0.60, "bad": 0.69}
            return {"validation_metrics": {"macro_f1": values[kwargs["dynamic_llm_edges"][0]["mode"]]}}

        candidate = {"validation_metrics": {"macro_f1": 0.70}}
        edges = [{"source": "A", "target": "B", "lag": 1}]
        common = {}

        import run_skab_dynamic_llm_graph_experiment as mod

        original_perturb = mod._perturb_edges
        original_train = mod._train_msfg_time_context_branch
        try:
            mod._perturb_edges = lambda _edges, mode, allowed_features: [{"mode": "good" if mode == "reverse_direction" else "bad"}]
            mod._train_msfg_time_context_branch = fake_train
            admitted, diag = _apply_counterfactual_guard(
                candidate=candidate,
                common=common,
                edges=edges,
                modes=["reverse_direction", "lag_shift"],
                min_macro_drop=0.02,
                min_passing_modes=2,
                allowed_features=["A", "B"],
                seed=42,
            )
        finally:
            mod._perturb_edges = original_perturb
            mod._train_msfg_time_context_branch = original_train

        self.assertFalse(admitted)
        self.assertEqual(diag["counterfactual_passing_modes"], ["reverse_direction"])
        self.assertEqual(diag["n_rejected_by_counterfactual_guard"], 1)


if __name__ == "__main__":
    unittest.main()
