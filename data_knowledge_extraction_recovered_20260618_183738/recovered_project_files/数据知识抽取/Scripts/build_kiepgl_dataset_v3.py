from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v2"
DEFAULT_OUTPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v3"

LEAKAGE_KEYWORDS = (
    "quality",
    "label",
    "defect",
    "abnormal",
    "group",
    "disposition",
    "reason",
    "grade",
    "lock",
    "role",
    "consistency",
    "品质",
    "异常",
    "标签",
    "缺陷",
    "处置",
    "改钢",
    "等级",
    "封锁",
    "原因",
    "大类",
)

PREFERRED_FEATURES = {
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
    "cover_flux_zero_flag",
    "mold_level_range",
    "mold_level_mean",
    "mold_level_ge7",
    "mold_level_ge10",
    "tundish_sequence_count",
    "heat_exchange_mean",
    "heat_exchange_ew_diff",
    "heat_exchange_ns_diff",
}


def _is_ascii_identifier(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(name)))


def _feature_group(name: str) -> str:
    text = str(name).lower()
    if "flux" in text or "覆盖剂" in text:
        return "flux"
    if "td_" in text or "tundish" in text or "中间包" in text:
        return "tundish"
    if "speed" in text or "拉速" in text:
        return "casting_speed"
    if "mold_level" in text or "液面" in text:
        return "mold_level"
    if "flow" in text or "流量" in text:
        return "nozzle_flow"
    if "argon" in text or "pressure" in text or "氩" in text or "压力" in text:
        return "argon_and_pressure"
    if "stopper" in text or "塞棒" in text:
        return "stopper"
    if "heat" in text or "热" in text or "拔热" in text:
        return "mold_heat_transfer"
    if "oscillation" in text or "ems" in text or "锥度" in text or "振动" in text:
        return "mold_ems_taper_oscillation"
    return "derived_process" if _is_ascii_identifier(str(name)) else "raw_process"


def _find_duplicate_groups(
    numeric_x: pd.DataFrame,
    *,
    corr_threshold: float,
) -> list[list[str]]:
    cols = list(numeric_x.columns)
    if len(cols) < 2:
        return []
    valid = numeric_x.dropna(axis=1, how="all")
    valid = valid.loc[:, valid.nunique(dropna=True) > 1]
    if valid.shape[1] < 2:
        return []
    corr = valid.corr(numeric_only=True).abs()
    parent = {col: col for col in valid.columns}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    arr_cols = list(valid.columns)
    for i, left in enumerate(arr_cols):
        for right in arr_cols[i + 1 :]:
            value = corr.loc[left, right]
            if pd.notna(value) and float(value) >= float(corr_threshold):
                union(left, right)
    groups: dict[str, list[str]] = {}
    for col in arr_cols:
        groups.setdefault(find(col), []).append(col)
    return [members for members in groups.values() if len(members) > 1]


def _choose_keeper(group: list[str], missing_rate: pd.Series) -> str:
    def rank(col: str) -> tuple[int, float, int, str]:
        preferred = 0 if col in PREFERRED_FEATURES else 1
        ascii_rank = 0 if _is_ascii_identifier(col) else 1
        return (preferred + ascii_rank, float(missing_rate.get(col, 1.0)), len(col), col)

    return sorted(group, key=rank)[0]


