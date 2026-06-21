from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from knowledge_state import append_knowledge_candidates
from paper_defect_pipeline import _build_event_window_supervision


class PipelineExtensionTests(unittest.TestCase):
    def test_event_window_supervision_creates_multi_level_mil_fields(self) -> None:
        df = pd.DataFrame({"x": np.arange(18, dtype=float)})
        y = np.zeros(18, dtype=int)
        y[8] = 1
        y[15] = 1
        cfg = {
            "paper_event_supervision_enabled": True,
            "event_precursor_min_lag": 1,
            "event_precursor_max_lag": 6,
            "event_buffer_after_lag": 0,
            "event_min_positive_after_windowing": 2,
            "event_min_negative_after_windowing": 2,
            "event_precursor_levels": [
                {"name": "late", "min_lag": 1, "max_lag": 2, "weight": 1.0},
                {"name": "mid", "min_lag": 3, "max_lag": 4, "weight": 0.8},
                {"name": "early", "min_lag": 5, "max_lag": 6, "weight": 0.55},
            ],
        }

        out_df, out_y, meta = _build_event_window_supervision(df, y, cfg)

        self.assertEqual(meta["mode"], "event_precursor_window")
        self.assertTrue(meta["mil_enabled"])
        self.assertGreaterEqual(meta["bag_count"], 2)
        self.assertIn("event_window_label", out_df.columns)
        self.assertIn("event_precursor_level", out_df.columns)
        self.assertIn("event_horizon_steps", out_df.columns)
        self.assertIn("event_bag_id", out_df.columns)
        self.assertIn("event_sample_weight", out_df.columns)
        self.assertGreater(int(out_y.sum()), 0)
        self.assertTrue({"late", "mid", "early"}.intersection(set(out_df["event_precursor_level"])))
        positive_weights = out_df.loc[out_df["event_window_label"] == 1, "event_sample_weight"]
        self.assertGreater(float(positive_weights.max()), float(positive_weights.min()))

    def test_candidate_registry_preserves_expert_review_and_tracks_history(self) -> None:
        bundle = {
            "version": "candidate-v2",
            "candidates": [
                {
                    "stage": "candidate",
                    "from": "mold_level",
                    "to": "quality_abnormal",
                    "lag": 2,
                    "relation_type": "process_propagation",
                    "score": 0.8,
                    "weight": 0.7,
                    "confidence": 0.6,
                    "stability": 0.5,
                    "dominant_source": "task_occlusion",
                    "evidence": {"task_occlusion": 0.5, "rule_prior": 0.3},
                    "evidence_sources": ["task_occlusion", "rule_prior"],
                }
            ],
        }
        report = {
            "target_label_column": "defect_label",
            "data_file": "model_ready.csv",
            "split_protocol_used": "time_ordered",
            "f1_defect_test_tuned": 0.7,
            "pr_auc_test": 0.8,
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = append_knowledge_candidates(root, candidate_bundle=bundle, defect_report=report)
            registry_path = Path(first["registry_path"])
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            item = registry["items"][0]
            item["review_status"] = "expert_approved"
            item["expert_approved"] = True
            item["active"] = True
            item["stage"] = "expert_approved"
            registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

            second = append_knowledge_candidates(root, candidate_bundle=bundle, defect_report=report)
            updated = json.loads(registry_path.read_text(encoding="utf-8"))
            updated_item = updated["items"][0]

            self.assertEqual(second["updated"], 1)
            self.assertTrue(Path(second["registry_path"]).is_file())
            self.assertTrue(Path(second["review_csv_path"]).is_file())
            self.assertEqual(updated_item["review_status"], "expert_approved")
            self.assertEqual(updated_item["stage"], "expert_approved")
            self.assertTrue(updated_item["expert_approved"])
            self.assertTrue(updated_item["active"])
            self.assertGreaterEqual(len(updated_item["history"]), 2)


if __name__ == "__main__":
    unittest.main()
