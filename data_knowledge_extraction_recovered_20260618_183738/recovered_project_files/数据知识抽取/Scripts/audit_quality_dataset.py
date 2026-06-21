from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v3"
DEFAULT_REPORT_PATH = ROOT / "docs" / "data_quality_audit_report.md"

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
    "source",
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


def pct(value: float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:.2%}"


def read_csv(dataset_dir: Path, name: str) -> pd.DataFrame:
    path = dataset_dir / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def safe_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def count_mojibake(values: list[str]) -> int:
    markers = ("�", "锟", "鏁", "鍝", "涓", "鎷", "鐑", "娑", "濉", "鈩")
    return sum(any(marker in str(value) for marker in markers) for value in values)


def _high_corr_pairs(numeric_x: pd.DataFrame, threshold: float = 0.995) -> list[tuple[str, str, float]]:
    clean = numeric_x.dropna(axis=1, how="all")
    clean = clean.loc[:, clean.nunique(dropna=True) > 1]
    if clean.shape[1] < 2:
        return []
    corr = clean.corr(numeric_only=True).abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    stacked = upper.stack().sort_values(ascending=False)
    rows: list[tuple[str, str, float]] = []
    for (left, right), value in stacked.head(40).items():
        if pd.notna(value) and float(value) >= threshold:
            rows.append((str(left), str(right), float(value)))
    return rows


