from __future__ import annotations

import argparse
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

import run_skab_dynamic_llm_graph_experiment as runner


class SkabDynamicLlmGraphExperimentTest(unittest.TestCase):
    def test_fallback_local_edges_continue_training_when_api_returns_no_edges(self) -> None:
        args = argparse.Namespace(
            dataset_root="unused",
            previous_result="missing.json",
            seed=42,
            error_branch="dynamic_graph_tcn_gate",
            max_dynamic_edges=4,
            model="gpt-5.5",
            api_timeout=1.0,
            allow_empty_dynamic=False,
            fallback_local_on_api_error=True,
            sequence_window_size=4,
            sequence_epochs=1,
            sequence_hidden_dim=8,
            sequence_batch_size=2,
        )
        x_raw = pd.DataFrame({"sensor_a": [1.0, 2.0, 3.0, 4.0], "sensor_b": [0.1, 0.2, 0.3, 0.4]})
        y = np.asarray([0, 1, 0, 1], dtype=np.int64)
        meta = pd.DataFrame({"run_id": ["train", "val", "test", "test"]})
        fallback_edges = [
            {
                "source": "sensor_a",
                "target": "sensor_b",
                "lag": 2,
                "sign": 1,
                "edge_type": "llm_dynamic",
                "reliability": 0.61,
            }
        ]
        branch_outputs = [
            {"metrics": {"macro_f1": 0.50}, "protocol": {"point_adjusted": {"f1": 0.70}}},
            {"metrics": {"macro_f1": 0.60}, "protocol": {"point_adjusted": {"f1": 0.75}}},
        ]

        with (
            patch.object(runner, "load_skab_dataset", return_value=(x_raw, y, meta)),
            patch.object(runner, "build_skab_llm_graph_update_prompt", return_value="prompt"),
            patch.object(runner, "call_openai_skab_graph_proposer", return_value=("", {"status": "error"})),
            patch.object(
                runner,
                "build_skab_local_dynamic_llm_edges",
                return_value=(fallback_edges, {"status": "local_fallback"}),
                create=True,
            ),
            patch.object(runner, "build_skab_causal_sequence_windows", return_value=(np.zeros((4, 4, 2)), ["sensor_a", "valid_mask"])),
            patch.object(runner, "split_skab_runs", return_value=(["train"], ["val"], ["test"])),
            patch.object(runner, "_train_msfg_time_context_branch", side_effect=branch_outputs) as train_branch,
        ):
            result = runner.run_experiment(args)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["fallback"]["status"], "local_fallback")
        self.assertEqual(result["dynamic_edges"], fallback_edges)
        self.assertAlmostEqual(float(result["macro_f1_delta"]), 0.10)
        self.assertIsNone(train_branch.call_args_list[0].kwargs["dynamic_llm_edges"])
        self.assertEqual(train_branch.call_args_list[1].kwargs["dynamic_llm_edges"], fallback_edges)


if __name__ == "__main__":
    unittest.main()
