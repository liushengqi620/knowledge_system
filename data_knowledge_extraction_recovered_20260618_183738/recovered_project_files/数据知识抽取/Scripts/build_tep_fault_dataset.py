from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "数据集" / "流程工业田纳西化工过程故障诊断与分析数据集"
DEFAULT_OUTPUT_DIR = ROOT / "knowledge_exports" / "tep_fault_diagnosis_dataset"

N_TEP_FEATURES = 52
TEST_FAULT_ONSET = 160

FAULT_DESCRIPTIONS = {
    0: "fault_free",
    1: "A/C_feed_ratio_B_composition_constant_stream_4",
    2: "B_composition_A/C_ratio_constant_stream_4",
    3: "D_feed_temperature_stream_2",
    4: "reactor_cooling_water_inlet_temperature",
    5: "condenser_cooling_water_inlet_temperature",
    6: "A_feed_loss_stream_1",
    7: "C_header_pressure_loss_stream_4",
    8: "A_B_C_feed_composition_stream_4",
    9: "D_feed_temperature_stream_2_random_variation",
    10: "C_feed_temperature_stream_4",
    11: "reactor_cooling_water_inlet_temperature_random_variation",
    12: "condenser_cooling_water_inlet_temperature_random_variation",
    13: "reaction_kinetics",
    14: "reactor_cooling_water_valve",
    15: "condenser_cooling_water_valve",
    16: "unknown_fault_16",
    17: "unknown_fault_17",
    18: "unknown_fault_18",
    19: "unknown_fault_19",
    20: "unknown_fault_20",
    21: "stream_4_valve_fixed",
}


def tep_feature_columns() -> list[str]:
    return [f"xmeas_{i:02d}" for i in range(1, 42)] + [f"xmv_{i:02d}" for i in range(1, 12)]


def _read_tep_dat(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, sep=r"\s+", header=None)
    if raw.shape[0] == N_TEP_FEATURES and raw.shape[1] != N_TEP_FEATURES:
        raw = raw.T
    if raw.shape[1] != N_TEP_FEATURES:
        raise ValueError(f"{path} must contain {N_TEP_FEATURES} variables, got shape {raw.shape}")
    raw = raw.reset_index(drop=True)
    raw.columns = tep_feature_columns()
    return raw.apply(pd.to_numeric, errors="coerce")