def audit_quality_dataset(
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    report_path = Path(report_path)
    x = read_csv(dataset_dir, "X_process_features.csv")
    y = read_csv(dataset_dir, "y_quality_label.csv")
    xy = read_csv(dataset_dir, "xy_quality_traceability.csv")
    aux = read_csv(dataset_dir, "auxiliary_quality_events.csv")
    invalid = read_csv(dataset_dir, "invalid_data_quality_rows.csv")
    summary = safe_json(dataset_dir / "dataset_summary.json")
    manifest = safe_json(dataset_dir / "feature_manifest.json")

    if x.empty or y.empty:
        raise FileNotFoundError(f"Dataset is incomplete: {dataset_dir}")

    id_col = "record_id"
    x_ids = x[id_col] if id_col in x.columns else pd.Series(dtype=object)
    y_ids = y[id_col] if id_col in y.columns else pd.Series(dtype=object)
    feature_cols = [c for c in x.columns if c != id_col]
    numeric_x = x[feature_cols].apply(pd.to_numeric, errors="coerce")
    label = pd.to_numeric(y.get("quality_label"), errors="coerce")
    role = y.get("quality_sample_role", pd.Series(dtype=object))

    missing_rate = numeric_x.isna().mean().sort_values(ascending=False)
    high_missing = missing_rate[missing_rate >= 0.20]
    moderate_missing = missing_rate[(missing_rate >= 0.05) & (missing_rate < 0.20)]
    zero_var = [col for col in numeric_x.columns if numeric_x[col].nunique(dropna=True) <= 1]
    leakage_candidates = [
        col for col in x.columns if any(keyword.lower() in str(col).lower() for keyword in LEAKAGE_KEYWORDS)
    ]
    corr_pairs = _high_corr_pairs(numeric_x, threshold=0.995)
    total_cells = int(numeric_x.shape[0] * numeric_x.shape[1])
    nan_cells = int(numeric_x.isna().sum().sum())
    inf_cells = int(np.isinf(numeric_x.to_numpy(dtype=float, na_value=np.nan)).sum())

    alignment = {
        "x_rows": int(len(x)),
        "y_rows": int(len(y)),
        "xy_rows": int(len(xy)),
        "x_y_same_order": bool(x_ids.equals(y_ids)) if len(x_ids) and len(y_ids) else False,
        "x_minus_y_ids": int(len(set(x_ids) - set(y_ids))) if len(x_ids) and len(y_ids) else None,
        "y_minus_x_ids": int(len(set(y_ids) - set(x_ids))) if len(x_ids) and len(y_ids) else None,
        "x_duplicate_record_id": int(x_ids.duplicated().sum()) if len(x_ids) else None,
        "y_duplicate_record_id": int(y_ids.duplicated().sum()) if len(y_ids) else None,
    }
    label_counts = label.value_counts(dropna=False).sort_index().to_dict()
    role_counts = role.value_counts(dropna=False).to_dict()
    group_counts = (
        y["quality_abnormal_group"].value_counts(dropna=False).head(20).to_dict()
        if "quality_abnormal_group" in y.columns
        else {}
    )
    positive_rate = float((label == 1).mean())
    column_mojibake = {
        "x_columns_with_mojibake": count_mojibake(list(x.columns)),
        "y_columns_with_mojibake": count_mojibake(list(y.columns)),
        "summary_x_columns_with_mojibake": count_mojibake(summary.get("x_feature_columns", [])),
        "manifest_features_with_mojibake": count_mojibake(
            [row.get("feature", "") for row in manifest.get("features", []) if isinstance(row, dict)]
        ),
    }

    pass_flags = {
        "alignment_pass": bool(alignment["x_y_same_order"] and alignment["x_minus_y_ids"] == 0 and alignment["y_minus_x_ids"] == 0),
        "no_duplicate_ids": bool((alignment["x_duplicate_record_id"] or 0) == 0 and (alignment["y_duplicate_record_id"] or 0) == 0),
        "no_leakage_name_candidates": len(leakage_candidates) == 0,
        "no_high_missing_features": len(high_missing) == 0,
        "no_constant_features": len(zero_var) == 0,
        "low_missing_rate": (nan_cells / total_cells if total_cells else 0.0) < 0.05,
    }

    lines: list[str] = []
    lines.append("# Data Quality Audit Report\n")
    lines.append("## Scope\n")
    lines.append(f"- Dataset directory: `{dataset_dir}`")
    lines.append("- Main X: `X_process_features.csv`")
    lines.append("- Main y: `y_quality_label.csv`")
    lines.append("- Wide table: `xy_quality_traceability.csv`")
    lines.append("- Auxiliary rows: `auxiliary_quality_events.csv`")
    lines.append("- Physically invalid rows: `invalid_data_quality_rows.csv`\n")

    lines.append("## Executive Summary\n")
    lines.append(f"- Main modeling rows: **{len(y):,}**.")
    lines.append(f"- X features: **{len(feature_cols):,}**.")
    lines.append(f"- Positive rows: **{int((label == 1).sum()):,}**; negative rows: **{int((label == 0).sum()):,}**; positive rate: **{pct(positive_rate)}**.")
    lines.append(f"- Auxiliary excluded rows: **{len(aux):,}**; physically invalid excluded rows: **{len(invalid):,}**.")
    lines.append(f"- Missing cells: **{nan_cells:,} / {total_cells:,}** ({pct(nan_cells / total_cells if total_cells else 0.0)}).")
    lines.append(f"- High-missing features: **{len(high_missing)}**; constant features: **{len(zero_var)}**; leakage-name candidates: **{len(leakage_candidates)}**.")
    if manifest:
        lines.append(f"- v3 curation removed **{manifest.get('removed_feature_count', 0)}** features from **{manifest.get('input_feature_count', len(feature_cols))}** input features.")
    lines.append("")

    lines.append("## Pass/Warning Checklist\n")
    lines.append("| Check | Result |")
    lines.append("|---|---:|")
    for key, value in pass_flags.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")

    lines.append("## Label Distribution\n")
    lines.append("| quality_label | Count |")
    lines.append("|---|---:|")
    for key, value in label_counts.items():
        lines.append(f"| {key} | {int(value):,} |")
    lines.append("")
    lines.append("| quality_sample_role | Count |")
    lines.append("|---|---:|")
    for key, value in role_counts.items():
        lines.append(f"| {key} | {int(value):,} |")
    lines.append("")
    lines.append("| quality_abnormal_group | Count |")
    lines.append("|---|---:|")
    for key, value in group_counts.items():
        lines.append(f"| {key} | {int(value):,} |")
    lines.append("")

    lines.append("## Alignment and ID Checks\n")
    lines.append("| Check | Value |")
    lines.append("|---|---:|")
    for key, value in alignment.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")

    lines.append("## Missingness and Numeric Validity\n")
    lines.append("| Check | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Total feature cells | {total_cells:,} |")
    lines.append(f"| NaN cells | {nan_cells:,} |")
    lines.append(f"| NaN cell rate | {pct(nan_cells / total_cells if total_cells else 0.0)} |")
    lines.append(f"| +/-inf cells | {inf_cells:,} |")
    lines.append(f"| Features with missing rate >= 20% | {len(high_missing):,} |")
    lines.append(f"| Features with 5% <= missing rate < 20% | {len(moderate_missing):,} |")
    lines.append(f"| Constant features | {len(zero_var):,} |")
    lines.append("")
    if len(high_missing):
        lines.append("### High-missing Features\n")
        lines.append("| Feature | Missing rate |")
        lines.append("|---|---:|")
        for col, value in high_missing.head(40).items():
            lines.append(f"| `{col}` | {pct(float(value))} |")
        lines.append("")

    lines.append("## High-correlation Feature Pairs\n")
    if corr_pairs:
        lines.append("| Feature A | Feature B | abs(corr) |")
        lines.append("|---|---|---:|")
        for left, right, value in corr_pairs:
            lines.append(f"| `{left}` | `{right}` | {value:.4f} |")
    else:
        lines.append("No feature pairs with abs(corr) >= 0.995 were found.")
    lines.append("")

    lines.append("## Leakage Name Check\n")
    if leakage_candidates:
        lines.append("The following X columns match leakage-related keywords and require review:")
        for col in leakage_candidates:
            lines.append(f"- `{col}`")
    else:
        lines.append("No X columns match label, quality, disposition, steel-change, grade, or lock leakage keywords.")
    lines.append("")

    lines.append("## v3 Feature Curation Summary\n")
    if manifest:
        removed = manifest.get("removed_features", {})
        lines.append("| Removed class | Count |")
        lines.append("|---|---:|")
        for key, values in removed.items():
            lines.append(f"| {key} | {len(values) if isinstance(values, list) else 0} |")
        lines.append("")
        lines.append("### Duplicate Alias Decisions\n")
        groups = manifest.get("duplicate_groups", [])
        if groups:
            lines.append("| Kept feature | Dropped aliases |")
            lines.append("|---|---|")
            for row in groups[:40]:
                lines.append(f"| `{row.get('keeper')}` | {', '.join(f'`{x}`' for x in row.get('dropped', []))} |")
        else:
            lines.append("No duplicate alias groups were removed.")
        lines.append("")
    else:
        lines.append("No `feature_manifest.json` was found. Run `build_kiepgl_dataset_v3.py` for curation details.")
        lines.append("")

    lines.append("## Encoding and Reproducibility\n")
    lines.append("| Check | Count |")
    lines.append("|---|---:|")
    for key, value in column_mojibake.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")

    lines.append("## Modeling Recommendation\n")
    lines.append("1. Use the v3 dataset for KIEP-GL experiments because duplicate raw/derived feature aliases and high-missing fields have been removed.")
    lines.append("2. Keep `target_positive` and `clean_negative` as the main binary task; keep auxiliary rows outside the main classifier.")
    lines.append("3. Use time-ordered or process-sequence grouped splits to avoid adjacent-record leakage.")
    lines.append("4. Report AUC-PR, event recall, average lead time, false alarm rate, path hit rate, and knowledge consistency.")
    lines.append("5. Keep `feature_manifest.json` with experiment artifacts so every X decision is traceable.")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = {
        "dataset_dir": str(dataset_dir),
        "report": str(report_path),
        "x_rows": int(len(x)),
        "y_rows": int(len(y)),
        "x_features": int(len(feature_cols)),
        "positive_rate": positive_rate,
        "alignment": alignment,
        "nan_cell_rate": float(nan_cells / total_cells if total_cells else 0.0),
        "high_missing_count": int(len(high_missing)),
        "zero_var_count": int(len(zero_var)),
        "leakage_candidate_count": int(len(leakage_candidates)),
        "high_corr_pair_count": int(len(corr_pairs)),
        "pass_flags": pass_flags,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit an exported quality traceability dataset.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()
    audit_quality_dataset(Path(args.dataset_dir), Path(args.report_path))


if __name__ == "__main__":
    main()
