from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v6_hierarchical"
DEFAULT_OUTPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v7_label_scheme"

NORMAL_CLASS = "no_quality_abnormal"

RISK_BINARY_CLASSES = {
    0: NORMAL_CLASS,
    1: "boundary_instability_risk",
}

COARSE_MECHANISM_BY_FINE_CLASS = {
    NORMAL_CLASS: (0, NORMAL_CLASS),
    "temperature_flux": (1, "thermal_boundary_instability"),
    "heat_transfer_imbalance": (1, "thermal_boundary_instability"),
    "mold_level_slag_risk": (2, "flow_control_boundary_instability"),
    "speed_stopper_flow": (2, "flow_control_boundary_instability"),
    "process_fluctuation": (3, "process_fluctuation"),
}

COARSE_MECHANISM_CLASSES = {
    0: NORMAL_CLASS,
    1: "thermal_boundary_instability",
    2: "flow_control_boundary_instability",
    3: "process_fluctuation",
}


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _json_sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_sanitize(v) for v in value]
    return value


def _class_mapping(classes: Mapping[int, str], *, scheme: str) -> dict[str, Any]:
    return {
        "task": f"{scheme}_event_level_quality_warning",
        "label_scheme": str(scheme),
        "primary_label_column": "event_quality_class_id",
        "primary_label_name_column": "event_quality_class",
        "original_label_column": "original_event_quality_class_id",
        "classes": [
            {
                "class_id": int(class_id),
                "class_name": str(class_name),
                "is_abnormal": int(class_id) != 0,
                "description": f"{scheme} label: {class_name}",
            }
            for class_id, class_name in sorted(classes.items())
        ],
    }


def _source_class_name(row: Mapping[str, Any]) -> str:
    raw = row.get("event_quality_class")
    if raw is not None and not pd.isna(raw) and str(raw).strip():
        return str(raw).strip()
    class_id = int(pd.to_numeric(pd.Series([row.get("event_quality_class_id")]), errors="coerce").fillna(0).iloc[0])
    fallback = {
        0: NORMAL_CLASS,
        1: "temperature_flux",
        2: "mold_level_slag_risk",
        3: "process_fluctuation",
        4: "speed_stopper_flow",
        5: "heat_transfer_imbalance",
    }
    return fallback.get(class_id, f"class_{class_id}")


def _apply_risk_binary(row: Mapping[str, Any]) -> tuple[int, str]:
    class_name = _source_class_name(row)
    if class_name == NORMAL_CLASS:
        return 0, NORMAL_CLASS
    return 1, RISK_BINARY_CLASSES[1]


def _apply_coarse_mechanism(row: Mapping[str, Any]) -> tuple[int, str]:
    class_name = _source_class_name(row)
    return COARSE_MECHANISM_BY_FINE_CLASS.get(class_name, (3, "process_fluctuation"))


