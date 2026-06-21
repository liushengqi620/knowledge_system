from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from boundary_graph_learning import learn_boundary_coupling_graph
from defect_graph_model import UnifiedDefectGraphModel
from rule_margin import RuleSpec, assign_boundary_region, compute_rule_margin, summarize_boundary_regions


class BoundaryMethodComponentTests(unittest.TestCase):
    def test_rule_margin_uses_signed_nearest_normalized_rule_distance(self) -> None:
        df = pd.DataFrame(
            {
                "mold_level_range": [10.0, 11.5, 12.2, 14.0],
                "superheat": [30.0, 6.0, 4.0, 20.0],
            }
        )
        rules = [
            RuleSpec(name="mold_upper", column="mold_level_range", upper=12.0, scale=2.0),
            RuleSpec(name="superheat_lower", column="superheat", lower=5.0, scale=5.0),
        ]

        out = compute_rule_margin(df, rules)
        regions = assign_boundary_region(out["rule_margin"], eps=0.25)

        self.assertTrue(np.allclose(out["rule_margin"].to_numpy(), [-1.0, -0.25, 0.20, 1.0]))
        self.assertEqual(out["active_rule"].tolist(), ["mold_upper", "mold_upper", "mold_upper", "mold_upper"])
        self.assertEqual(
            regions.tolist(),
            ["clear_normal", "normal_boundary", "abnormal_boundary", "clear_abnormal"],
        )

    def test_boundary_summary_reports_eps_sensitive_counts_and_ratios(self) -> None:
        margins = pd.Series([-1.0, -0.20, 0.10, 0.80], name="rule_margin")

        summary = summarize_boundary_regions(margins, eps_list=[0.15, 0.25])

        self.assertEqual(summary.loc[summary["eps"] == 0.15, "boundary_n"].iloc[0], 1)
        self.assertEqual(summary.loc[summary["eps"] == 0.25, "boundary_n"].iloc[0], 2)
        self.assertAlmostEqual(summary.loc[summary["eps"] == 0.25, "boundary_ratio"].iloc[0], 0.5)

    def test_boundary_graph_learning_prefers_boundary_enriched_lagged_source(self) -> None:
        n = 80
        source = np.zeros(n, dtype=float)
        source[20:40] = np.linspace(0.0, 4.0, 20)
        target = np.roll(source, 1)
        target[0] = 0.0
        unrelated = np.sin(np.linspace(0.0, 6.0, n))
        margin = np.full(n, -1.0, dtype=float)
        margin[20:40] = np.linspace(-0.2, 0.2, 20)
        df = pd.DataFrame({"source": source, "target": target, "unrelated": unrelated})

        edges = learn_boundary_coupling_graph(
            df,
            ["source", "target", "unrelated"],
            margin,
            max_lag=2,
            eps=0.25,
            top_k=3,
            direction_prior={("source", "target"): 1.0},
        )

        self.assertGreaterEqual(len(edges), 1)
        top = edges[0]
        self.assertEqual((top.from_node, top.to_node), ("source", "target"))
        self.assertEqual(top.relation_type, "event_precursor")
        self.assertGreater(top.evidence["boundary_enrichment"], 0.0)
        self.assertGreater(top.evidence["lag_predictive_gain"], 0.0)

    def test_kiepgl_explain_only_mode_keeps_final_probabilities_equal_to_base(self) -> None:
        model = UnifiedDefectGraphModel(
            {
                "paper_model_variant": "invariant_event_precursor_graph",
                "kiepgl_enabled": True,
                "kiepgl_mode": "explain_only",
                "kiepgl_logit_fusion_enabled": True,
            }
        )
        classes = np.array([0, 1, 2], dtype=int)
        base_proba = np.array([[0.70, 0.20, 0.10], [0.20, 0.60, 0.20]], dtype=float)
        base_logits = model._class_logits_from_proba(base_proba)
        path_scores = np.ones((2, 0), dtype=np.float32)

        fused = model._fuse_kiepgl_class_logits(
            base_logits,
            path_scores,
            classes,
            base_class_proba=base_proba,
        )

        self.assertTrue(np.allclose(fused["final_class_probabilities"], base_proba, atol=1e-6))
        self.assertTrue(np.allclose(fused["path_mil_logits"], 0.0))
        self.assertTrue(np.allclose(fused["knowledge_prior_logits"], 0.0))


if __name__ == "__main__":
    unittest.main()
