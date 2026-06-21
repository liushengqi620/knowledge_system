from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v5_event_bag"
DEFAULT_OUTPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v6_hierarchical"


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


def add_hierarchical_labels(y: pd.DataFrame, *, normal_class_id: int = 0) -> pd.DataFrame:
    if "event_quality_class_id" not in y.columns:
        raise ValueError("y must contain event_quality_class_id.")
    out = y.copy()
    class_id = pd.to_numeric(out["event_quality_class_id"], errors="coerce").fillna(normal_class_id).astype(int)
    risk_label = (class_id != int(normal_class_id)).astype(int)
    out["risk_label"] = risk_label
    out["subtype_label"] = np.where(risk_label == 1, class_id, np.nan)
    out["subtype_label_source"] = np.where(risk_label == 1, "target_quality_subtype", "not_applicable")
    out["hierarchical_sample_role"] = np.where(risk_label == 1, "risk_positive_subtype", "risk_negative")
    return out


def build_kiepgl_hierarchical_dataset_v6(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    x_path = input_dir / "X_event_precursor_windows.csv"
    y_path = input_dir / "y_event_bag_label.csv"
    if not x_path.exists() or not y_path.exists():
        raise FileNotFoundError("v5 input must contain X_event_precursor_windows.csv and y_event_bag_label.csv.")

    x = pd.read_csv(x_path, low_memory=False)
    y = pd.read_csv(y_path, low_memory=False)
    y_h = add_hierarchical_labels(y)
    xy = y_h.merge(x, on=["sample_id", "event_bag_id", "precursor_stage"], how="left", validate="one_to_one")

    output_dir.mkdir(parents=True, exist_ok=True)
    x.to_csv(output_dir / "X_event_precursor_windows.csv", index=False, encoding="utf-8-sig")
    y_h.to_csv(output_dir / "y_hierarchical_event_label.csv", index=False, encoding="utf-8-sig")
    xy.to_csv(output_dir / "xy_hierarchical_event_windows.csv", index=False, encoding="utf-8-sig")

    for name in ("class_name_mapping.json", "feature_manifest.json", "feature_groups.json", "label_mapping.json"):
        src = input_dir / name
        if src.exists():
            (output_dir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    role_counts = y_h["hierarchical_sample_role"].value_counts().to_dict()
    class_counts = y_h["event_quality_class"].value_counts().to_dict() if "event_quality_class" in y_h.columns else {}
    summary = {
        "dataset_version": "v6_kiepgl_hierarchical_event_bag",
        "task": "hierarchical_event_risk_and_defect_subtype_warning",
        "source_dir": str(input_dir),
        "n_samples": int(len(y_h)),
        "n_x_features": int(max(len(x.columns) - 3, 0)) if not x.empty else 0,
        "risk_positive_count": int(y_h["risk_label"].sum()),
        "risk_negative_count": int((y_h["risk_label"] == 0).sum()),
        "subtype_training_count": int(y_h["subtype_label"].notna().sum()),
        "role_distribution": {str(k): int(v) for k, v in role_counts.items()},
        "class_distribution": {str(k): int(v) for k, v in class_counts.items()},
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
                "# KIEP-GL v6 Hierarchical Event Dataset",
                "",
                "This dataset separates binary event-risk warning from abnormal-only defect subtype attribution.",
                "",
                "Primary files:",
                "- `X_event_precursor_windows.csv`: event precursor window features inherited from v5.",
                "- `y_hierarchical_event_label.csv`: risk and subtype labels.",
                "- `xy_hierarchical_event_windows.csv`: joined modeling table.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build KIEP-GL v6 hierarchical event dataset.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    summary = build_kiepgl_hierarchical_dataset_v6(Path(args.input_dir), Path(args.output_dir))
    print(json.dumps(_json_sanitize(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
