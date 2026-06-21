from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


RAW_NULL_VALUES = ["(null)", "null", "NULL", "", "nan", "NaN", "missing", "MISSING", "None", "none", "<NA>"]

QUALITY_CODE_GROUPS: dict[str, tuple[str, str]] = {
    "15": ("temperature_flux", "温度/保护剂质量类"),
    "24": ("temperature_flux", "温度/保护剂质量类"),
    "27": ("temperature_flux", "温度/保护剂质量类"),
    "33": ("temperature_flux", "温度/保护剂质量类"),
    "69": ("temperature_flux", "温度/保护剂质量类"),
    "70": ("temperature_flux", "温度/保护剂质量类"),
    "29": ("mold_level_slag_risk", "液面/卷渣质量类"),
    "30": ("mold_level_slag_risk", "液面/卷渣质量类"),
    "31": ("mold_level_slag_risk", "液面/卷渣质量类"),
    "32": ("mold_level_slag_risk", "液面/卷渣质量类"),
    "37": ("mold_level_slag_risk", "液面/卷渣质量类"),
    "54": ("mold_level_slag_risk", "液面/卷渣质量类"),
    "86": ("mold_level_slag_risk", "液面/卷渣质量类"),
    "38": ("heat_transfer_imbalance", "传热不均质量类"),
    "34": ("speed_stopper_flow", "拉速/塞棒/流量控制异常类"),
    "51": ("speed_stopper_flow", "拉速/塞棒/流量控制异常类"),
    "52": ("speed_stopper_flow", "拉速/塞棒/流量控制异常类"),
    "57": ("speed_stopper_flow", "拉速/塞棒/流量控制异常类"),
    "85": ("speed_stopper_flow", "拉速/塞棒/流量控制异常类"),
    "89": ("speed_stopper_flow", "拉速/塞棒/流量控制异常类"),
    "18": ("process_fluctuation", "过程参数异常类"),
    "19": ("process_fluctuation", "过程参数异常类"),
    "39": ("process_fluctuation", "过程参数异常类"),
    "55": ("process_fluctuation", "过程参数异常类"),
    "56": ("process_fluctuation", "过程参数异常类"),
    "83": ("process_fluctuation", "过程参数异常类"),
    "21": ("transition_tundish", "交接过渡/质量状态类"),
    "41": ("transition_tundish", "交接过渡/质量状态类"),
    "42": ("transition_tundish", "交接过渡/质量状态类"),
    "43": ("transition_tundish", "交接过渡/质量状态类"),
    "58": ("transition_tundish", "交接过渡/质量状态类"),
    "87": ("transition_tundish", "交接过渡/质量状态类"),
    "94": ("transition_tundish", "交接过渡/质量状态类"),
}

QUALITY_GROUP_PRIORITY = (
    "temperature_flux",
    "mold_level_slag_risk",
    "speed_stopper_flow",
    "heat_transfer_imbalance",
    "process_fluctuation",
    "transition_tundish",
    "other_quality_abnormal",
)

TARGET_QUALITY_GROUPS = {
    "temperature_flux",
    "mold_level_slag_risk",
    "speed_stopper_flow",
    "heat_transfer_imbalance",
    "process_fluctuation",
}

AUXILIARY_QUALITY_GROUPS = {
    "transition_tundish",
    "other_quality_abnormal",
}

NULL_CODE_TEXT = {str(item).strip().lower() for item in RAW_NULL_VALUES} | {"0", "0.0"}


@dataclass(frozen=True)
class ColumnGroup:
    name: str
    columns: tuple[str, ...]
    kind: str  # numeric | categorical | time | label