def apply_label_scheme(y: pd.DataFrame, *, scheme: str) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    if "event_quality_class_id" not in y.columns:
        raise ValueError("y must contain event_quality_class_id.")
    mode = str(scheme or "").strip().lower()
    if mode not in {"risk_binary", "coarse_mechanism"}:
        raise ValueError("scheme must be one of: risk_binary, coarse_mechanism")

    out = y.copy()
    if "original_event_quality_class_id" not in out.columns:
        out["original_event_quality_class_id"] = pd.to_numeric(
            out["event_quality_class_id"],
            errors="coerce",
        ).fillna(0).astype(int)
    if "original_event_quality_class" not in out.columns:
        out["original_event_quality_class"] = [
            _source_class_name(row) for _, row in out.iterrows()
        ]

    mapper = _apply_risk_binary if mode == "risk_binary" else _apply_coarse_mechanism
    mapped = [mapper(row) for _, row in out.iterrows()]
    out["event_quality_class_id"] = [int(item[0]) for item in mapped]
    out["event_quality_class"] = [str(item[1]) for item in mapped]
    out["event_is_abnormal"] = (out["event_quality_class_id"].astype(int) != 0).astype("int8")
    out["risk_label"] = out["event_is_abnormal"].astype("int8")
    out["label_scheme"] = mode

    if "subtype_label" in out.columns:
        subtype = pd.to_numeric(out["event_quality_class_id"], errors="coerce").fillna(0).astype(int)
        out["subtype_label"] = np.where(subtype != 0, subtype, np.nan)
    if "subtype_supervision_mask" in out.columns:
        # Binary risk is intended for flat binary training; coarse mechanism can still use subtype supervision.
        mask = (out["event_quality_class_id"].astype(int) != 0) & (mode == "coarse_mechanism")
        out["subtype_supervision_mask"] = mask.astype("int8")
    if "hierarchical_sample_role" in out.columns:
        out["hierarchical_sample_role"] = np.where(
            out["event_quality_class_id"].astype(int) == 0,
            "risk_negative",
            "risk_positive_subtype" if mode == "coarse_mechanism" else "risk_positive_binary",
        )

    classes = RISK_BINARY_CLASSES if mode == "risk_binary" else COARSE_MECHANISM_CLASSES
    mapping = _class_mapping(classes, scheme=mode)
    summary = {
        "dataset_version": "v7_kiepgl_label_scheme",
        "label_scheme": mode,
        "n_samples": int(len(out)),
        "class_distribution": {
            str(k): int(v) for k, v in out["event_quality_class"].value_counts().to_dict().items()
        },
        "source_class_distribution": {
            str(k): int(v) for k, v in out["original_event_quality_class"].value_counts().to_dict().items()
        },
        "classes": mapping["classes"],
    }
    return out, mapping, summary


def build_kiepgl_label_scheme_dataset_v7(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    scheme: str = "risk_binary",
) -> dict[str, Any]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    x_path = input_dir / "X_event_precursor_windows.csv"
    y_path = input_dir / "y_hierarchical_event_label.csv"
    if not x_path.exists() or not y_path.exists():
        raise FileNotFoundError("input must contain X_event_precursor_windows.csv and y_hierarchical_event_label.csv")

    x = pd.read_csv(x_path, low_memory=False)
    y = pd.read_csv(y_path, low_memory=False)
    y_out, mapping, summary = apply_label_scheme(y, scheme=scheme)
    xy = y_out.merge(x, on=["sample_id", "event_bag_id", "precursor_stage"], how="left", validate="one_to_one")

    output_dir.mkdir(parents=True, exist_ok=True)
    x.to_csv(output_dir / "X_event_precursor_windows.csv", index=False, encoding="utf-8-sig")
    y_out.to_csv(output_dir / "y_hierarchical_event_label.csv", index=False, encoding="utf-8-sig")
    xy.to_csv(output_dir / "xy_hierarchical_event_windows.csv", index=False, encoding="utf-8-sig")
    (output_dir / "class_name_mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    for name in ("feature_manifest.json", "feature_groups.json", "label_mapping.json"):
        src = input_dir / name
        if src.exists():
            shutil.copyfile(src, output_dir / name)

    summary = {
        **summary,
        "source_dir": str(input_dir),
        "outputs": {
            "X_event_precursor_windows": str(output_dir / "X_event_precursor_windows.csv"),
            "y_hierarchical_event_label": str(output_dir / "y_hierarchical_event_label.csv"),
            "xy_hierarchical_event_windows": str(output_dir / "xy_hierarchical_event_windows.csv"),
        },
    }
    (output_dir / "dataset_summary.json").write_text(json.dumps(_json_sanitize(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "# KIEP-GL v7 Label-Scheme Dataset",
                "",
                f"Label scheme: `{scheme}`.",
                "",
                "The dataset preserves original fine-grained subtype columns while replacing the primary modeling label.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build KIEP-GL v7 relabelled event dataset.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--scheme", choices=["risk_binary", "coarse_mechanism"], default="risk_binary")
    args = parser.parse_args()
    summary = build_kiepgl_label_scheme_dataset_v7(
        Path(args.input_dir),
        Path(args.output_dir),
        scheme=str(args.scheme),
    )
    print(json.dumps(_json_sanitize(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