def _fault_id_from_name(path: Path) -> int:
    match = re.match(r"d(\d{2})(?:_te)?\.dat$", path.name, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Unexpected TEP file name: {path.name}")
    return int(match.group(1))


def _rows_for_file(path: Path, *, split_role: str, test_fault_onset: int) -> pd.DataFrame:
    fault_id = _fault_id_from_name(path)
    x = _read_tep_dat(path)
    n_rows = len(x)
    sample_index = np.arange(n_rows, dtype=np.int64)
    labels = np.full(n_rows, fault_id, dtype=np.int64)
    if fault_id == 0:
        labels[:] = 0
    elif split_role == "test":
        onset = max(0, min(int(test_fault_onset), n_rows))
        labels[:onset] = 0

    out = x.copy()
    out.insert(0, "sample_index", sample_index)
    out.insert(0, "source_file", path.name)
    out.insert(0, "source_split", split_role)
    out.insert(0, "fault_id", fault_id)
    out.insert(0, "record_id", [f"tep_{split_role}_{path.stem}_{i:04d}" for i in range(n_rows)])
    out["event_quality_class_id"] = labels
    out["event_quality_class"] = [FAULT_DESCRIPTIONS.get(int(label), f"fault_{int(label):02d}") for label in labels]
    out["event_is_abnormal"] = (labels != 0).astype("int8")
    out["split_role"] = split_role
    out["event_bag_id"] = [
        f"{split_role}_{path.stem}_normal_pre_fault" if int(label) == 0 else f"{split_role}_{path.stem}_fault_{fault_id:02d}"
        for label in labels
    ]
    horizons = np.full(n_rows, -1.0, dtype=float)
    if fault_id != 0:
        fault_positions = np.flatnonzero(labels == fault_id)
        if fault_positions.size:
            horizons[fault_positions] = np.arange(fault_positions.size, 0, -1, dtype=float)
    out["lead_horizon_min"] = horizons
    return out


def _dat_files(directory: Path, pattern: str) -> list[Path]:
    files = sorted(directory.glob(pattern), key=lambda p: _fault_id_from_name(p))
    if not files:
        raise FileNotFoundError(f"No files matching {pattern!r} in {directory}")
    return files


def _class_mapping(max_fault_id: int) -> dict[str, Any]:
    return {
        "task": "tep_multiclass_fault_diagnosis",
        "primary_label_column": "event_quality_class_id",
        "primary_label_name_column": "event_quality_class",
        "classes": [
            {
                "class_id": int(class_id),
                "class_name": FAULT_DESCRIPTIONS.get(class_id, f"fault_{class_id:02d}"),
                "is_abnormal": bool(class_id != 0),
                "description": FAULT_DESCRIPTIONS.get(class_id, f"TEP fault {class_id:02d}"),
            }
            for class_id in range(0, int(max_fault_id) + 1)
        ],
    }


def build_tep_fault_dataset(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    train_dir_name: str = "训练集",
    test_dir_name: str = "测试集",
    test_fault_onset: int = TEST_FAULT_ONSET,
) -> dict[str, Any]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    train_dir = input_dir / train_dir_name
    test_dir = input_dir / test_dir_name

    train_frames = [_rows_for_file(path, split_role="train", test_fault_onset=test_fault_onset) for path in _dat_files(train_dir, "d*.dat")]
    test_frames = [_rows_for_file(path, split_role="test", test_fault_onset=test_fault_onset) for path in _dat_files(test_dir, "d*_te.dat")]
    all_rows = pd.concat([*train_frames, *test_frames], ignore_index=True)
    all_rows = all_rows.sort_values(["source_split", "sample_index", "fault_id"], kind="stable").reset_index(drop=True)

    feature_cols = tep_feature_columns()
    x_cols = ["record_id", *feature_cols]
    y_cols = [
        "record_id",
        "event_quality_class",
        "event_quality_class_id",
        "event_is_abnormal",
        "split_role",
        "source_split",
        "source_file",
        "fault_id",
        "sample_index",
        "event_bag_id",
        "lead_horizon_min",
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    x = all_rows[x_cols].copy()
    y = all_rows[y_cols].copy()
    xy = y.merge(x, on="record_id", how="left", validate="one_to_one")

    x.to_csv(output_dir / "X_process_features.csv", index=False, encoding="utf-8-sig")
    y.to_csv(output_dir / "y_quality_label.csv", index=False, encoding="utf-8-sig")
    xy.to_csv(output_dir / "xy_quality_traceability.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame().to_csv(output_dir / "auxiliary_quality_events.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame().to_csv(output_dir / "invalid_data_quality_rows.csv", index=False, encoding="utf-8-sig")

    max_fault_id = int(max(all_rows["fault_id"].max(), all_rows["event_quality_class_id"].max()))
    mapping = _class_mapping(max_fault_id)
    (output_dir / "class_name_mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "feature_groups.json").write_text(
        json.dumps(
            {
                "measured_variables": [f"xmeas_{i:02d}" for i in range(1, 42)],
                "manipulated_variables": [f"xmv_{i:02d}" for i in range(1, 12)],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    class_counts = y["event_quality_class_id"].value_counts().sort_index()
    split_counts = y["split_role"].value_counts().sort_index()
    summary = {
        "source_dir": str(input_dir),
        "dataset_version": "tep_standard_dat_adapter",
        "task": "tep_multiclass_fault_diagnosis",
        "primary_label_column": "event_quality_class_id",
        "primary_label_name_column": "event_quality_class",
        "test_fault_onset": int(test_fault_onset),
        "n_rows": int(len(y)),
        "n_x_features": int(len(feature_cols)),
        "n_classes": int(len(mapping["classes"])),
        "class_distribution": {str(int(k)): int(v) for k, v in class_counts.items()},
        "split_distribution": {str(k): int(v) for k, v in split_counts.items()},
        "outputs": {
            "X_process_features": str(output_dir / "X_process_features.csv"),
            "y_quality_label": str(output_dir / "y_quality_label.csv"),
            "xy_quality_traceability": str(output_dir / "xy_quality_traceability.csv"),
            "class_name_mapping": str(output_dir / "class_name_mapping.json"),
        },
    }
    (output_dir / "dataset_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "# TEP Fault Diagnosis Dataset",
                "",
                "Adapted from standard Tennessee Eastman `.dat` files.",
                "",
                "- Normal class: `event_quality_class_id = 0`.",
                "- Fault classes: `event_quality_class_id = 1..21`.",
                f"- Testing fault files are labeled normal before sample {int(test_fault_onset)} and faulty afterward.",
                "- `split_role` preserves the official train/test source split; validation is held out from training rows by the experiment runner.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an experiment-ready TEP fault diagnosis dataset.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--train-dir-name", default="训练集")
    parser.add_argument("--test-dir-name", default="测试集")
    parser.add_argument("--test-fault-onset", type=int, default=TEST_FAULT_ONSET)
    args = parser.parse_args()
    summary = build_tep_fault_dataset(
        Path(args.input_dir),
        Path(args.output_dir),
        train_dir_name=args.train_dir_name,
        test_dir_name=args.test_dir_name,
        test_fault_onset=args.test_fault_onset,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
