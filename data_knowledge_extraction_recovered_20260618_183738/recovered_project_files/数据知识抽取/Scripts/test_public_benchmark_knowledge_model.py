from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from public_benchmark_knowledge_model import build_mechanism_edge_features, build_public_benchmark_knowledge_model


class PublicBenchmarkKnowledgeModelTest(unittest.TestCase):
    def test_skab_knowledge_graph_uses_actual_flow_column(self) -> None:
        x = pd.DataFrame(
            {
                "record_id": ["r1", "r2"],
                "Current": [1.0, 2.0],
                "Temperature": [30.0, 32.0],
                "Voltage": [220.0, 221.0],
                "Pressure": [0.2, 0.3],
                "Volume Flow RateRMS": [75.0, 76.0],
                "Accelerometer1RMS": [0.1, 0.2],
                "Thermocouple": [28.0, 29.0],
            }
        )
        y = pd.DataFrame({"record_id": ["r1", "r2"], "anomaly": [0, 1], "changepoint": [0, 1]})

        with tempfile.TemporaryDirectory() as tmp:
            result = build_public_benchmark_knowledge_model("skab", x, y, output_dir=Path(tmp))
            graph = json.loads((Path(tmp) / "knowledge_graph.json").read_text(encoding="utf-8"))

        self.assertGreaterEqual(result["n_edges"], 4)
        pairs = {(edge["source"], edge["target"]) for edge in graph["edges"]}
        self.assertIn(("Volume Flow RateRMS", "Pressure"), pairs)
        self.assertIn(("Pressure", "Volume Flow RateRMS"), pairs)

    def test_mechanism_edge_features_are_model_ready(self) -> None:
        x = pd.DataFrame(
            {
                "Current": [1.0, 2.0, 3.0],
                "Temperature": [10.0, 12.0, 15.0],
                "Voltage": [100.0, 101.0, 102.0],
                "Pressure": [0.1, 0.2, 0.4],
                "Volume Flow RateRMS": [50.0, 55.0, 60.0],
            }
        )

        features, diagnostics = build_mechanism_edge_features("skab", x)

        self.assertGreater(diagnostics["generated_features"], 0)
        self.assertEqual(len(features), len(x))
        self.assertTrue(any(col.startswith("kg_") for col in features.columns))


if __name__ == "__main__":
    unittest.main()
