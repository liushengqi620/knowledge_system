from __future__ import annotations

import unittest

from run_tep_sequence_graph_ablation import aggregate_records, build_variant_configs


class TepSequenceGraphAblationTest(unittest.TestCase):
    def test_build_variant_configs_defines_no_all_and_reliable_lagged_graphs(self) -> None:
        variants = build_variant_configs(graph_strength=0.2, reliability_threshold=0.7, max_edges=40)

        self.assertEqual([item["name"] for item in variants], ["no_graph", "all_lagged", "reliable_lagged"])
        self.assertEqual(variants[0]["graph_strength"], 0.0)
        self.assertFalse(variants[0]["use_lagged_graph"])
        self.assertEqual(variants[1]["graph_strength"], 0.2)
        self.assertTrue(variants[1]["use_lagged_graph"])
        self.assertEqual(variants[1]["graph_reliability_threshold"], 0.0)
        self.assertIsNone(variants[1]["graph_max_edges"])
        self.assertEqual(variants[2]["graph_reliability_threshold"], 0.7)
        self.assertEqual(variants[2]["graph_max_edges"], 40)

    def test_build_variant_configs_can_add_residual_gated_lagged_graph(self) -> None:
        variants = build_variant_configs(
            graph_strength=0.2,
            reliability_threshold=0.7,
            max_edges=40,
            include_residual_gated=True,
        )

        self.assertEqual(
            [item["name"] for item in variants],
            ["no_graph", "all_lagged", "reliable_lagged", "residual_gated_lagged"],
        )
        self.assertEqual(variants[-1]["lagged_graph_fusion_mode"], "residual_channel")
        self.assertTrue(variants[-1]["use_lagged_graph"])

    def test_build_variant_configs_can_select_efficiency_subset(self) -> None:
        variants = build_variant_configs(
            graph_strength=0.2,
            reliability_threshold=0.7,
            max_edges=40,
            include_residual_gated=True,
            selected_variants=["no_graph", "residual_gated_lagged"],
        )

        self.assertEqual([item["name"] for item in variants], ["no_graph", "residual_gated_lagged"])

    def test_build_variant_configs_rejects_unknown_selected_variant(self) -> None:
        with self.assertRaises(ValueError):
            build_variant_configs(
                graph_strength=0.2,
                reliability_threshold=0.7,
                max_edges=40,
                include_residual_gated=True,
                selected_variants=["missing"],
            )

    def test_aggregate_records_computes_variant_metrics_and_edge_counts(self) -> None:
        records = [
            {
                "variant": "no_graph",
                "seed": 1,
                "result": {
                    "sample_multiclass_metrics": {"target_defect_macro_f1": 0.10, "macro_f1": 0.09},
                    "event_warning_metrics": {"event_macro_recall": 0.20},
                    "path_explanation_metrics": {"path_hit_rate": 0.0},
                    "graph_constraint": {"enabled": False},
                },
            },
            {
                "variant": "reliable_lagged",
                "seed": 1,
                "result": {
                    "sample_multiclass_metrics": {"target_defect_macro_f1": 0.20, "macro_f1": 0.18},
                    "event_warning_metrics": {"event_macro_recall": 0.30},
                    "path_explanation_metrics": {"path_hit_rate": 0.1},
                    "graph_constraint": {"candidate_edges": 10, "matched_edges": 4, "pruned_edges": 6},
                },
            },
            {
                "variant": "reliable_lagged",
                "seed": 2,
                "result": {
                    "sample_multiclass_metrics": {"target_defect_macro_f1": 0.30, "macro_f1": 0.28},
                    "event_warning_metrics": {"event_macro_recall": 0.40},
                    "path_explanation_metrics": {"path_hit_rate": 0.2},
                    "graph_constraint": {"candidate_edges": 12, "matched_edges": 6, "pruned_edges": 6},
                },
            },
        ]

        summary = aggregate_records(records)

        self.assertAlmostEqual(summary["no_graph"]["target_defect_macro_f1_mean"], 0.10)
        self.assertAlmostEqual(summary["reliable_lagged"]["target_defect_macro_f1_mean"], 0.25)
        self.assertAlmostEqual(summary["reliable_lagged"]["target_defect_macro_f1_std"], 0.05)
        self.assertAlmostEqual(summary["reliable_lagged"]["matched_edges_mean"], 5.0)
        self.assertAlmostEqual(summary["reliable_lagged"]["pruned_edges_mean"], 6.0)


if __name__ == "__main__":
    unittest.main()
