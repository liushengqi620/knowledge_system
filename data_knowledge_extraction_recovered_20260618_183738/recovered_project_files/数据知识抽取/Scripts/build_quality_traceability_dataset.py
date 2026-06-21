from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROCESS_GROUPS = (
    "flux",
    "tundish",
    "casting_speed",
    "mold_level",
    "nozzle_flow",
    "argon_and_pressure",
    "stopper",
    "mold_heat_transfer",
    "mold_ems_taper_oscillation",
)

DERIVED_PROCESS_FEATURES = (
    "TD_weight_mean",
    "TD_weight_range",
    "TD_avg_temp",
    "cast_speed_mean",
    "cast_speed_range",
    "liquidus_temp",
    "superheat",
    "cover_flux_1",
    "cover_flux_2",
    "cover_flux_total",
    "cover_flux_ratio",
    "mold_level_range",
    "mold_level_mean",
    "mold_level_ge7",
    "mold_level_ge10",
    "tundish_sequence_count",
    "heat_exchange_mean",
    "heat_exchange_ew_diff",
    "heat_exchange_ns_diff",
)

TARGET_MULTICLASS_LABELS = (
    ("no_quality_abnormal", "无品质异常"),
    ("temperature_flux", "温度/保护渣质量异常"),
    ("mold_level_slag_risk", "液面波动/卷渣风险异常"),
    ("speed_stopper_flow", "拉速/塞棒/流量控制异常"),
    ("heat_transfer_imbalance", "结晶器传热不均异常"),
    ("process_fluctuation", "过程参数波动异常"),
)

TARGET_MULTICLASS_IDS = {
    code: idx for idx, (code, _name) in enumerate(TARGET_MULTICLASS_LABELS)
}

TARGET_MULTICLASS_NAMES = {
    code: name for code, name in TARGET_MULTICLASS_LABELS
}

TARGET_QUALITY_GROUP_COLUMNS = (
    "quality_group_temperature_flux",
    "quality_group_mold_level_slag_risk",
    "quality_group_speed_stopper_flow",
    "quality_group_heat_transfer_imbalance",
    "quality_group_process_fluctuation",
)

AUXILIARY_CLASS_NAMES = {
    "transition_tundish": "过渡/中间包状态辅助样本",
    "other_quality_abnormal": "其他未归因品质异常辅助样本",
    "unmapped_quality_abnormal": "未映射品质异常",
}

META_COLUMNS = (
    "record_id",
    "process_time",
    "连铸处理号",
    "材料跟踪号",
    "记录识别码",
)

Y_COLUMNS = (
    "quality_label",
    "quality_sample_role",
    "quality_label_source",
    "quality_abnormal_label",
    "quality_code_present_label",
    "quality_abnormal_codes",
    "quality_abnormal_group",
    "quality_abnormal_group_cn",
    "quality_abnormal_groups",
    "quality_group_mold_level_slag_risk",
    "quality_group_process_fluctuation",
    "quality_group_speed_stopper_flow",
    "quality_group_heat_transfer_imbalance",
    "quality_group_transition_tundish",
    "quality_group_temperature_flux",
    "quality_group_other_quality_abnormal",
)

EXCLUDE_FROM_X = {
    "defect_label",
    "defect_label_lock",
    "quality_label",
    "quality_sample_role",
    "quality_label_source",
    "quality_abnormal_label",
    "quality_code_present_label",
    "quality_abnormal_codes",
    "quality_abnormal_group",
    "quality_abnormal_group_cn",
    "quality_abnormal_groups",
    "quality_group_mold_level_slag_risk",
    "quality_group_process_fluctuation",
    "quality_group_speed_stopper_flow",
    "quality_group_heat_transfer_imbalance",
    "quality_group_transition_tundish",
    "quality_group_temperature_flux",
    "quality_group_other_quality_abnormal",
}


