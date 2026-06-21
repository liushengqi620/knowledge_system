from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v3"
DEFAULT_OUTPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v4_multiclass"

CLASS_NAME_TO_ID = {
    "no_quality_abnormal": 0,
    "temperature_flux": 1,
    "mold_level_slag_risk": 2,
    "process_fluctuation": 3,
    "speed_stopper_flow": 4,
    "heat_transfer_imbalance": 5,
    "transition_tundish": 6,
    "other_quality_abnormal": 7,
}

CLASS_ID_TO_NAME = {value: key for key, value in CLASS_NAME_TO_ID.items()}


def _normalize_class(value: Any) -> str:
    raw = "" if pd.isna(value) else str(value).strip()
    if raw in CLASS_NAME_TO_ID:
        return raw
    if not raw or raw.lower() in {"nan", "none", "null"}:
        return "no_quality_abnormal"
    return raw


def add_multiclass_event_labels(y: pd.DataFrame) -> pd.DataFrame:
    if "quality_abnormal_group" not in y.columns:
        raise ValueError("y_quality_label.csv must contain quality_abnormal_group.")
    out = y.copy()
    event_class = out["quality_abnormal_group"].map(_normalize_class)
    unknown = sorted(set(event_class) - set(CLASS_NAME_TO_ID))
    if unknown:
        raise ValueError(f"Unknown event quality classes: {unknown}")
    out["event_quality_class"] = event_class
    out["event_quality_class_id"] = out["event_quality_class"].map(CLASS_NAME_TO_ID).astype("int64")
    out["event_is_abnormal"] = (out["event_quality_class_id"] != 0).astype("int64")
    return out


def _class_mapping() -> dict[str, Any]:
    rows = []
    for name, class_id in CLASS_NAME_TO_ID.items():
        rows.append(
            {
                "class_id": int(class_id),
                "class_name": name,
                "is_abnormal": bool(class_id != 0),
                "description": (
                    "clean normal or no target quality abnormal code"
                    if class_id == 0
                    else f"target quality abnormal class: {name}"
                ),
            }
        )
    return {
        "task": "multiclass_event_level_quality_warning",
        "primary_label_column": "event_quality_class_id",
        "primary_label_name_column": "event_quality_class",
        "auxiliary_binary_label": "quality_label",
        "classes": rows,
    }


def build_kiepgl_multiclass_dataset_v4(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    x = pd.read_csv(input_dir / "X_process_features.csv", low_memory=False)
    y = pd.read_csv(input_dir / "y_quality_label.csv", low_memory=False)
    xy = pd.read_csv(input_dir / "xy_quality_traceability.csv", low_memory=False)
    aux = pd.read_csv(input_dir / "auxiliary_quality_events.csv", low_memory=False)
    invalid = pd.read_csv(input_dir / "invalid_data_quality_rows.csv", low_memory=False)

    y_multi = add_multiclass_event_labels(y)
    class_cols = ["record_id", "event_quality_class", "event_quality_class_id", "event_is_abnormal"]
    class_frame = y_multi[class_cols].copy()
    xy_base = xy.drop(
        columns=[c for c in ["event_quality_class", "event_quality_class_id", "event_is_abnormal"] if c in xy.columns],
        errors="ignore",
    )
    xy_multi = class_frame.merge(xy_base, on="record_id", how="left", validate="one_to_one")

    output_dir.mkdir(parents=True, exist_ok=True)
    x.to_csv(output_dir / "X_process_features.csv", index=False, encoding="utf-8-sig")
    y_multi.to_csv(output_dir / "y_quality_label.csv", index=False, encoding="utf-8-sig")
    xy_multi.to_csv(output_dir / "xy_quality_traceability.csv", index=False, encoding="utf-8-sig")
    aux.to_csv(output_dir / "auxiliary_quality_events.csv", index=False, encoding="utf-8-sig")
    invalid.to_csv(output_dir / "invalid_data_quality_rows.csv", index=False, encoding="utf-8-sig")
    mapping = _class_mapping()
    (output_dir / "class_name_mapping.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for name in ("feature_manifest.json", "feature_groups.json", "label_mapping.json"):
        src = input_dir / name
        if src.exists():
            (output_dir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    class_counts = y_multi["event_quality_class"].value_counts().reindex(CLASS_NAME_TO_ID.keys(), fill_value=0)
    class_distribution = {str(k): int(v) for k, v in class_counts.items()}
    summary = {
        "source_dir": str(input_dir),
        "dataset_version": "v4_kiepgl_multiclass_event_warning",
        "task": "multiclass_event_level_quality_warning",
        "primary_label_column": "event_quality_class_id",
        "primary_label_name_column": "event_quality_class",
        "auxiliary_binary_label": "quality_label",
        "n_rows": int(len(y_multi)),
        "n_x_features": int(len([c for c in x.columns if c != "record_id"])),
        "n_classes": int(len(CLASS_NAME_TO_ID)),
        "class_distribution": class_distribution,
        "outputs": {
            "X_process_features": str(output_dir / "X_process_features.csv"),
            "y_quality_label": str(output_dir / "y_quality_label.csv"),
            "xy_quality_traceability": str(output_dir / "xy_quality_traceability.csv"),
            "class_name_mapping": str(output_dir / "class_name_mapping.json"),
        },
    }
    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "# KIEP-GL v4 Multiclass Dataset",
                "",
                "This dataset upgrades v3 from binary quality abnormal warning to multiclass event-level quality warning.",
                "",
                "Primary multiclass labels:",
                "- `event_quality_class`",
                "- `event_quality_class_id`",
                "",
                "`quality_label` is retained only as an auxiliary binary abnormal indicator.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build KIEP-GL v4 multiclass event warning dataset.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    summary = build_kiepgl_multiclass_dataset_v4(Path(args.input_dir), Path(args.output_dir))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
