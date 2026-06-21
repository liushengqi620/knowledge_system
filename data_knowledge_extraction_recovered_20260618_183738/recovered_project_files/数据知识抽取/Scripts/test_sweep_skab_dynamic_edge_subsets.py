from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sweep_skab_dynamic_edge_subsets import edge_label, enumerate_edge_subsets, write_best_candidate_cache


class SweepSkabDynamicEdgeSubsetsTest(unittest.TestCase):
    def test_enumerate_edge_subsets_builds_singletons_and_pairs(self) -> None:
        edges = [
            {"source": "A", "target": "B", "lag": 1},
            {"source": "B", "target": "C", "lag": 2},
            {"source": "C", "target": "D", "lag": 3},
        ]

        subsets = enumerate_edge_subsets(edges, max_subset_size=2)

        self.assertEqual(len(subsets), 6)
        self.assertEqual(edge_label(subsets[0][0]), "A->B@1")

    def test_write_best_candidate_cache_requires_validation_positive_subset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "best.json"
            written = write_best_candidate_cache(
                {
                    "seed": 42,
                    "candidate_file": "source.json",
                    "best": {
                        "validation_gain": 0.01,
                        "validation_macro_f1": 0.7,
                        "test_macro_f1": 0.6,
                        "test_gain": 0.0,
                        "edge_labels": ["A->B@1"],
                        "edges": [{"source": "A", "target": "B", "lag": 1, "reliability": 0.5}],
                    },
                },
                path,
            )

            self.assertTrue(written)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "skab_cf_validated_candidate_subset_v1")
            self.assertEqual(len(payload["dynamic_edges"]), 1)

    def test_write_best_candidate_cache_skips_negative_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "best.json"
            written = write_best_candidate_cache({"seed": 42, "best": {"validation_gain": -0.01}}, path)

            self.assertFalse(written)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
