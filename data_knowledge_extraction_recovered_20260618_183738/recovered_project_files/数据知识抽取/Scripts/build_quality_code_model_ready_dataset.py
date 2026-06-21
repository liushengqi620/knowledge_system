from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
V8_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v8_quality_abnormal_event_cleanconflict"
CLASSIFIED_DIR = ROOT / "knowledge_exports" / "quality_code_curation_v1_classified"
OUT_DIR = ROOT / "knowledge_exports" / "quality_code_model_ready_v1"

XY_IN = V8_DIR / "xy_quality_traceability.csv"
X_IN = V8_DIR / "X_process_features.csv"
CLASSIFIED_LABELS_IN = CLASSIFIED_DIR / "quality_label_analyzable_codes_classified.csv"
CODE_CLASSIFICATION_IN = CLASSIFIED_DIR / "quality_code_classification.csv"

KEY = "记录识别码"

CLASSIFIED_COLUMNS = [
    KEY,
    "quality_codes_original",
    "quality_codes_analyzable",
    "quality_codes_low_support_removed",
    "quality_code_group_set_analyzable",
    "quality_code_group_cn_set_analyzable",
    "n_quality_codes_original",
    "n_quality_codes_analyzable",
    "n_quality_codes_low_support_removed",
    "quality_code_curation_role",
    "quality_code_analyzable_label",
    "quality_code_macro_class_set",
    "quality_code_macro_class_cn_set",
    "quality_code_model_role_set",
    "quality_code_model_role_cn_set",
    "quality_codes_core_quality",
    "quality_codes_process_precursor",
    "quality_codes_auxiliary_state",
    "quality_core_code_label",
    "quality_process_precursor_label",
    "quality_auxiliary_state_label",
]

ID_COLUMNS = [
    "record_id",
    "process_time",
    "连铸处理号",
    "材料跟踪号",
    "记录识别码",
    "source_row_id",
    "process_sequence_key",
]


def as_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)


