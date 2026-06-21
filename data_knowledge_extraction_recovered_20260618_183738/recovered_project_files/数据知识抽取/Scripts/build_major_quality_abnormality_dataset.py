from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "knowledge_exports" / "quality_code_model_ready_v1"
XY_IN = SOURCE_DIR / "xy_quality_code_model_ready_all.csv"
CLASS_IN = SOURCE_DIR / "quality_code_classification.csv"
OUT_DIR = ROOT / "knowledge_exports" / "major_quality_abnormality_v1"

KEY_COLUMNS = [
    "record_id",
    "process_time",
    "连铸处理号",
    "材料跟踪号",
    "记录识别码",
    "source_row_id",
    "process_sequence_key",
]

MAIN_MACRO_CLASSES = [
    "mold_level_slag_quality",
    "temperature_flux_quality",
    "heat_transfer_quality",
    "flow_control_anomaly",
    "process_parameter_anomaly",
]

CONTEXT_MACRO_CLASSES = [
    "transition_or_quality_state",
]

MACRO_CLASS_CN = {
    "mold_level_slag_quality": "液面/卷渣质量类",
    "temperature_flux_quality": "温度/保护剂质量类",
    "heat_transfer_quality": "传热不均质量类",
    "flow_control_anomaly": "拉速-塞棒/流量控制异常类",
    "process_parameter_anomaly": "过程参数异常类",
    "transition_or_quality_state": "交接过渡/质量状态类",
    "clean_negative": "无品质异常代码",
}

