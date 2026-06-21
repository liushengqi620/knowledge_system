from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "knowledge_exports" / "quality_code_model_ready_v1"
XY_IN = SOURCE_DIR / "xy_quality_code_model_ready_all.csv"
CODE_CLASSIFICATION_IN = SOURCE_DIR / "quality_code_classification.csv"
OUT_DIR = ROOT / "knowledge_exports" / "quality_code_second_stage_v1"

KEY_COLUMNS = [
    "record_id",
    "process_time",
    "连铸处理号",
    "材料跟踪号",
    "记录识别码",
    "source_row_id",
    "process_sequence_key",
]

MACRO_CLASSES = [
    "mold_level_slag_quality",
    "temperature_flux_quality",
    "heat_transfer_quality",
    "flow_control_anomaly",
    "process_parameter_anomaly",
    "transition_or_quality_state",
]

MACRO_CLASS_CN = {
    "mold_level_slag_quality": "液面/卷渣质量类",
    "temperature_flux_quality": "温度/保护剂质量类",
    "heat_transfer_quality": "传热不均质量类",
    "flow_control_anomaly": "拉速-塞棒/流量控制异常类",
    "process_parameter_anomaly": "过程参数异常类",
    "transition_or_quality_state": "交接过渡/质量状态类",
}

# Primary label is only for compatibility with conventional multiclass heads.
# The multilabel target remains the recommended second-stage formulation.
PRIMARY_PRIORITY = [
    "heat_transfer_quality",
    "mold_level_slag_quality",
    "temperature_flux_quality",
    "flow_control_anomaly",
    "process_parameter_anomaly",
    "transition_or_quality_state",
]


def split_set(value: object) -> list[str]:
    if pd.isna(value):
        return []
    text = str(value).strip()
    if text in {"", "none", "no_analyzable_quality_code", "no_quality_abnormal"}:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def choose_primary(classes: set[str]) -> str:
    for item in PRIMARY_PRIORITY:
        if item in classes:
            return item
    return "unknown_or_low_support"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    xy = pd.read_csv(XY_IN, low_memory=False)
    code_cls = pd.read_csv(CODE_CLASSIFICATION_IN, dtype={"code": str})
    analyzable_codes = code_cls.loc[code_cls["is_analyzable"] == 1, "code"].astype(str).tolist()

    # Second-stage abnormal-type recognition should not use clean negatives as
    # normal class by default. It is invoked after the first-stage risk filter.
    stage2 = xy[xy["quality_code_multilabel_role"].eq("analyzable_code_event")].copy()

    macro_sets = stage2["quality_code_macro_class_set"].map(lambda v: set(split_set(v)))
    for macro in MACRO_CLASSES:
        stage2[f"label_macro_{macro}"] = [int(macro in values) for values in macro_sets]

    for code in analyzable_codes:
        stage2[f"label_code_{code}"] = [
            int(code in set(split_set(value))) for value in stage2["quality_codes_analyzable"]
        ]

    primary = [choose_primary(values) for values in macro_sets]
    stage2["second_stage_primary_class"] = primary
    stage2["second_stage_primary_class_cn"] = [MACRO_CLASS_CN.get(item, "未知/低支持") for item in primary]
    stage2["second_stage_is_multilabel"] = [int(sum(m in values for m in MACRO_CLASSES) > 1) for values in macro_sets]
    stage2["second_stage_n_macro_labels"] = [sum(m in values for m in MACRO_CLASSES) for values in macro_sets]

    primary_mapping = {name: idx for idx, name in enumerate(PRIMARY_PRIORITY)}
    primary_mapping["unknown_or_low_support"] = len(primary_mapping)
    stage2["second_stage_primary_class_id"] = stage2["second_stage_primary_class"].map(primary_mapping).astype(int)

    label_cols = [
        *[c for c in KEY_COLUMNS if c in stage2.columns],
        "quality_codes_original",
        "quality_codes_analyzable",
        "quality_codes_low_support_removed",
        "quality_code_macro_class_set",
        "quality_code_model_role_set",
        "quality_codes_core_quality",
        "quality_codes_process_precursor",
        "quality_codes_auxiliary_state",
        "second_stage_primary_class",
        "second_stage_primary_class_cn",
        "second_stage_primary_class_id",
        "second_stage_is_multilabel",
        "second_stage_n_macro_labels",
        *[f"label_macro_{macro}" for macro in MACRO_CLASSES],
        *[f"label_code_{code}" for code in analyzable_codes],
        "reason_mechanism_set",
        "reason_available",
        "reason_confidence",
        "steel_change_reason_code",
        "steel_change_reason_group",
    ]
    label_cols = [c for c in label_cols if c in stage2.columns]

    y_path = OUT_DIR / "y_second_stage_multilabel.csv"
    xy_path = OUT_DIR / "xy_second_stage_multilabel.csv"
    multiclass_path = OUT_DIR / "xy_second_stage_primary_multiclass.csv"
    code_cls_path = OUT_DIR / "quality_code_classification.csv"
    summary_path = OUT_DIR / "dataset_summary.json"

    stage2[label_cols].to_csv(y_path, index=False, encoding="utf-8-sig")
    stage2.to_csv(xy_path, index=False, encoding="utf-8-sig")

    multiclass_cols = [
        *[c for c in KEY_COLUMNS if c in stage2.columns],
        "second_stage_primary_class_id",
        "second_stage_primary_class",
        "second_stage_primary_class_cn",
        "second_stage_is_multilabel",
        "second_stage_n_macro_labels",
        "quality_codes_analyzable",
        "quality_code_macro_class_set",
    ]
    feature_cols = [
        c
        for c in stage2.columns
        if c not in label_cols
        and not c.startswith("label_macro_")
        and not c.startswith("label_code_")
    ]
    stage2[[c for c in multiclass_cols if c in stage2.columns] + feature_cols].to_csv(
        multiclass_path, index=False, encoding="utf-8-sig"
    )
    code_cls.to_csv(code_cls_path, index=False, encoding="utf-8-sig")

    macro_counts = {macro: int(stage2[f"label_macro_{macro}"].sum()) for macro in MACRO_CLASSES}
    primary_counts = stage2["second_stage_primary_class"].value_counts().to_dict()
    n_multilabel = int(stage2["second_stage_is_multilabel"].sum())
    exact_code_counts = {
        code: int(stage2[f"label_code_{code}"].sum())
        for code in analyzable_codes
    }

    summary = {
        "source": str(XY_IN),
        "n_rows": int(len(stage2)),
        "task_definition": {
            "recommended": "multilabel abnormal-phenomenon recognition",
            "compatibility_output": "primary multiclass label derived by deterministic priority",
            "note": "Clean negatives are excluded because this is the second stage after risk filtering.",
        },
        "macro_classes": MACRO_CLASSES,
        "primary_priority": PRIMARY_PRIORITY,
        "n_multilabel_rows": n_multilabel,
        "multilabel_row_rate": n_multilabel / len(stage2) if len(stage2) else 0.0,
        "macro_label_counts": macro_counts,
        "primary_class_counts": primary_counts,
        "exact_code_counts": exact_code_counts,
        "outputs": {
            "y_second_stage_multilabel": str(y_path),
            "xy_second_stage_multilabel": str(xy_path),
            "xy_second_stage_primary_multiclass": str(multiclass_path),
            "quality_code_classification": str(code_cls_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