CONTINUOUS_CASTING_GROUPS: tuple[ColumnGroup, ...] = (
    ColumnGroup(
        "identity",
        (
            "材料跟踪号",
            "炼钢材料号",
            "铸机号",
            "奇偶流区分",
            "材料状态",
            "出钢记号",
            "钢级代码",
            "熔炼号",
            "钢包号",
            "连铸处理号",
            "中间包号",
            "前炉出钢记号",
            "后炉出钢记号",
            "插铁板板坯标识",
            "切断出钢记号",
            "记录识别码",
            "机组材料拼接主键",
        ),
        "categorical",
    ),
    ColumnGroup(
        "casting_time",
        (
            "记录创建时间",
            "钢包到达连铸时刻",
            "大包注入开始时刻",
            "大包注入终了时刻",
            "板坯切断时间",
        ),
        "time",
    ),
    ColumnGroup(
        "flux",
        (
            "覆盖剂1使用量/ppm",
            "覆盖剂2使用量/ppm",
            "下渣线圈状态",
        ),
        "numeric",
    ),
    ColumnGroup(
        "tundish",
        (
            "中间包连浇炉数",
            "连铸镇静时间/min",
            "交接部开始位置/mm",
            "交接部长度/mm",
            "液相线温度/℃",
            "过热度/℃",
            "中间包吨位平均值/t",
            "中间包吨位最大值/t",
            "中间包吨位最小值/t",
            "中间包吨位波动/t",
            "大包注入开始时钢水量/t",
            "大包注入结束时钢水量/t",
            "注入开始时TD钢水量/t",
            "注入结束时TD钢水量/t",
        ),
        "numeric",
    ),
    ColumnGroup(
        "casting_speed",
        (
            "拉速平均值/(m/min)",
            "拉速最大值/(m/min)",
            "拉速最小值/(m/min)",
            "拉速波动/(m/min)",
        ),
        "numeric",
    ),
    ColumnGroup(
        "mold_level",
        (
            "液面高度最大值/mm",
            "液面高度最小值/mm",
            "液面波动极差/mm",
            "液面波动均值/mm",
            "±3mm≤液面波动<±5mm的个数",
            "±5mm≤液面波动<±7mm的个数",
            "±3mm≤液面波动<±7mm的个数",
            "液面波动的个数≥±7mm",
            "液面波动的个数≥±10mm",
        ),
        "numeric",
    ),
    ColumnGroup(
        "nozzle_flow",
        (
            "上水口流量平均值/(L/min)",
            "上水口流量最大值/(L/min)",
            "上水口流量最小值/(L/min)",
            "上水口流量波动/(L/min)",
            "上滑板流量平均值/(L/min)",
            "上滑板流量最大值/(L/min)",
            "上滑板流量最小值/(L/min)",
            "上滑板流量波动/(L/min)",
        ),
        "numeric",
    ),
    ColumnGroup(
        "argon_and_pressure",
        (
            "上水口氩气压力平均值/kPa",
            "上水口氩气压力最大值/kPa",
            "上水口氩气压力最小值/kPa",
            "上水口氩气压力波动/kPa",
            "上滑板压力平均值/kPa",
            "上滑板压力最大值/kPa",
            "上滑板压力最小值/kPa",
            "塞棒氩气流量平均值/(L/min)",
            "塞棒氩气流量最大值/(L/min)",
            "塞棒氩气流量最小值/(L/min)",
            "塞棒氩气流量波动/(L/min)",
            "塞棒氩气压力平均值/kPa",
            "塞棒氩气压力最大值/kPa",
            "塞棒氩气压力最小值/kPa",
            "塞棒氩气压力波动/kPa",
        ),
        "numeric",
    ),
    ColumnGroup(
        "stopper",
        (
            "塞棒开口度平均值/mm",
            "塞棒开口度最大值/mm",
            "塞棒开口度最小值/mm",
        ),
        "numeric",
    ),
    ColumnGroup(
        "mold_heat_transfer",
        (
            "热交换平均(东)/℃",
            "热交换平均(西)/℃",
            "热交换平均(南)/℃",
            "热交换平均(北)/℃",
            "东西拔热量差/℃",
            "南北拔热量差/℃",
        ),
        "numeric",
    ),
    ColumnGroup(
        "mold_ems_taper_oscillation",
        (
            "结晶器电磁搅拌电流平均值/A",
            "结晶器电磁搅拌电流最大值/A",
            "结晶器电磁搅拌电流最小值/A",
            "结晶器电磁搅拌电流波动/A",
            "结晶器电磁搅拌频率平均值/Hz",
            "结晶器电磁搅拌频率最大值/Hz",
            "结晶器电磁搅拌频率最小值/Hz",
            "结晶器锥度北平均值/mm",
            "结晶器锥度北最大值/mm",
            "结晶器锥度北最小值/mm",
            "结晶器锥度南平均值/mm",
            "结晶器锥度南最大值/mm",
            "结晶器锥度南最小值/mm",
            "结晶器振动频率平均值/Hz",
            "结晶器振动频率最大值/Hz",
            "结晶器振动频率最小值/Hz",
            "结晶器振动负滑脱时间平均值/s",
            "结晶器振动负滑脱时间最大值/s",
            "结晶器振动负滑脱时间最小值/s",
        ),
        "numeric",
    ),
    ColumnGroup(
        "quality_label",
        (
            "品质异常处理组号",
            "品质异常代码1",
            "品质异常代码2",
            "品质异常代码3",
            "品质异常代码4",
            "品质异常代码5",
            "异常处置代码1",
            "异常处置代码2",
            "异常处置代码3",
            "异常处置代码4",
            "异常处置代码5",
            "热轧封锁标志",
            "HCR基准",
            "机清变更标记",
            "机清模式",
            "机清号",
            "机清次数",
            "板坯机清实绩",
        ),
        "label",
    ),
)