def _unique_existing(cols: list[str], existing: set[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for col in cols:
        if col in existing and col not in seen:
            out.append(col)
            seen.add(col)
    return out


def _numeric_feature_columns(
    df: pd.DataFrame,
    columns_by_group: dict[str, Any],
) -> tuple[list[str], dict[str, list[str]]]:
    existing = set(df.columns)
    feature_groups: dict[str, list[str]] = {}
    feature_cols: list[str] = []

    for group in PROCESS_GROUPS:
        raw_cols = columns_by_group.get(group, {}).get("columns", [])
        numeric_cols: list[str] = []
        for col in raw_cols:
            if col not in existing or col in EXCLUDE_FROM_X:
                continue
            s = pd.to_numeric(df[col], errors="coerce")
            if s.notna().mean() < 0.35 or s.nunique(dropna=True) <= 1:
                continue
            df[col] = s
            numeric_cols.append(col)
            feature_cols.append(col)
        feature_groups[group] = numeric_cols

    derived_cols: list[str] = []
    for col in DERIVED_PROCESS_FEATURES:
        if col not in existing or col in EXCLUDE_FROM_X:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        if s.notna().mean() < 0.35 or s.nunique(dropna=True) <= 1:
            continue
        df[col] = s
        derived_cols.append(col)
        feature_cols.append(col)
    feature_groups["derived_process"] = derived_cols

    feature_cols = list(dict.fromkeys(feature_cols))
    return feature_cols, feature_groups


def _clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _single_multiclass_code(row: pd.Series) -> str:
    role = _clean_text(row.get("quality_sample_role", ""))
    quality_label = pd.to_numeric(pd.Series([row.get("quality_label", None)]), errors="coerce").iloc[0]
    group = _clean_text(row.get("quality_abnormal_group", ""))
    if role == "clean_negative" or quality_label == 0:
        return "no_quality_abnormal"
    if group in TARGET_MULTICLASS_IDS:
        return group
    groups = _clean_text(row.get("quality_abnormal_groups", ""))
    for code, _name in TARGET_MULTICLASS_LABELS[1:]:
        if code in groups:
            return code
    return "unmapped_quality_abnormal"


def _build_multiclass_labels(main_df: pd.DataFrame) -> pd.DataFrame:
    labels = pd.DataFrame({"record_id": main_df["record_id"].to_numpy()})
    labels["quality_multiclass_code"] = main_df.apply(_single_multiclass_code, axis=1).to_numpy()
    labels["quality_multiclass_id"] = labels["quality_multiclass_code"].map(TARGET_MULTICLASS_IDS).fillna(-1).astype("int16")
    labels["quality_multiclass_name"] = labels["quality_multiclass_code"].map(
        {**TARGET_MULTICLASS_NAMES, **AUXILIARY_CLASS_NAMES}
    )
    labels["quality_sample_role"] = main_df.get("quality_sample_role", "").astype(str).to_numpy()
    if "quality_abnormal_codes" in main_df.columns:
        labels["quality_abnormal_codes"] = main_df["quality_abnormal_codes"].astype(str).to_numpy()
    if "quality_abnormal_groups" in main_df.columns:
        labels["quality_abnormal_groups"] = main_df["quality_abnormal_groups"].astype(str).to_numpy()
    return labels


def _build_multilabel_targets(main_df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"record_id": main_df["record_id"].to_numpy()})
    for col in TARGET_QUALITY_GROUP_COLUMNS:
        if col in main_df.columns:
            out[col] = pd.to_numeric(main_df[col], errors="coerce").fillna(0).astype("int8").to_numpy()
        else:
            out[col] = 0
    out["quality_target_label_count"] = out[list(TARGET_QUALITY_GROUP_COLUMNS)].sum(axis=1).astype("int8")
    out["has_multiple_quality_targets"] = (out["quality_target_label_count"] > 1).astype("int8")
    return out


def build_quality_traceability_dataset(
    input_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    all_path = input_dir / "continuous_casting_all.csv"
    columns_path = input_dir / "continuous_casting_columns_by_group.json"
    mapping_path = input_dir / "quality_abnormal_group_mapping.json"

    df = pd.read_csv(all_path, encoding="utf-8-sig", low_memory=False)
    df.insert(0, "record_id", range(len(df)))
    columns_by_group = json.loads(columns_path.read_text(encoding="utf-8"))

    feature_cols, feature_groups = _numeric_feature_columns(df, columns_by_group)
    meta_cols = _unique_existing(list(META_COLUMNS), set(df.columns))
    y_cols = _unique_existing(list(Y_COLUMNS), set(df.columns))
    if "quality_abnormal_label" in df.columns and "quality_label" not in df.columns:
        df["quality_label"] = pd.to_numeric(df["quality_abnormal_label"], errors="coerce").fillna(0).astype("int8")
        df["quality_sample_role"] = df["quality_label"].map({1: "target_positive", 0: "clean_negative"}).fillna("auxiliary_excluded")
        df["quality_label_source"] = "quality_abnormal_code_1_5"
        y_cols = _unique_existing(list(Y_COLUMNS), set(df.columns))

    if "quality_sample_role" in df.columns:
        main_mask = df["quality_sample_role"].astype(str).isin(["target_positive", "clean_negative"])
    else:
        main_mask = pd.Series(True, index=df.index)
    main_df = df.loc[main_mask].copy()

    output_dir.mkdir(parents=True, exist_ok=True)
    X = main_df[["record_id"] + feature_cols].copy()
    y = main_df[meta_cols + y_cols].copy()
    xy = main_df[meta_cols + y_cols + feature_cols].copy()
    y_multiclass = _build_multiclass_labels(main_df)
    y_multilabel = _build_multilabel_targets(main_df)
    auxiliary = df.loc[~main_mask, meta_cols + y_cols].copy()
    invalid = main_df.loc[main_df[feature_cols].isna().all(axis=1), meta_cols + y_cols].copy() if feature_cols else main_df.iloc[0:0][meta_cols + y_cols].copy()

    x_path = output_dir / "X_process_features.csv"
    y_path = output_dir / "y_quality_abnormal.csv"
    y_legacy_path = output_dir / "y_quality_label.csv"
    y_multiclass_path = output_dir / "y_quality_multiclass.csv"
    y_multilabel_path = output_dir / "y_quality_multilabel.csv"
    xy_path = output_dir / "xy_quality_traceability.csv"
    aux_path = output_dir / "auxiliary_quality_events.csv"
    invalid_path = output_dir / "invalid_data_quality_rows.csv"
    feature_groups_path = output_dir / "feature_groups.json"
    label_mapping_path = output_dir / "label_mapping.json"
    summary_path = output_dir / "dataset_summary.json"
    readme_path = output_dir / "README.md"

    X.to_csv(x_path, index=False, encoding="utf-8-sig")
    y.to_csv(y_path, index=False, encoding="utf-8-sig")
    y.to_csv(y_legacy_path, index=False, encoding="utf-8-sig")
    y_multiclass.to_csv(y_multiclass_path, index=False, encoding="utf-8-sig")
    y_multilabel.to_csv(y_multilabel_path, index=False, encoding="utf-8-sig")
    xy.to_csv(xy_path, index=False, encoding="utf-8-sig")
    auxiliary.to_csv(aux_path, index=False, encoding="utf-8-sig")
    invalid.to_csv(invalid_path, index=False, encoding="utf-8-sig")
    feature_groups_path.write_text(
        json.dumps(feature_groups, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    label_mapping = {
        "binary_task": {
            "column": "quality_label",
            "negative": {"id": 0, "name": "无品质异常", "rule": "品质异常代码1-5均为空、0或缺失"},
            "positive": {"id": 1, "name": "目标质量异常", "rule": "品质异常代码命中目标质量异常大类"},
        },
        "single_label_multiclass_task": {
            "id_column": "quality_multiclass_id",
            "code_column": "quality_multiclass_code",
            "name_column": "quality_multiclass_name",
            "classes": [
                {"id": idx, "code": code, "name": name}
                for idx, (code, name) in enumerate(TARGET_MULTICLASS_LABELS)
            ],
            "priority_rule": "一条记录命中多个目标异常大类时，按温度/保护渣、液面/卷渣、拉速/塞棒/流量、传热不均、过程波动的顺序选主类。",
        },
        "multi_label_task": {
            "columns": list(TARGET_QUALITY_GROUP_COLUMNS),
            "count_column": "quality_target_label_count",
            "multiple_flag_column": "has_multiple_quality_targets",
            "usage": "用于保留同一记录同时命中多个异常机理的情况，不强制压成单一类别。",
        },
        "auxiliary_samples": {
            "excluded_from_main_training": ["transition_tundish", "other_quality_abnormal"],
            "usage": "作为知识图谱、历史案例和规则沉淀数据，不直接进入主二分类/多分类训练集。",
        },
    }
    label_mapping_path.write_text(json.dumps(label_mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    label_counts = (
        main_df["quality_abnormal_group_cn"].value_counts(dropna=False).to_dict()
        if "quality_abnormal_group_cn" in df.columns
        else {}
    )
    multilabel_cols = [c for c in y_cols if c.startswith("quality_group_")]
    multilabel_counts = {
        col: int(pd.to_numeric(main_df[col], errors="coerce").fillna(0).sum())
        for col in multilabel_cols
        if col in df.columns
    }
    target_multilabel_counts = {
        col: int(y_multilabel[col].sum())
        for col in TARGET_QUALITY_GROUP_COLUMNS
        if col in y_multilabel.columns
    }
    multiclass_counts = y_multiclass["quality_multiclass_name"].value_counts(dropna=False).to_dict()
    multiple_target_count = int(y_multilabel["has_multiple_quality_targets"].sum())
    role_counts = (
        df["quality_sample_role"].astype(str).value_counts(dropna=False).to_dict()
        if "quality_sample_role" in df.columns
        else {}
    )
    quality_label_counts = (
        main_df["quality_label"].value_counts(dropna=False).to_dict()
        if "quality_label" in main_df.columns
        else {}
    )
    summary = {
        "source_dir": str(input_dir),
        "n_rows": int(len(main_df)),
        "n_source_rows": int(len(df)),
        "n_auxiliary_rows": int((~main_mask).sum()),
        "n_x_features": int(len(feature_cols)),
        "meta_columns": meta_cols,
        "y_columns": y_cols,
        "x_feature_columns": feature_cols,
        "feature_groups": {k: len(v) for k, v in feature_groups.items()},
        "quality_label_counts": {str(k): int(v) for k, v in quality_label_counts.items()},
        "quality_sample_role_counts": {str(k): int(v) for k, v in role_counts.items()},
        "primary_label_counts": {str(k): int(v) for k, v in label_counts.items()},
        "quality_multiclass_counts": {str(k): int(v) for k, v in multiclass_counts.items()},
        "multilabel_counts": multilabel_counts,
        "target_multilabel_counts": target_multilabel_counts,
        "multiple_target_sample_count": multiple_target_count,
        "outputs": {
            "X_process_features": str(x_path),
            "y_quality_abnormal": str(y_path),
            "y_quality_label": str(y_legacy_path),
            "y_quality_multiclass": str(y_multiclass_path),
            "y_quality_multilabel": str(y_multilabel_path),
            "xy_quality_traceability": str(xy_path),
            "auxiliary_quality_events": str(aux_path),
            "invalid_data_quality_rows": str(invalid_path),
            "feature_groups": str(feature_groups_path),
            "label_mapping": str(label_mapping_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    readme_path.write_text(
        "\n".join(
            [
                "# 品质异常溯源建模数据集",
                "",
                "本目录将连铸原始数据重新整理为建模友好的 X/y 结构。",
                "",
                "## 文件",
                "",
                "- `X_process_features.csv`: 生产工艺参数合集 X。第一列 `record_id` 用于和 y 对齐，其余列为数值型工艺特征。",
                "- `y_quality_abnormal.csv`: 品质异常标签 y，包含主异常大类、中文标签、原始异常代码集合和多标签 one-hot。",
                "- `y_quality_label.csv`: 兼容旧版 KIEP-GL 脚本的标签表，内容同 `y_quality_abnormal.csv`。",
                "- `xy_quality_traceability.csv`: 元数据 + y + X 的统筹宽表，便于直接分析和建模。",
                "- `auxiliary_quality_events.csv`: 过渡/状态类辅助样本。",
                "- `invalid_data_quality_rows.csv`: 全特征缺失等不适合建模的记录。",
                "- `feature_groups.json`: X 特征按工艺模块分组。",
                "- `label_mapping.json`: 品质异常代码到异常大类的映射。",
                "- `dataset_summary.json`: 行数、特征数、标签分布和输出清单。",
                "",
                "## 建议用法",
                "",
                "优先用 `quality_abnormal_group` / `quality_abnormal_group_cn` 做单标签主任务；",
                "若一条记录有多个异常大类，用 `quality_group_*` 列做多标签溯源。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Build X/y dataset for quality abnormal traceability.")
    parser.add_argument(
        "--input-dir",
        default=str(root / "knowledge_exports" / "continuous_casting_grouped"),
    )
    parser.add_argument(
        "--output-dir",
        default=str(root / "knowledge_exports" / "quality_traceability_dataset"),
    )
    args = parser.parse_args()
    summary = build_quality_traceability_dataset(Path(args.input_dir), Path(args.output_dir))
    print("quality traceability dataset completed")
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:3000])


if __name__ == "__main__":
    main()
