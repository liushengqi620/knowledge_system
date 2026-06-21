from __future__ import annotations

import unittest
from pathlib import Path

from export_skab_cf_candidate_edges import balanced_candidate_edges, merge_candidate_edges, output_path


class ExportSkabCfCandidateEdgesTest(unittest.TestCase):
    def test_merge_candidate_edges_deduplicates_and_tracks_families(self) -> None:
        edges = merge_candidate_edges(
            [
                ("expert", [{"source": "Current", "target": "Pressure", "lag": 1, "reliability": 0.45}]),
                ("data", [{"source": "Current", "target": "Pressure", "lag": 1, "reliability": 0.80}]),
                ("llm", [{"source": "Voltage", "target": "Current", "lag": 1, "reliability": 0.10}]),
            ],
            allowed_features=["Current", "Pressure", "Voltage"],
            max_edges=4,
            min_reliability=0.20,
        )

        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["reliability"], 0.80)
        self.assertEqual(edges[0]["source_families"], ["data", "expert"])

    def test_output_path_matches_cf_suite_cache_name(self) -> None:
        path = output_path(Path("exports"), 42)

        self.assertEqual(
            path.name,
            "public_benchmark_skab_dynamic_llm_api_seed42_e8_learned_reliability_probe2_t045_k4.json",
        )

    def test_balanced_candidate_edges_reserves_expert_and_llm_sources(self) -> None:
        edges = balanced_candidate_edges(
            [
                ("expert", [{"source": "Current", "target": "Pressure", "lag": 1, "reliability": 0.30}]),
                ("llm_static", [{"source": "Voltage", "target": "Current", "lag": 1, "reliability": 0.30}]),
                (
                    "data",
                    [
                        {"source": "A", "target": "B", "lag": 1, "reliability": 0.90},
                        {"source": "B", "target": "A", "lag": 1, "reliability": 0.90},
                    ],
                ),
            ],
            allowed_features=["Current", "Pressure", "Voltage", "A", "B"],
            max_edges=3,
            min_reliability=0.20,
            reserve_per_family=1,
        )

        families = [set(edge["source_families"]) for edge in edges]
        self.assertIn({"expert"}, families)
        self.assertIn({"llm_static"}, families)


if __name__ == "__main__":
    unittest.main()
