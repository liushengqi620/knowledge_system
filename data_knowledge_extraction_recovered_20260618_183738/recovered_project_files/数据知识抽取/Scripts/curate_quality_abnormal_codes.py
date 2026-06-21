from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "knowledge_exports" / "continuous_casting_grouped" / "categories" / "quality_label.csv"
DEFAULT_MAPPING = ROOT / "knowledge_exports" / "continuous_casting_grouped" / "quality_abnormal_group_mapping.json"
DEFAULT_OUT = ROOT / "knowledge_exports" / "quality_code_curation_v1"
CODE_COLUMNS = [f"品质异常代码{i}" for i in range(1, 6)]

GROUP_NAME_FALLBACK = {
    "mold_level_slag_risk": "液面/卷渣风险类",
    "process_fluctuation": "强过程波动类",
    "speed_stopper_flow": "拉速-塞棒/流量控制类",
    "heat_transfer_imbalance": "热交换不均类",
    "transition_tundish": "交接段/中间包过渡类",
    "temperature_flux": "温度/保护剂相关类",
    "other_quality_abnormal": "其他品质异常类",
}


def normalize_code(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "missing"}:
        return None
    try:
        code = int(float(text))
    except ValueError:
        return None
    return None if code == 0 else str(code)


def load_code_mapping(path: Path) -> dict[str, dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict[str, dict[str, str]] = {}
    for group, info in raw.items():
        group_cn = info.get("name_cn") or GROUP_NAME_FALLBACK.get(group, group)
        for code in info.get("codes", []):
            mapping[str(code)] = {"group": group, "group_cn": group_cn}
    return mapping


def row_codes(row: pd.Series) -> list[str]:
    codes: list[str] = []
    seen: set[str] = set()
    for col in CODE_COLUMNS:
        code = normalize_code(row[col])
        if code is not None and code not in seen:
            codes.append(code)
            seen.add(code)
    return codes


def build_support_table(df: pd.DataFrame, mapping: dict[str, dict[str, str]], min_count: int) -> pd.DataFrame:
    row_counter: Counter[str] = Counter()
    appearance_counter: Counter[str] = Counter()
    slot_counter: dict[str, Counter[str]] = {col: Counter() for col in CODE_COLUMNS}

    for _, row in df[CODE_COLUMNS].iterrows():
        codes = row_codes(row)
        row_counter.update(codes)
        for col in CODE_COLUMNS:
            code = normalize_code(row[col])
            if code is not None:
                appearance_counter[code] += 1
                slot_counter[col][code] += 1

    rows: list[dict[str, object]] = []
    for code, row_count in sorted(row_counter.items(), key=lambda item: int(item[0])):
        info = mapping.get(code, {"group": "unmapped_low_frequency", "group_cn": "未归类/低频"})
        slot_counts = {f"{col}_count": slot_counter[col][code] for col in CODE_COLUMNS}
        keep = row_count >= min_count
        rows.append(
            {
                "code": code,
                "row_count": row_count,
                "row_rate": row_count / len(df),
                "appearance_count": appearance_counter[code],
                "avg_appearance_per_positive_row": appearance_counter[code] / row_count,
                "group": info["group"],
                "group_cn": info["group_cn"],
                "is_analyzable": int(keep),
                "curation_reason": "enough_support" if keep else f"low_support_lt_{min_count}",
                **slot_counts,
            }
        )
    return pd.DataFrame(rows)


def curate_rows(df: pd.DataFrame, support: pd.DataFrame) -> pd.DataFrame:
    keep_codes = set(support.loc[support["is_analyzable"] == 1, "code"].astype(str))
    code_to_group = support.set_index("code")["group"].to_dict()
    code_to_group_cn = support.set_index("code")["group_cn"].to_dict()

    out = df.copy()
    original_sets: list[str] = []
    kept_sets: list[str] = []
    removed_sets: list[str] = []
    group_sets: list[str] = []
    group_cn_sets: list[str] = []
    n_original: list[int] = []
    n_kept: list[int] = []
    n_removed: list[int] = []
    roles: list[str] = []
    labels: list[float | None] = []

    for _, row in df[CODE_COLUMNS].iterrows():
        codes = row_codes(row)
        kept = [code for code in codes if code in keep_codes]
        removed = [code for code in codes if code not in keep_codes]
        groups = sorted({code_to_group.get(code, "unmapped_low_frequency") for code in kept})
        groups_cn = sorted({code_to_group_cn.get(code, "未归类/低频") for code in kept})

        original_sets.append(";".join(codes) if codes else "no_quality_abnormal")
        kept_sets.append(";".join(kept) if kept else "no_analyzable_quality_code")
        removed_sets.append(";".join(removed) if removed else "none")
        group_sets.append(";".join(groups) if groups else "no_analyzable_quality_code")
        group_cn_sets.append(";".join(groups_cn) if groups_cn else "无可分析品质异常")
        n_original.append(len(codes))
        n_kept.append(len(kept))
        n_removed.append(len(removed))

        if not codes:
            roles.append("clean_negative")
            labels.append(0.0)
        elif kept:
            roles.append("analyzable_positive" if not removed else "mixed_trimmed_positive")
            labels.append(1.0)
        else:
            roles.append("low_support_only_auxiliary")
            labels.append(None)

    out["quality_codes_original"] = original_sets
    out["quality_codes_analyzable"] = kept_sets
    out["quality_codes_low_support_removed"] = removed_sets
    out["quality_code_group_set_analyzable"] = group_sets
    out["quality_code_group_cn_set_analyzable"] = group_cn_sets
    out["n_quality_codes_original"] = n_original
    out["n_quality_codes_analyzable"] = n_kept
    out["n_quality_codes_low_support_removed"] = n_removed
    out["quality_code_curation_role"] = roles
    out["quality_code_analyzable_label"] = labels
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--min-count", type=int, default=500)
    args = parser.parse_args()

    df = pd.read_csv(args.input, low_memory=False)
    missing = [col for col in CODE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"missing code columns: {missing}")

    mapping = load_code_mapping(args.mapping)
    support = build_support_table(df, mapping, args.min_count)
    curated = curate_rows(df, support)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    support_path = args.out_dir / "quality_code_support.csv"
    curated_path = args.out_dir / "quality_label_analyzable_codes.csv"
    keep_path = args.out_dir / "analyzable_quality_codes.json"
    summary_path = args.out_dir / "dataset_summary.json"

    support.to_csv(support_path, index=False, encoding="utf-8-sig")
    curated.to_csv(curated_path, index=False, encoding="utf-8-sig")

    analyzable = support[support["is_analyzable"] == 1].copy()
    low_support = support[support["is_analyzable"] == 0].copy()
    role_counts = curated["quality_code_curation_role"].value_counts(dropna=False).to_dict()
    group_counts = (
        analyzable.groupby(["group", "group_cn"])["row_count"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .to_dict(orient="records")
    )

    keep_payload = {
        "min_count": args.min_count,
        "n_analyzable_codes": int(len(analyzable)),
        "n_low_support_codes": int(len(low_support)),
        "analyzable_codes": analyzable["code"].astype(str).tolist(),
        "low_support_codes": low_support["code"].astype(str).tolist(),
    }
    keep_path.write_text(json.dumps(keep_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "input": str(args.input),
        "n_rows": int(len(df)),
        "min_count": args.min_count,
        "n_unique_quality_codes": int(len(support)),
        "n_analyzable_quality_codes": int(len(analyzable)),
        "n_low_support_quality_codes": int(len(low_support)),
        "n_rows_clean_negative": int(role_counts.get("clean_negative", 0)),
        "n_rows_analyzable_positive": int(role_counts.get("analyzable_positive", 0)),
        "n_rows_mixed_trimmed_positive": int(role_counts.get("mixed_trimmed_positive", 0)),
        "n_rows_low_support_only_auxiliary": int(role_counts.get("low_support_only_auxiliary", 0)),
        "role_counts": role_counts,
        "top_analyzable_codes": analyzable.sort_values("row_count", ascending=False)
        .head(20)[["code", "row_count", "row_rate", "group", "group_cn"]]
        .to_dict(orient="records"),
        "low_support_codes": low_support.sort_values("row_count", ascending=False)[
            ["code", "row_count", "row_rate", "group", "group_cn"]
        ].to_dict(orient="records"),
        "group_row_count_sum_among_analyzable_codes": group_counts,
        "outputs": {
            "quality_code_support": str(support_path),
            "quality_label_analyzable_codes": str(curated_path),
            "analyzable_quality_codes": str(keep_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"output_dir={args.out_dir}")
    print(f"n_rows={len(df)}")
    print(f"n_unique_codes={len(support)}")
    print(f"n_analyzable_codes={len(analyzable)}")
    print(f"n_low_support_codes={len(low_support)}")
    print(f"role_counts={role_counts}")
    print(f"support={support_path}")
    print(f"curated={curated_path}")
    print(f"summary={summary_path}")


if __name__ == "__main__":
    main()