def assign_roles(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    core = as_int_series(out["quality_core_code_label"])
    precursor = as_int_series(out["quality_process_precursor_label"])
    aux = as_int_series(out["quality_auxiliary_state_label"])
    abnormal = as_int_series(out["quality_abnormal_event_label"])
    low_support_only = out["quality_code_curation_role"].fillna("").eq("low_support_only_auxiliary")

    out["core_quality_binary_label"] = core
    out["process_precursor_binary_label"] = precursor
    out["auxiliary_state_context_label"] = aux

    core_roles = []
    precursor_roles = []
    multilabel_roles = []
    for c, p, a, abn, low in zip(core, precursor, aux, abnormal, low_support_only):
        if c == 1:
            core_roles.append("target_positive_core_quality")
        elif abn == 0:
            core_roles.append("clean_negative")
        elif low:
            core_roles.append("auxiliary_low_support_only")
        else:
            core_roles.append("auxiliary_non_core_quality_event")

        if p == 1:
            precursor_roles.append("target_positive_process_precursor")
        elif abn == 0:
            precursor_roles.append("clean_negative")
        elif low:
            precursor_roles.append("auxiliary_low_support_only")
        else:
            precursor_roles.append("auxiliary_non_precursor_quality_event")

        if c or p or a:
            multilabel_roles.append("analyzable_code_event")
        elif abn == 0:
            multilabel_roles.append("clean_negative")
        elif low:
            multilabel_roles.append("auxiliary_low_support_only")
        else:
            multilabel_roles.append("auxiliary_no_analyzable_code")

    out["core_quality_task_role"] = core_roles
    out["process_precursor_task_role"] = precursor_roles
    out["quality_code_multilabel_role"] = multilabel_roles
    return out


def summarize_task(df: pd.DataFrame, role_col: str, label_col: str) -> dict[str, object]:
    main = df[df[role_col].isin(["target_positive_core_quality", "target_positive_process_precursor", "clean_negative"])]
    return {
        "role_counts": df[role_col].value_counts(dropna=False).to_dict(),
        "main_rows": int(len(main)),
        "main_label_counts": main[label_col].value_counts(dropna=False).to_dict() if label_col in main else {},
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    xy = pd.read_csv(XY_IN, low_memory=False)
    classified = pd.read_csv(CLASSIFIED_LABELS_IN, usecols=CLASSIFIED_COLUMNS, low_memory=False)

    if xy[KEY].duplicated().any():
        raise RuntimeError(f"{XY_IN} has duplicated merge key {KEY}")
    if classified[KEY].duplicated().any():
        raise RuntimeError(f"{CLASSIFIED_LABELS_IN} has duplicated merge key {KEY}")

    merged = xy.merge(classified, on=KEY, how="left", validate="one_to_one")
    missing = int(merged["quality_core_code_label"].isna().sum())
    if missing:
        raise RuntimeError(f"{missing} rows failed to merge classified quality-code labels")

    merged = assign_roles(merged)

    aligned_labels_cols = [
        *[c for c in ID_COLUMNS if c in merged.columns],
        "quality_abnormal_event_label",
        "quality_event_label",
        "quality_codes_original",
        "quality_codes_analyzable",
        "quality_codes_low_support_removed",
        "quality_code_macro_class_set",
        "quality_code_model_role_set",
        "quality_codes_core_quality",
        "quality_codes_process_precursor",
        "quality_codes_auxiliary_state",
        "core_quality_binary_label",
        "process_precursor_binary_label",
        "auxiliary_state_context_label",
        "core_quality_task_role",
        "process_precursor_task_role",
        "quality_code_multilabel_role",
        "reason_mechanism_set",
        "reason_stage_set",
        "reason_variable_group_set",
        "reason_available",
        "reason_confidence",
        "steel_change_reason_code",
        "steel_change_reason_group",
    ]
    aligned_labels_cols = [c for c in aligned_labels_cols if c in merged.columns]

    aligned_path = OUT_DIR / "y_quality_code_tasks_aligned.csv"
    xy_all_path = OUT_DIR / "xy_quality_code_model_ready_all.csv"
    core_main_path = OUT_DIR / "xy_core_quality_binary_main.csv"
    precursor_main_path = OUT_DIR / "xy_process_precursor_binary_main.csv"
    code_classification_path = OUT_DIR / "quality_code_classification.csv"
    x_path = OUT_DIR / "X_process_features.csv"
    summary_path = OUT_DIR / "dataset_summary.json"

    merged[aligned_labels_cols].to_csv(aligned_path, index=False, encoding="utf-8-sig")
    merged.to_csv(xy_all_path, index=False, encoding="utf-8-sig")

    core_main = merged[merged["core_quality_task_role"].isin(["target_positive_core_quality", "clean_negative"])].copy()
    precursor_main = merged[
        merged["process_precursor_task_role"].isin(["target_positive_process_precursor", "clean_negative"])
    ].copy()
    core_main.to_csv(core_main_path, index=False, encoding="utf-8-sig")
    precursor_main.to_csv(precursor_main_path, index=False, encoding="utf-8-sig")

    shutil.copy2(CODE_CLASSIFICATION_IN, code_classification_path)
    shutil.copy2(X_IN, x_path)

    summary = {
        "source_xy": str(XY_IN),
        "source_classified_labels": str(CLASSIFIED_LABELS_IN),
        "n_rows_merged": int(len(merged)),
        "merge_key": KEY,
        "n_core_quality_positive_rows": int(merged["core_quality_binary_label"].sum()),
        "n_process_precursor_positive_rows": int(merged["process_precursor_binary_label"].sum()),
        "n_auxiliary_state_context_rows": int(merged["auxiliary_state_context_label"].sum()),
        "core_quality_task": summarize_task(merged, "core_quality_task_role", "core_quality_binary_label"),
        "process_precursor_task": summarize_task(
            merged, "process_precursor_task_role", "process_precursor_binary_label"
        ),
        "multilabel_role_counts": merged["quality_code_multilabel_role"].value_counts(dropna=False).to_dict(),
        "outputs": {
            "y_quality_code_tasks_aligned": str(aligned_path),
            "xy_quality_code_model_ready_all": str(xy_all_path),
            "xy_core_quality_binary_main": str(core_main_path),
            "xy_process_precursor_binary_main": str(precursor_main_path),
            "quality_code_classification": str(code_classification_path),
            "X_process_features_copy": str(x_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