def curate_features(
    x: pd.DataFrame,
    *,
    high_missing_threshold: float = 0.20,
    corr_threshold: float = 0.999,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if "record_id" not in x.columns:
        raise ValueError("X_process_features.csv must contain record_id.")
    feature_cols = [c for c in x.columns if c != "record_id"]
    numeric = x[feature_cols].apply(pd.to_numeric, errors="coerce")
    missing_rate = numeric.isna().mean()
    high_missing_cols = sorted(missing_rate[missing_rate >= float(high_missing_threshold)].index.tolist())
    constant_cols = sorted([c for c in numeric.columns if numeric[c].nunique(dropna=True) <= 1])
    leakage_cols = sorted(
        [
            c
            for c in feature_cols
            if any(keyword.lower() in str(c).lower() for keyword in LEAKAGE_KEYWORDS)
        ]
    )

    duplicate_groups = _find_duplicate_groups(
        numeric.drop(columns=high_missing_cols + constant_cols + leakage_cols, errors="ignore"),
        corr_threshold=float(corr_threshold),
    )
    keepers: dict[str, str] = {}
    duplicate_drop: list[str] = []
    duplicate_manifest: list[dict[str, Any]] = []
    for group in duplicate_groups:
        keeper = _choose_keeper(group, missing_rate)
        keepers[keeper] = keeper
        drops = sorted([col for col in group if col != keeper])
        duplicate_drop.extend(drops)
        duplicate_manifest.append(
            {
                "keeper": keeper,
                "dropped": drops,
                "reason": f"abs(corr)>={corr_threshold}; keep standard/low-missing feature",
            }
        )

    drop_cols = sorted(set(high_missing_cols + constant_cols + leakage_cols + duplicate_drop))
    curated_cols = [col for col in feature_cols if col not in set(drop_cols)]
    out = pd.concat([x[["record_id"]], numeric[curated_cols]], axis=1)

    feature_rows = []
    for col in curated_cols:
        feature_rows.append(
            {
                "feature": col,
                "group": _feature_group(col),
                "missing_rate": float(missing_rate.get(col, 0.0)),
                "kept": True,
                "source": "preferred_standard" if col in PREFERRED_FEATURES else "raw_or_process_numeric",
            }
        )
    manifest = {
        "input_feature_count": int(len(feature_cols)),
        "output_feature_count": int(len(curated_cols)),
        "removed_feature_count": int(len(drop_cols)),
        "high_missing_threshold": float(high_missing_threshold),
        "duplicate_corr_threshold": float(corr_threshold),
        "removed_features": {
            "high_missing": high_missing_cols,
            "constant": constant_cols,
            "leakage_name_candidates": leakage_cols,
            "duplicate_aliases": sorted(set(duplicate_drop)),
        },
        "duplicate_groups": duplicate_manifest,
        "feature_groups": {
            group: int(sum(1 for row in feature_rows if row["group"] == group))
            for group in sorted({row["group"] for row in feature_rows})
        },
        "features": feature_rows,
    }
    return out, manifest


def build_kiepgl_dataset_v3(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    high_missing_threshold: float = 0.20,
    corr_threshold: float = 0.999,
) -> dict[str, Any]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    x = pd.read_csv(input_dir / "X_process_features.csv", low_memory=False)
    y = pd.read_csv(input_dir / "y_quality_label.csv", low_memory=False)
    xy = pd.read_csv(input_dir / "xy_quality_traceability.csv", low_memory=False)
    aux = pd.read_csv(input_dir / "auxiliary_quality_events.csv", low_memory=False)
    invalid = pd.read_csv(input_dir / "invalid_data_quality_rows.csv", low_memory=False)

    curated_x, manifest = curate_features(
        x,
        high_missing_threshold=high_missing_threshold,
        corr_threshold=corr_threshold,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    curated_cols = [c for c in curated_x.columns if c != "record_id"]
    y_cols = list(y.columns)
    xy_out = xy[[c for c in y_cols if c in xy.columns] + [c for c in curated_cols if c in xy.columns]].copy()
    feature_groups = {
        group: [str(row["feature"]) for row in manifest["features"] if row["group"] == group]
        for group in sorted({str(row["group"]) for row in manifest["features"]})
    }

    curated_x.to_csv(output_dir / "X_process_features.csv", index=False, encoding="utf-8-sig")
    y.to_csv(output_dir / "y_quality_label.csv", index=False, encoding="utf-8-sig")
    xy_out.to_csv(output_dir / "xy_quality_traceability.csv", index=False, encoding="utf-8-sig")
    aux.to_csv(output_dir / "auxiliary_quality_events.csv", index=False, encoding="utf-8-sig")
    invalid.to_csv(output_dir / "invalid_data_quality_rows.csv", index=False, encoding="utf-8-sig")
    (output_dir / "feature_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "feature_groups.json").write_text(
        json.dumps(feature_groups, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for name in ("label_mapping.json",):
        src = input_dir / name
        if src.exists():
            (output_dir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    summary = {
        "source_dir": str(input_dir),
        "dataset_version": "v3_kiepgl_audited_features",
        "n_rows": int(len(y)),
        "n_x_features": int(len(curated_cols)),
        "n_features_removed": int(manifest["removed_feature_count"]),
        "removed_features": manifest["removed_features"],
        "feature_groups": {group: len(cols) for group, cols in feature_groups.items()},
        "outputs": {
            "X_process_features": str(output_dir / "X_process_features.csv"),
            "y_quality_label": str(output_dir / "y_quality_label.csv"),
            "xy_quality_traceability": str(output_dir / "xy_quality_traceability.csv"),
            "feature_manifest": str(output_dir / "feature_manifest.json"),
        },
    }
    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "# KIEP-GL v3 Dataset",
                "",
                "This dataset is derived from quality_traceability_dataset_v2.",
                "It removes high-missing process fields, constant fields, leakage-name candidates, and duplicate raw/derived feature aliases.",
                "",
                "Use `X_process_features.csv` and `y_quality_label.csv` for the main KIEP-GL experiments.",
                "Use `feature_manifest.json` to audit every kept and removed feature decision.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build audited KIEP-GL v3 dataset from v2 exports.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--high-missing-threshold", type=float, default=0.20)
    parser.add_argument("--corr-threshold", type=float, default=0.999)
    args = parser.parse_args()
    summary = build_kiepgl_dataset_v3(
        Path(args.input_dir),
        Path(args.output_dir),
        high_missing_threshold=float(args.high_missing_threshold),
        corr_threshold=float(args.corr_threshold),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
