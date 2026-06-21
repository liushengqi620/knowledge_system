from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CURATION_DIR = ROOT / "knowledge_exports" / "quality_code_curation_v1"
SUPPORT_IN = CURATION_DIR / "quality_code_support.csv"
LABEL_IN = CURATION_DIR / "quality_label_analyzable_codes.csv"
OUT_DIR = ROOT / "knowledge_exports" / "quality_code_curation_v1_classified"


CODE_CLASSIFICATION: dict[str, dict[str, str]] = {
    # Transition / state-like high-frequency quality event codes.
    "94": {"macro_class": "transition_or_quality_state", "model_role": "auxiliary_context", "core_quality": "0"},
    "21": {"macro_class": "transition_or_quality_state", "model_role": "auxiliary_context", "core_quality": "0"},
    "41": {"macro_class": "transition_or_quality_state", "model_role": "auxiliary_context", "core_quality": "0"},
    "42": {"macro_class": "transition_or_quality_state", "model_role": "auxiliary_context", "core_quality": "0"},
    "43": {"macro_class": "transition_or_quality_state", "model_role": "auxiliary_context", "core_quality": "0"},
    "58": {"macro_class": "transition_or_quality_state", "model_role": "auxiliary_context", "core_quality": "0"},
    "87": {"macro_class": "transition_or_quality_state", "model_role": "auxiliary_context", "core_quality": "0"},
    # Core quality-risk codes.
    "24": {"macro_class": "temperature_flux_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "15": {"macro_class": "temperature_flux_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "27": {"macro_class": "temperature_flux_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "33": {"macro_class": "temperature_flux_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "69": {"macro_class": "temperature_flux_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "70": {"macro_class": "temperature_flux_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "29": {"macro_class": "mold_level_slag_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "30": {"macro_class": "mold_level_slag_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "31": {"macro_class": "mold_level_slag_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "32": {"macro_class": "mold_level_slag_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "37": {"macro_class": "mold_level_slag_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "54": {"macro_class": "mold_level_slag_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "86": {"macro_class": "mold_level_slag_quality", "model_role": "core_quality_target", "core_quality": "1"},
    "38": {"macro_class": "heat_transfer_quality", "model_role": "core_quality_target", "core_quality": "1"},
    # Process parameter / control anomaly codes.
    "18": {"macro_class": "process_parameter_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "19": {"macro_class": "process_parameter_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "39": {"macro_class": "process_parameter_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "55": {"macro_class": "process_parameter_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "56": {"macro_class": "process_parameter_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "83": {"macro_class": "process_parameter_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "34": {"macro_class": "flow_control_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "51": {"macro_class": "flow_control_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "52": {"macro_class": "flow_control_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "57": {"macro_class": "flow_control_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "85": {"macro_class": "flow_control_anomaly", "model_role": "process_precursor", "core_quality": "0"},
    "89": {"macro_class": "flow_control_anomaly", "model_role": "process_precursor", "core_quality": "0"},
}

MACRO_CLASS_CN = {
    "transition_or_quality_state": "交接过渡/质量状态类",
    "temperature_flux_quality": "温度/保护剂质量类",
    "mold_level_slag_quality": "液面/卷渣质量类",
    "heat_transfer_quality": "传热不均质量类",
    "process_parameter_anomaly": "过程参数异常类",
    "flow_control_anomaly": "拉速-塞棒/流量控制异常类",
    "low_support_or_unmapped": "低支持/未归类",
}

MODEL_ROLE_CN = {
    "core_quality_target": "核心质量异常目标",
    "process_precursor": "过程异常前兆",
    "auxiliary_context": "辅助状态/过渡上下文",
    "low_support_auxiliary": "低支持辅助",
}


def split_codes(value: object) -> list[str]:
    if pd.isna(value):
        return []
    text = str(value).strip()
    if text in {"", "none", "no_quality_abnormal", "no_analyzable_quality_code"}:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def classify_code(code: str) -> dict[str, str]:
    if code in CODE_CLASSIFICATION:
        item = dict(CODE_CLASSIFICATION[code])
    else:
        item = {"macro_class": "low_support_or_unmapped", "model_role": "low_support_auxiliary", "core_quality": "0"}
    item["macro_class_cn"] = MACRO_CLASS_CN[item["macro_class"]]
    item["model_role_cn"] = MODEL_ROLE_CN[item["model_role"]]
    return item


def joined(values: set[str]) -> str:
    return ";".join(sorted(values)) if values else "none"


def main() -> None:
    support = pd.read_csv(SUPPORT_IN, dtype={"code": str})
    labels = pd.read_csv(LABEL_IN, low_memory=False)

    class_rows: list[dict[str, object]] = []
    for _, row in support.iterrows():
        code = str(row["code"])
        cls = classify_code(code)
        class_rows.append(
            {
                "code": code,
                "row_count": int(row["row_count"]),
                "row_rate": float(row["row_rate"]),
                "is_analyzable": int(row["is_analyzable"]),
                "original_group": row["group"],
                "original_group_cn": row["group_cn"],
                **cls,
            }
        )

    class_df = pd.DataFrame(class_rows)
    class_df["core_quality"] = class_df["core_quality"].astype(int)
    code_to_cls = class_df.set_index("code").to_dict(orient="index")

    macro_sets: list[str] = []
    macro_cn_sets: list[str] = []
    role_sets: list[str] = []
    role_cn_sets: list[str] = []
    core_code_sets: list[str] = []
    precursor_code_sets: list[str] = []
    state_code_sets: list[str] = []
    core_labels: list[int] = []
    precursor_labels: list[int] = []
    state_labels: list[int] = []

    for value in labels["quality_codes_analyzable"]:
        codes = split_codes(value)
        macros: set[str] = set()
        macros_cn: set[str] = set()
        roles: set[str] = set()
        roles_cn: set[str] = set()
        core_codes: set[str] = set()
        precursor_codes: set[str] = set()
        state_codes: set[str] = set()
        for code in codes:
            cls = code_to_cls.get(code, classify_code(code))
            macros.add(str(cls["macro_class"]))
            macros_cn.add(str(cls["macro_class_cn"]))
            roles.add(str(cls["model_role"]))
            roles_cn.add(str(cls["model_role_cn"]))
            if cls["model_role"] == "core_quality_target":
                core_codes.add(code)
            elif cls["model_role"] == "process_precursor":
                precursor_codes.add(code)
            elif cls["model_role"] == "auxiliary_context":
                state_codes.add(code)

        macro_sets.append(joined(macros))
        macro_cn_sets.append(joined(macros_cn))
        role_sets.append(joined(roles))
        role_cn_sets.append(joined(roles_cn))
        core_code_sets.append(joined(core_codes))
        precursor_code_sets.append(joined(precursor_codes))
        state_code_sets.append(joined(state_codes))
        core_labels.append(int(bool(core_codes)))
        precursor_labels.append(int(bool(precursor_codes)))
        state_labels.append(int(bool(state_codes)))

    out = labels.copy()
    out["quality_code_macro_class_set"] = macro_sets
    out["quality_code_macro_class_cn_set"] = macro_cn_sets
    out["quality_code_model_role_set"] = role_sets
    out["quality_code_model_role_cn_set"] = role_cn_sets
    out["quality_codes_core_quality"] = core_code_sets
    out["quality_codes_process_precursor"] = precursor_code_sets
    out["quality_codes_auxiliary_state"] = state_code_sets
    out["quality_core_code_label"] = core_labels
    out["quality_process_precursor_label"] = precursor_labels
    out["quality_auxiliary_state_label"] = state_labels

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    class_path = OUT_DIR / "quality_code_classification.csv"
    label_path = OUT_DIR / "quality_label_analyzable_codes_classified.csv"
    summary_path = OUT_DIR / "dataset_summary.json"
    class_df.to_csv(class_path, index=False, encoding="utf-8-sig")
    out.to_csv(label_path, index=False, encoding="utf-8-sig")

    summary = {
        "source_curation_dir": str(CURATION_DIR),
        "n_rows": int(len(out)),
        "n_codes": int(len(class_df)),
        "n_analyzable_codes": int(class_df["is_analyzable"].sum()),
        "code_macro_class_counts": class_df[class_df["is_analyzable"] == 1]["macro_class"].value_counts().to_dict(),
        "code_model_role_counts": class_df[class_df["is_analyzable"] == 1]["model_role"].value_counts().to_dict(),
        "row_core_quality_positive": int(sum(core_labels)),
        "row_process_precursor_positive": int(sum(precursor_labels)),
        "row_auxiliary_state_positive": int(sum(state_labels)),
        "row_role_set_counts": out["quality_code_model_role_set"].value_counts().to_dict(),
        "outputs": {
            "quality_code_classification": str(class_path),
            "quality_label_analyzable_codes_classified": str(label_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"output_dir={OUT_DIR}")
    print(f"code_classification={class_path}")
    print(f"classified_labels={label_path}")
    print(f"summary={summary_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