DERIVED_MODEL_COLUMNS = (
    "process_time",
    "defect_label",
    "defect_label_lock",
    "quality_abnormal_label",
    "quality_code_present_label",
    "quality_label",
    "quality_sample_role",
    "quality_label_source",
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


def continuous_casting_usecols() -> list[str]:
    seen: set[str] = set()
    cols: list[str] = []
    for group in CONTINUOUS_CASTING_GROUPS:
        for col in group.columns:
            if col not in seen:
                seen.add(col)
                cols.append(col)
    return cols


def _read_csv_with_fallback(
    file_path: str | Path,
    *,
    usecols: Sequence[str],
    nrows: int | None = None,
) -> pd.DataFrame:
    path = Path(file_path)
    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            return pd.read_csv(
                path,
                encoding=encoding,
                usecols=lambda c: c in set(usecols),
                na_values=RAW_NULL_VALUES,
                keep_default_na=True,
                low_memory=False,
                nrows=nrows,
            )
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise ValueError(f"Unable to read CSV: {path}")


def _parse_compact_datetime(s: pd.Series) -> pd.Series:
    text = s.astype("string").str.strip()
    compact = text.str.replace(r"\.0$", "", regex=True)
    out = pd.to_datetime(compact, format="%Y%m%d%H%M%S", errors="coerce")
    miss = out.isna()
    if bool(miss.any()):
        out.loc[miss] = pd.to_datetime(text.loc[miss], errors="coerce")
    return out


def _is_present_code(s: pd.Series) -> pd.Series:
    return s.map(lambda value: _normalize_quality_code(value) is not None).astype(bool)


def _normalize_quality_code(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if text.lower() in NULL_CODE_TEXT:
        return None
    if text.endswith(".0"):
        text = text[:-2]
    if text.lower() in NULL_CODE_TEXT:
        return None
    return text


def _quality_codes_for_row(row: pd.Series, quality_cols: Sequence[str]) -> list[str]:
    codes: list[str] = []
    seen: set[str] = set()
    for col in quality_cols:
        code = _normalize_quality_code(row.get(col))
        if code and code not in seen:
            codes.append(code)
            seen.add(code)
    return codes


def _quality_groups_for_codes(codes: Sequence[str]) -> list[str]:
    groups = {
        QUALITY_CODE_GROUPS.get(str(code), ("other_quality_abnormal", "其他品质异常类"))[0]
        for code in codes
    }
    return [group for group in QUALITY_GROUP_PRIORITY if group in groups]


def _quality_group_cn(group: str) -> str:
    if group == "no_quality_abnormal":
        return "无品质异常"
    for value in QUALITY_CODE_GROUPS.values():
        if value[0] == group:
            return value[1]
    return "其他品质异常类"


def _numeric(df: pd.DataFrame, col: str, default: float | None = None) -> pd.Series:
    if col not in df.columns:
        if default is None:
            return pd.Series(np.nan, index=df.index, dtype="float64")
        return pd.Series(float(default), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")


def load_continuous_casting_raw(
    file_path: str | Path,
    *,
    nrows: int | None = None,
) -> pd.DataFrame:
    df = _read_csv_with_fallback(
        file_path,
        usecols=continuous_casting_usecols(),
        nrows=nrows,
    )
    missing = [c for c in continuous_casting_usecols() if c not in df.columns]
    if missing:
        print(f"[continuous casting] skipped missing columns: {missing}")
    return df


def clean_continuous_casting_data(
    raw: pd.DataFrame,
    *,
    label_mode: str = "quality",
) -> pd.DataFrame:
    out = raw.copy()

    for group in CONTINUOUS_CASTING_GROUPS:
        existing = [c for c in group.columns if c in out.columns]
        if group.kind == "time":
            for col in existing:
                out[col] = _parse_compact_datetime(out[col])
        elif group.kind == "numeric":
            for col in existing:
                out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            for col in existing:
                out[col] = out[col].astype("string").fillna("missing").str.strip()

    out["process_time"] = (
        out["记录创建时间"]
        if "记录创建时间" in out.columns
        else pd.Series(pd.NaT, index=out.index)
    )

    quality_cols = [f"品质异常代码{i}" for i in range(1, 6) if f"品质异常代码{i}" in out.columns]
    quality_code_sets = [
        _quality_codes_for_row(row, quality_cols)
        for _, row in out.iterrows()
    ]
    quality_any_mask = pd.Series([bool(codes) for codes in quality_code_sets], index=out.index)

    if "热轧封锁标志" in out.columns:
        lock_mask = _is_present_code(out["热轧封锁标志"])
    else:
        lock_mask = pd.Series(False, index=out.index)

    group_sets = [
        _quality_groups_for_codes(codes)
        for codes in quality_code_sets
    ]
    target_mask = pd.Series(
        [any(group in TARGET_QUALITY_GROUPS for group in groups) for groups in group_sets],
        index=out.index,
    )
    clean_negative_mask = ~quality_any_mask

    out["quality_abnormal_label"] = target_mask.astype("int8")
    out["quality_code_present_label"] = quality_any_mask.astype("int8")
    out["quality_label"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out.loc[target_mask, "quality_label"] = 1
    out.loc[clean_negative_mask, "quality_label"] = 0
    out["quality_sample_role"] = "auxiliary_excluded"
    out.loc[target_mask, "quality_sample_role"] = "target_positive"
    out.loc[clean_negative_mask, "quality_sample_role"] = "clean_negative"
    out["quality_label_source"] = "quality_abnormal_code_1_5"
    out["defect_label_lock"] = lock_mask.astype("int8")
    out["quality_abnormal_codes"] = [
        ";".join(codes) if codes else "none"
        for codes in quality_code_sets
    ]
    out["quality_abnormal_groups"] = [";".join(groups) if groups else "none" for groups in group_sets]
    out["quality_abnormal_group"] = [
        groups[0] if groups else "no_quality_abnormal"
        for groups in group_sets
    ]
    out["quality_abnormal_group_cn"] = [
        _quality_group_cn(group) for group in out["quality_abnormal_group"].astype(str)
    ]
    for group in QUALITY_GROUP_PRIORITY:
        out[f"quality_group_{group}"] = [
            int(group in groups)
            for groups in group_sets
        ]

    mode = label_mode.strip().lower()
    if mode == "quality":
        out["defect_label"] = out["quality_abnormal_label"]
    elif mode == "either":
        out["defect_label"] = (target_mask | lock_mask).astype("int8")
    else:
        out["defect_label"] = out["defect_label_lock"]

    out["TD_weight_mean"] = _numeric(out, "中间包吨位平均值/t")
    out["TD_weight_range"] = _numeric(out, "中间包吨位波动/t")
    out["liquidus_temp"] = _numeric(out, "液相线温度/℃")
    out["superheat"] = _numeric(out, "过热度/℃")
    out["TD_avg_temp"] = out["liquidus_temp"] + out["superheat"]
    out["cast_speed_mean"] = _numeric(out, "拉速平均值/(m/min)")
    out["cast_speed_range"] = _numeric(out, "拉速波动/(m/min)")

    out["cover_flux_1"] = _numeric(out, "覆盖剂1使用量/ppm", 0.0).fillna(0.0)
    out["cover_flux_2"] = _numeric(out, "覆盖剂2使用量/ppm", 0.0).fillna(0.0)
    out["cover_flux_total"] = out["cover_flux_1"] + out["cover_flux_2"]
    out["cover_flux_ratio"] = out["cover_flux_2"] / out["cover_flux_total"].replace(0, np.nan)
    out["cover_flux_ratio"] = out["cover_flux_ratio"].fillna(0.0)

    out["mold_level_range"] = _numeric(out, "液面波动极差/mm")
    out["mold_level_mean"] = _numeric(out, "液面波动均值/mm")
    out["mold_level_ge7"] = _numeric(out, "液面波动的个数≥±7mm", 0.0).fillna(0.0)
    out["mold_level_ge10"] = _numeric(out, "液面波动的个数≥±10mm", 0.0).fillna(0.0)
    out["tundish_sequence_count"] = _numeric(out, "中间包连浇炉数")

    heat_cols = [c for c in ("热交换平均(东)/℃", "热交换平均(西)/℃", "热交换平均(南)/℃", "热交换平均(北)/℃") if c in out.columns]
    if heat_cols:
        out["heat_exchange_mean"] = out[heat_cols].mean(axis=1)
    else:
        out["heat_exchange_mean"] = np.nan
    out["heat_exchange_ew_diff"] = _numeric(out, "东西拔热量差/℃")
    out["heat_exchange_ns_diff"] = _numeric(out, "南北拔热量差/℃")

    if "process_time" in out.columns:
        out = out.sort_values("process_time", na_position="last").reset_index(drop=True)
    return out


def split_continuous_casting_by_group(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    key_cols = [c for c in ("process_time", "连铸处理号", "材料跟踪号", "记录识别码", "defect_label") if c in df.columns]
    tables: dict[str, pd.DataFrame] = {}
    for group in CONTINUOUS_CASTING_GROUPS:
        cols = key_cols + [c for c in group.columns if c in df.columns and c not in key_cols]
        if cols:
            tables[group.name] = df.loc[:, cols].copy()

    model_cols = [c for c in DERIVED_MODEL_COLUMNS if c in df.columns]
    tables["model_ready"] = df.loc[:, model_cols].copy()
    return tables


def summarize_continuous_casting_data(df: pd.DataFrame) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "time_min": None,
        "time_max": None,
        "labels": {},
        "groups": {},
    }
    if "process_time" in df.columns:
        t = pd.to_datetime(df["process_time"], errors="coerce")
        if int(t.notna().sum()):
            summary["time_min"] = str(t.min())
            summary["time_max"] = str(t.max())
    for col in ("defect_label", "defect_label_lock", "quality_abnormal_label", "quality_code_present_label", "quality_label", "quality_sample_role"):
        if col in df.columns:
            counts = df[col].value_counts(dropna=False).to_dict()
            summary["labels"][col] = {str(k): int(v) for k, v in counts.items()}

    for group in CONTINUOUS_CASTING_GROUPS:
        existing = [c for c in group.columns if c in df.columns]
        numeric_existing = [
            c for c in existing if pd.api.types.is_numeric_dtype(df[c])
        ]
        group_summary: dict[str, Any] = {
            "kind": group.kind,
            "columns": existing,
            "missing_ratio": {
                c: float(df[c].isna().mean()) for c in existing
            },
        }
        if numeric_existing:
            desc = df[numeric_existing].describe().transpose()
            group_summary["numeric_describe"] = {
                idx: {str(k): float(v) for k, v in row.dropna().items()}
                for idx, row in desc.iterrows()
            }
        summary["groups"][group.name] = group_summary
    return summary


def export_continuous_casting_tables(
    file_path: str | Path,
    output_dir: str | Path,
    *,
    label_mode: str = "quality",
    nrows: int | None = None,
) -> dict[str, Path]:
    raw = load_continuous_casting_raw(file_path, nrows=nrows)
    cleaned = clean_continuous_casting_data(raw, label_mode=label_mode)
    tables = split_continuous_casting_by_group(cleaned)
    summary = summarize_continuous_casting_data(cleaned)

    out_dir = Path(output_dir)
    category_dir = out_dir / "categories"
    category_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    all_path = out_dir / "continuous_casting_all.csv"
    cleaned.to_csv(all_path, index=False, encoding="utf-8-sig")
    paths["all"] = all_path

    for name, table in tables.items():
        path = category_dir / f"{name}.csv"
        table.to_csv(path, index=False, encoding="utf-8-sig")
        paths[name] = path

    summary_path = out_dir / "continuous_casting_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["summary"] = summary_path

    columns_path = out_dir / "continuous_casting_columns_by_group.json"
    columns_payload = {
        group.name: {
            "kind": group.kind,
            "columns": [c for c in group.columns if c in cleaned.columns],
        }
        for group in CONTINUOUS_CASTING_GROUPS
    }
    columns_path.write_text(json.dumps(columns_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["columns_by_group"] = columns_path
    return paths


def _default_raw_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "raw" / "baosteel_protection_slag_raw.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and clean continuous casting variables from raw flux data.")
    parser.add_argument("--input", default=str(_default_raw_path()), help="Raw CSV path.")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent.parent / "knowledge_exports" / "continuous_casting"),
        help="Output directory.",
    )
    parser.add_argument(
        "--label-mode",
        choices=("lock", "quality", "either"),
        default="quality",
        help="How to derive defect_label: lock=热轧封锁标志, quality=品质异常代码, either=union.",
    )
    parser.add_argument("--nrows", type=int, default=None, help="Optional row limit for quick checks.")
    args = parser.parse_args()

    paths = export_continuous_casting_tables(
        args.input,
        args.output,
        label_mode=args.label_mode,
        nrows=args.nrows,
    )
    print("continuous casting export completed:")
    for name, path in paths.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