PRIMARY_PRIORITY = [
    "heat_transfer_quality",
    "mold_level_slag_quality",
    "temperature_flux_quality",
    "flow_control_anomaly",
    "process_parameter_anomaly",
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
    return "clean_negative" if not classes else "context_only"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    xy = pd.read_csv(XY_IN, low_memory=False)
    code_cls = pd.read_csv(CLASS_IN, dtype={"code": str})
    code_cls = code_cls[code_cls["is_analyzable"].eq(1)].copy()
    main_codes = code_cls[
        code_cls["macro_class"].isin(MAIN_MACRO_CLASSES)
    ]["code"].astype(str).tolist()
    context_codes = code_cls[
        code_cls["macro_class"].isin(CONTEXT_MACRO_CLASSES)
    ]["code"].astype(str).tolist()

    macro_sets = xy["quality_code_macro_class_set"].map(lambda v: set(split_set(v)))
    main_sets = [values.intersection(MAIN_MACRO_CLASSES) for values in macro_sets]
    context_sets = [values.intersection(CONTEXT_MACRO_CLASSES) for values in macro_sets]

    out = xy.copy()
    out["major_abnormality_label"] = [int(bool(values)) for values in main_sets]
    out["major_context_only_label"] = [
        int((not bool(main_values)) and bool(ctx_values))
        for main_values, ctx_values in zip(main_sets, context_sets)
    ]
    out["major_macro_class_set"] = [
        ";".join(sorted(values)) if values else "none" for values in main_sets
    ]
    out["major_primary_class"] = [choose_primary(values) for values in main_sets]
    out["major_primary_class_cn"] = [
        MACRO_CLASS_CN.get(value, value) for value in out["major_primary_class"]
    ]
    out["major_n_macro_labels"] = [len(values) for values in main_sets]
    out["major_is_multilabel"] = [int(len(values) > 1) for values in main_sets]

    primary_mapping = {name: idx for idx, name in enumerate(PRIMARY_PRIORITY)}
    primary_mapping["context_only"] = len(primary_mapping)
    primary_mapping["clean_negative"] = len(primary_mapping)
    out["major_primary_class_id"] = out["major_primary_class"].map(primary_mapping).astype(int)

    for macro in MAIN_MACRO_CLASSES:
        out[f"label_major_{macro}"] = [int(macro in values) for values in main_sets]

    for macro in CONTEXT_MACRO_CLASSES:
        out[f"context_{macro}"] = [int(macro in values) for values in context_sets]

    for code in main_codes:
        out[f"label_major_code_{code}"] = [
            int(code in set(split_set(value))) for value in out["quality_codes_analyzable"]
        ]

    for code in context_codes:
        out[f"context_code_{code}"] = [
            int(code in set(split_set(value))) for value in out["quality_codes_analyzable"]
        ]

    major = out[out["major_abnormality_label"].eq(1)].copy()
    clean_negative = out[out["quality_code_multilabel_role"].eq("clean_negative")].copy()
    context_only = out[out["major_context_only_label"].eq(1)].copy()
    train_binary = pd.concat([major, clean_negative], ignore_index=True)

    y_cols = [
        *[c for c in KEY_COLUMNS if c in out.columns],
        "quality_codes_original",
        "quality_codes_analyzable",
        "quality_codes_low_support_removed",
        "quality_code_macro_class_set",
        "quality_code_model_role_set",
        "quality_codes_core_quality",
        "quality_codes_process_precursor",
        "quality_codes_auxiliary_state",
        "major_abnormality_label",
        "major_context_only_label",
        "major_macro_class_set",
        "major_primary_class",
        "major_primary_class_cn",
        "major_primary_class_id",
        "major_n_macro_labels",
        "major_is_multilabel",
        *[f"label_major_{macro}" for macro in MAIN_MACRO_CLASSES],
        *[f"context_{macro}" for macro in CONTEXT_MACRO_CLASSES],
        *[f"label_major_code_{code}" for code in main_codes],
        *[f"context_code_{code}" for code in context_codes],
        "reason_mechanism_set",
        "reason_available",
        "reason_confidence",
        "steel_change_reason_code",
        "steel_change_reason_group",
    ]
    y_cols = [c for c in y_cols if c in out.columns]

    y_major_path = OUT_DIR / "y_major_abnormality_multilabel.csv"
    xy_major_path = OUT_DIR / "xy_major_abnormality_multilabel.csv"
    xy_binary_path = OUT_DIR / "xy_major_abnormality_with_clean_negative.csv"
    y_all_path = OUT_DIR / "y_major_abnormality_all_rows.csv"
    context_path = OUT_DIR / "context_only_auxiliary_rows.csv"
    class_path = OUT_DIR / "quality_code_classification_main.csv"
    summary_path = OUT_DIR / "dataset_summary.json"

    major[y_cols].to_csv(y_major_path, index=False, encoding="utf-8-sig")
    major.to_csv(xy_major_path, index=False, encoding="utf-8-sig")
    train_binary.to_csv(xy_binary_path, index=False, encoding="utf-8-sig")
    out[y_cols].to_csv(y_all_path, index=False, encoding="utf-8-sig")
    context_only[y_cols].to_csv(context_path, index=False, encoding="utf-8-sig")
    code_cls.to_csv(class_path, index=False, encoding="utf-8-sig")

    macro_counts = {
        macro: int(major[f"label_major_{macro}"].sum()) for macro in MAIN_MACRO_CLASSES
    }
    exact_code_counts = {
        code: int(major[f"label_major_code_{code}"].sum()) for code in main_codes
    }
    summary = {
        "source": str(XY_IN),
        "definition": {
            "major_abnormality": "Rows containing analyzable core-quality or process-precursor quality abnormal codes.",
            "excluded_from_main_target": "Low-support-only and transition/state-only rows are not used as main target labels.",
            "context_usage": "Transition/state codes are kept as context columns for tracing and ablation.",
        },
        "n_all_rows": int(len(out)),
        "n_major_rows": int(len(major)),
        "n_clean_negative_rows": int(len(clean_negative)),
        "n_context_only_rows": int(len(context_only)),
        "n_binary_train_rows": int(len(train_binary)),
        "n_main_codes": int(len(main_codes)),
        "n_context_codes": int(len(context_codes)),
        "main_macro_classes": MAIN_MACRO_CLASSES,
        "context_macro_classes": CONTEXT_MACRO_CLASSES,
        "primary_priority": PRIMARY_PRIORITY,
        "major_multilabel_rows": int(major["major_is_multilabel"].sum()),
        "major_multilabel_rate": float(major["major_is_multilabel"].mean()) if len(major) else 0.0,
        "major_macro_label_counts": macro_counts,
        "major_primary_class_counts": major["major_primary_class"].value_counts().to_dict(),
        "major_exact_code_counts": exact_code_counts,
        "outputs": {
            "y_major_abnormality_multilabel": str(y_major_path),
            "xy_major_abnormality_multilabel": str(xy_major_path),
            "xy_major_abnormality_with_clean_negative": str(xy_binary_path),
            "y_major_abnormality_all_rows": str(y_all_path),
            "context_only_auxiliary_rows": str(context_path),
            "quality_code_classification_main": str(class_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
