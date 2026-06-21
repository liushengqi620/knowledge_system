from __future__ import annotations

import unittest

from run_skab_msfg_pruning_ablation import build_source_mode_edge_sets


class SkabMsfgPruningAblationTest(unittest.TestCase):
    def test_build_source_mode_edge_sets_separates_pruned_and_source_roles(self) -> None:
        expert_edges = [
            {
                "source": "Current",
                "target": "Accelerometer1RMS",
                "lags": [2],
                "weight": 0.9,
                "reliability": 0.8,
                "source_system": "expert",
            },
            {
                "source": "Pressure",
                "target": "Current",
                "lags": [1],
                "weight": 0.9,
                "reliability": 0.8,
                "source_system": "expert",
            },
        ]
        llm_edges = [
            {
                "source": "Current",
                "target": "Accelerometer1RMS",
                "lags": [2],
                "weight": 0.7,
                "reliability": 0.7,
                "source_system": "llm",
            }
        ]
        data_edges = [
            {
                "source": "Pressure",
                "target": "Volume Flow RateRMS",
                "lags": [1],
                "weight": 0.8,
                "reliability": 0.8,
                "source_system": "data_lag",
            }
        ]

        modes = build_source_mode_edge_sets(
            expert_edges=expert_edges,
            llm_edges=llm_edges,
            data_edges=data_edges,
            min_support_score=0.2,
        )

        self.assertEqual(
            set(modes),
            {
                "original_full_msfg",
                "full_pruned_kg",
                "no_llm_pruned_kg",
                "expert_only_pruned_kg",
                "llm_only",
                "data_only",
            },
        )
        self.assertGreater(
            modes["original_full_msfg"]["fusion"]["n_fused_edges"],
            modes["full_pruned_kg"]["fusion"]["n_fused_edges"],
        )
        self.assertEqual(modes["full_pruned_kg"]["expert_pruning"]["n_pruned_expert_edges"], 1)
        self.assertEqual(len(modes["no_llm_pruned_kg"]["llm_edges"]), 0)
        self.assertEqual(len(modes["llm_only"]["expert_edges"]), 0)
        self.assertEqual(len(modes["llm_only"]["data_edges"]), 0)
        self.assertEqual(len(modes["data_only"]["llm_edges"]), 0)


if __name__ == "__main__":
    unittest.main()
