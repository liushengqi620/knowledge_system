import csv
import json
from pathlib import Path


def test_baosteel_builder_writes_valid_records(tmp_path: Path):
    from experiments.build_baosteel_knowledge_extraction_dataset import build_dataset
    from experiments.validate_knowledge_extraction_dataset import iter_records, validate_records

    quality_dir = tmp_path / "quality_traceability_dataset"
    three_level_dir = tmp_path / "baosteel_three_level_system_v1"
    quality_dir.mkdir()
    three_level_dir.mkdir()

    (quality_dir / "feature_groups.json").write_text(
        json.dumps(
            {
                "tundish": ["TD_avg_temp"],
                "mold_level": ["mold_level_range"],
                "casting_speed": ["cast_speed_mean"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with (quality_dir / "xy_quality_traceability.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "record_id",
                "process_time",
                "连铸处理号",
                "材料跟踪号",
                "记录识别码",
                "quality_abnormal_label",
                "quality_abnormal_codes",
                "quality_abnormal_group",
                "quality_abnormal_group_cn",
                "quality_abnormal_groups",
                "quality_label",
                "TD_avg_temp",
                "mold_level_range",
                "cast_speed_mean",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record_id": "1",
                "process_time": "2022-01-01 00:00:00",
                "连铸处理号": "255928",
                "材料跟踪号": "M001",
                "记录识别码": "RID001",
                "quality_abnormal_label": "1",
                "quality_abnormal_codes": "18;0",
                "quality_abnormal_group": "mold_level_slag_risk",
                "quality_abnormal_group_cn": "液面/卷渣质量类",
                "quality_abnormal_groups": "mold_level_slag_risk;other_quality_abnormal",
                "quality_label": "1",
                "TD_avg_temp": "1561",
                "mold_level_range": "10",
                "cast_speed_mean": "1.01",
            }
        )

    event = {
        "event_id": "event_1_mold_level_slag_risk",
        "sample_id": "event_1_mold_level_slag_risk__late",
        "precursor_stage": "late",
        "risk_warning": {
            "risk_probability": 0.9,
            "risk_level": "high",
            "boundary_status": "boundary_violation",
            "top_risk_variables": [{"feature": "mold_level_range_last", "value": 10, "importance": 0.2, "score": 2.0}],
        },
        "abnormal_identification": {
            "primary_abnormal_class": "mold_level_slag_risk",
            "true_abnormal_class": "mold_level_slag_risk",
            "class_confidence": 0.8,
        },
        "traceability": {
            "top_k_paths": [
                {
                    "path_id": "path_1",
                    "path_score": 0.7,
                    "path_template_id": "mold_level->mold_level_slag_risk",
                    "nodes": [
                        {"id": "mold_level_range_last", "label": "mold_level_range_last", "layer": "window_feature"},
                        {"id": "mold_level", "label": "mold_level", "layer": "variable_group"},
                        {"id": "mold", "label": "mold", "layer": "equipment_zone"},
                        {"id": "mold_level_unstable", "label": "mold_level_unstable", "layer": "process_state"},
                        {"id": "mold_level_slag_risk", "label": "mold_level_slag_risk", "layer": "defect_mechanism"},
                    ],
                }
            ]
        },
        "recommendation": {
            "recommended_checks": ["核对液面波动"],
            "recommended_adjustments": ["加强液面复核"],
        },
    }
    (three_level_dir / "event_explanations.jsonl").write_text(json.dumps(event, ensure_ascii=False) + "\n", encoding="utf-8")

    output_dir = tmp_path / "out"
    manifest = build_dataset(
        quality_dir=quality_dir,
        three_level_dir=three_level_dir,
        output_dir=output_dir,
        top_features=3,
        max_structured_records=0,
        max_event_records=0,
        preview_records=2,
    )

    assert manifest["records"] == 2
    assert (output_dir / "records.jsonl").exists()
    assert (output_dir / "splits" / "train.jsonl").exists()
    assert (output_dir / "plm" / "baosteel_plm_train_pool.json").exists()

    records = list(iter_records(output_dir / "records.jsonl"))
    assert {record["source"]["source_type"] for record in records} == {
        "baosteel_processed_traceability_row",
        "baosteel_three_level_event_explanation",
    }
    assert validate_records(records) == []
