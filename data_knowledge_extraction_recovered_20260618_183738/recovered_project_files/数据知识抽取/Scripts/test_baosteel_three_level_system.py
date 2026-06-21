from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

import pandas as pd

from baosteel_three_level_system import (
    build_multihop_path_templates,
    compute_three_level_path_metrics,
    run_three_level_system,
)
from baosteel_three_level_api import load_system_artifacts


class BaosteelThreeLevelSystemTests(unittest.TestCase):
    def test_multihop_templates_are_not_short_chains(self) -> None:
        feature_columns = [
            "superheat_mean",
            "cover_flux_total_last",
            "mold_level_range_last",
            "cast_speed_range_mean",
        ]
        feature_groups = {
            "derived_process": [
                "superheat",
                "cover_flux_total",
                "mold_level_range",
                "cast_speed_range",
            ]
        }

        paths = build_multihop_path_templates(feature_columns, feature_groups)

        self.assertTrue(paths)
        for path in paths:
            self.assertGreaterEqual(len(path["nodes"]), 5)
            self.assertEqual(path["nodes"][0]["layer"], "window_feature")
            self.assertIn("correction_action", {node["layer"] for node in path["nodes"]})
            self.assertIn(path["defect_mechanism"], path["event_target"])

    def test_path_metrics_align_mechanism_variable_group_and_stage(self) -> None:
        top_paths_by_event = {
            "event_a": [
                {
                    "defect_mechanism": "temperature_flux",
                    "variable_group": "temperature",
                    "stage": "late",
                    "path_occlusion_drop": 0.22,
                    "nodes": [
                        {"layer": "window_feature", "id": "superheat_mean"},
                        {"layer": "variable_group", "id": "temperature"},
                        {"layer": "equipment_zone", "id": "tundish"},
                        {"layer": "process_state", "id": "thermal_state"},
                        {"layer": "defect_mechanism", "id": "temperature_flux"},
                    ],
                }
            ],
            "event_b": [
                {
                    "defect_mechanism": "mold_level_slag_risk",
                    "variable_group": "mold_level",
                    "stage": "mid",
                    "path_occlusion_drop": 0.05,
                    "nodes": [
                        {"layer": "window_feature", "id": "mold_level_range_last"},
                        {"layer": "variable_group", "id": "mold_level"},
                        {"layer": "equipment_zone", "id": "mold"},
                        {"layer": "process_state", "id": "mold_level_stability"},
                        {"layer": "defect_mechanism", "id": "mold_level_slag_risk"},
                    ],
                }
            ],
            "event_no_reason": [
                {
                    "defect_mechanism": "process_fluctuation",
                    "variable_group": "process_operation",
                    "stage": "early",
                    "path_occlusion_drop": 0.01,
                    "nodes": [
                        {"layer": "window_feature", "id": "TD_weight_range_mean"},
                        {"layer": "variable_group", "id": "process_operation"},
                        {"layer": "equipment_zone", "id": "tundish"},
                        {"layer": "process_state", "id": "process_operation"},
                        {"layer": "defect_mechanism", "id": "process_fluctuation"},
                    ],
                }
            ],
        }

        metrics = compute_three_level_path_metrics(
            top_paths_by_event,
            reason_mechanisms_by_event={
                "event_a": "temperature_flux",
                "event_b": "temperature_flux",
                "event_no_reason": "no_reason_evidence",
            },
            reason_variable_groups_by_event={
                "event_a": "temperature;superheat;flux",
                "event_b": "mold_level;slag",
                "event_no_reason": "none",
            },
            reason_stages_by_event={
                "event_a": "thermal_state;late",
                "event_b": "mold",
                "event_no_reason": "none",
            },
            top_k=1,
        )

        self.assertEqual(metrics["n_reason_events"], 2)
        self.assertAlmostEqual(metrics["mechanism_alignment_at_k"], 0.5)
        self.assertAlmostEqual(metrics["variable_group_alignment_at_k"], 1.0)
        self.assertAlmostEqual(metrics["stage_alignment_at_k"], 0.5)
        self.assertGreater(metrics["path_comprehensiveness"], 0.0)
        self.assertGreater(metrics["average_occlusion_drop_at_k"], 0.0)

    def test_smoke_pipeline_exports_three_level_artifacts(self) -> None:
        root = Path(__file__).resolve().parent.parent / "knowledge_exports" / f"_test_three_level_{uuid.uuid4().hex}"
        dataset_dir = root / "dataset"
        output_dir = root / "system"
        try:
            dataset_dir.mkdir(parents=True)
            x = pd.DataFrame(
                {
                    "sample_id": [f"s{i}" for i in range(24)],
                    "event_bag_id": [f"event_{i // 3}" for i in range(24)],
                    "precursor_stage": ["late", "mid", "early"] * 8,
                    "lead_horizon_min": [1, 5, 10] * 8,
                    "caster_id": [2] * 24,
                    "strand_parity": [1] * 24,
                    "superheat_mean": [10, 12, 14, 50, 52, 54] * 4,
                    "cover_flux_total_last": [1, 1, 2, 8, 9, 10] * 4,
                    "mold_level_range_last": [2, 3, 4, 18, 19, 20] * 4,
                    "cast_speed_range_mean": [0.02, 0.03, 0.04, 0.20, 0.22, 0.24] * 4,
                    "TD_weight_range_mean": [1, 2, 1, 12, 14, 16] * 4,
                }
            )
            y = pd.DataFrame(
                {
                    "sample_id": x["sample_id"],
                    "event_bag_id": x["event_bag_id"],
                    "event_quality_class_id": [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3] * 2,
                    "event_quality_class": [
                        "no_quality_abnormal",
                        "no_quality_abnormal",
                        "no_quality_abnormal",
                        "temperature_flux",
                        "temperature_flux",
                        "temperature_flux",
                        "mold_level_slag_risk",
                        "mold_level_slag_risk",
                        "mold_level_slag_risk",
                        "process_fluctuation",
                        "process_fluctuation",
                        "process_fluctuation",
                    ]
                    * 2,
                    "event_is_abnormal": [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1] * 2,
                    "risk_label": [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1] * 2,
                    "quality_abnormal_groups": [
                        "no_quality_abnormal",
                        "no_quality_abnormal",
                        "no_quality_abnormal",
                        "temperature_flux;transition_tundish",
                        "temperature_flux",
                        "temperature_flux",
                        "mold_level_slag_risk",
                        "mold_level_slag_risk;transition_tundish",
                        "mold_level_slag_risk",
                        "process_fluctuation",
                        "process_fluctuation",
                        "process_fluctuation",
                    ]
                    * 2,
                    "reason_mechanism_set": [
                        "no_reason_evidence",
                        "no_reason_evidence",
                        "no_reason_evidence",
                        "temperature_flux",
                        "temperature_flux",
                        "temperature_flux",
                        "mold_level_slag_risk",
                        "mold_level_slag_risk",
                        "mold_level_slag_risk",
                        "process_fluctuation",
                        "process_fluctuation",
                        "process_fluctuation",
                    ]
                    * 2,
                    "reason_stage_set": [
                        "none",
                        "none",
                        "none",
                        "thermal_state",
                        "thermal_state",
                        "thermal_state",
                        "mold",
                        "mold",
                        "mold",
                        "process_operation",
                        "process_operation",
                        "process_operation",
                    ]
                    * 2,
                    "reason_variable_group_set": [
                        "none",
                        "none",
                        "none",
                        "temperature;superheat;flux",
                        "temperature;superheat;flux",
                        "temperature;superheat;flux",
                        "mold_level;slag",
                        "mold_level;slag",
                        "mold_level;slag",
                        "tundish_weight;sequence_transition",
                        "tundish_weight;sequence_transition",
                        "tundish_weight;sequence_transition",
                    ]
                    * 2,
                }
            )
            mapping = {
                "classes": [
                    {"class_id": 0, "class_name": "no_quality_abnormal"},
                    {"class_id": 1, "class_name": "temperature_flux"},
                    {"class_id": 2, "class_name": "mold_level_slag_risk"},
                    {"class_id": 3, "class_name": "process_fluctuation"},
                ]
            }
            feature_groups = {
                "derived_process": [
                    "superheat",
                    "cover_flux_total",
                    "mold_level_range",
                    "cast_speed_range",
                    "TD_weight_range",
                ]
            }
            x.to_csv(dataset_dir / "X_event_precursor_windows.csv", index=False, encoding="utf-8-sig")
            y.to_csv(dataset_dir / "y_hierarchical_event_label.csv", index=False, encoding="utf-8-sig")
            (dataset_dir / "class_name_mapping.json").write_text(json.dumps(mapping), encoding="utf-8")
            (dataset_dir / "feature_groups.json").write_text(json.dumps(feature_groups), encoding="utf-8")

            summary = run_three_level_system(
                dataset_dir=dataset_dir,
                output_dir=output_dir,
                max_rows=24,
                n_estimators=8,
                random_state=7,
            )
            artifacts = load_system_artifacts(output_dir)

            self.assertEqual(summary["status"], "ok")
            self.assertTrue((output_dir / "dashboard" / "index.html").is_file())
            self.assertIn("risk_warning", artifacts["metrics"])
            self.assertIn("abnormal_identification", artifacts["metrics"])
            self.assertIn("traceability", artifacts["metrics"])
            self.assertTrue(artifacts["events"])
            first_event = artifacts["events"][0]
            self.assertIn("risk_probability", first_event["risk_warning"])
            self.assertIn("top_k_paths", first_event["traceability"])
            self.assertGreaterEqual(len(first_event["traceability"]["top_k_paths"][0]["nodes"]), 5)
            self.assertIn("recommended_checks", first_event["recommendation"])
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
