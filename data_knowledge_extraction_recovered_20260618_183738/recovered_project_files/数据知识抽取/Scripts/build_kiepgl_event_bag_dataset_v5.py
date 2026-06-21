from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

try:
    from config import CONFIG
except ModuleNotFoundError:
    CONFIG = {}


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v4_multiclass"
DEFAULT_OUTPUT_DIR = ROOT / "knowledge_exports" / "quality_traceability_dataset_v5_event_bag"

DEFAULT_STAGES = [
    {"name": "late", "min_lag": 1, "max_lag": 3},
    {"name": "mid", "min_lag": 4, "max_lag": 8},
    {"name": "early", "min_lag": 9, "max_lag": 12},
]


def _normal_class_id() -> int:
    return 0


def _safe_text(value: Any) -> str:
    if pd.isna(value):
        return "missing"
    text = str(value).strip()
    return text if text else "missing"


def _event_group_key(row: Mapping[str, Any]) -> str:
    for col in ("process_sequence_key", "连铸处理号", "材料跟踪号"):
        value = row.get(col)
        if value is not None and not pd.isna(value) and str(value).strip():
            return f"{col}:{_safe_text(value)}"
    return "global"


def _numeric_feature_cols(x: pd.DataFrame) -> list[str]:
    return [
        str(col)
        for col in x.columns
        if str(col) != "record_id" and pd.api.types.is_numeric_dtype(x[col])
    ]


def _event_onsets(y: pd.DataFrame) -> list[dict[str, Any]]:
    labels = pd.to_numeric(y["event_quality_class_id"], errors="coerce").fillna(0).astype(int).to_numpy()
    onsets: list[dict[str, Any]] = []
    prev_class = _normal_class_id()
    prev_group = ""
    for idx, class_id in enumerate(labels):
        row = y.iloc[idx]
        group_key = _event_group_key(row)
        is_onset = (
            int(class_id) != _normal_class_id()
            and (int(prev_class) == _normal_class_id() or int(prev_class) != int(class_id) or group_key != prev_group)
        )
        if is_onset:
            record_id = row.get("record_id", idx)
            event_class = str(row.get("event_quality_class", f"class_{int(class_id)}"))
            onsets.append(
                {
                    "event_onset_index": int(idx),
                    "event_anchor_record_id": int(record_id) if not pd.isna(record_id) else int(idx),
                    "event_anchor_time": _safe_text(row.get("process_time", "")),
                    "event_quality_class_id": int(class_id),
                    "event_quality_class": event_class,
                    "event_bag_id": f"event_{int(record_id) if not pd.isna(record_id) else idx}_{event_class}",
                    "event_group_key": group_key,
                }
            )
        prev_class = int(class_id)
        prev_group = group_key
    return onsets


def _negative_anchors(
    y: pd.DataFrame,
    *,
    max_lag: int,
    stride: int,
) -> list[dict[str, Any]]:
    if stride <= 0:
        return []
    labels = pd.to_numeric(y["event_quality_class_id"], errors="coerce").fillna(0).astype(int).to_numpy()
    anchors: list[dict[str, Any]] = []
    for idx in range(max_lag, len(labels), stride):
        if int(labels[idx]) != _normal_class_id():
            continue
        row = y.iloc[idx]
        record_id = row.get("record_id", idx)
        anchors.append(
            {
                "event_onset_index": int(idx),
                "event_anchor_record_id": int(record_id) if not pd.isna(record_id) else int(idx),
                "event_anchor_time": _safe_text(row.get("process_time", "")),
                "event_quality_class_id": 0,
                "event_quality_class": "no_quality_abnormal",
                "event_bag_id": f"normal_{int(record_id) if not pd.isna(record_id) else idx}",
                "event_group_key": _event_group_key(row),
            }
        )
    return anchors


def _window_stats(frame: pd.DataFrame, feature_cols: Sequence[str]) -> dict[str, float]:
    row: dict[str, float] = {}
    for col in feature_cols:
        values = pd.to_numeric(frame[col], errors="coerce").to_numpy(dtype=np.float64)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            mean = std = last = trend = 0.0
        else:
            mean = float(np.mean(finite))
            std = float(np.std(finite))
            last = float(finite[-1])
            trend = float(finite[-1] - finite[0]) if finite.size > 1 else 0.0
        row[f"{col}_mean"] = mean
        row[f"{col}_std"] = std
        row[f"{col}_last"] = last
        row[f"{col}_trend"] = trend
    return row


def _stage_defs(stages: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    raw = list(stages or CONFIG.get("event_precursor_levels") or DEFAULT_STAGES)
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name", "stage"))
        lo = max(1, int(item.get("min_lag", 1)))
        hi = max(lo, int(item.get("max_lag", lo)))
        out.append({"name": name, "min_lag": lo, "max_lag": hi})
    return out or list(DEFAULT_STAGES)


def build_event_bag_windows(
    x: pd.DataFrame,
    y: pd.DataFrame,
    *,
    stages: Sequence[Mapping[str, Any]] | None = None,
    negative_stride: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if "event_quality_class_id" not in y.columns:
        raise ValueError("y must contain event_quality_class_id.")
    if len(x) != len(y):
        raise ValueError("X and y must have the same row count.")
    x_work = x.reset_index(drop=True).copy()
    y_work = y.reset_index(drop=True).copy()
    feature_cols = _numeric_feature_cols(x_work)
    stage_defs = _stage_defs(stages)
    max_lag = max(int(s["max_lag"]) for s in stage_defs)
    anchors = _event_onsets(y_work)
    anchors.extend(_negative_anchors(y_work, max_lag=max_lag, stride=int(negative_stride)))
    anchors.sort(key=lambda row: (int(row["event_onset_index"]), str(row["event_bag_id"])))

    x_rows: list[dict[str, Any]] = []
    y_rows: list[dict[str, Any]] = []
    for anchor in anchors:
        onset = int(anchor["event_onset_index"])
        for stage in stage_defs:
            lo = int(stage["min_lag"])
            hi = int(stage["max_lag"])
            start = onset - hi
            end = onset - lo
            if start < 0 or end < start:
                continue
            window = x_work.iloc[start : end + 1]
            sample_id = f"{anchor['event_bag_id']}__{stage['name']}"
            x_row = {
                "sample_id": sample_id,
                "event_bag_id": anchor["event_bag_id"],
                "precursor_stage": stage["name"],
                **_window_stats(window, feature_cols),
            }
            y_row = {
                "sample_id": sample_id,
                "event_bag_id": anchor["event_bag_id"],
                "event_anchor_record_id": int(anchor["event_anchor_record_id"]),
                "event_anchor_time": anchor["event_anchor_time"],
                "event_onset_index": int(onset),
                "event_group_key": anchor["event_group_key"],
                "event_quality_class_id": int(anchor["event_quality_class_id"]),
                "event_quality_class": str(anchor["event_quality_class"]),
                "event_is_abnormal": int(int(anchor["event_quality_class_id"]) != _normal_class_id()),
                "precursor_stage": stage["name"],
                "lead_horizon_min": int(lo),
                "lead_horizon_max": int(hi),
                "window_start_index": int(start),
                "window_end_index": int(end),
                "window_size": int(end - start + 1),
            }
            x_rows.append(x_row)
            y_rows.append(y_row)
    x_out = pd.DataFrame(x_rows)
    y_out = pd.DataFrame(y_rows)
    summary = {
        "dataset_version": "v5_kiepgl_event_bag_precursor_windows",
        "task": "event_bag_multiclass_precursor_warning",
        "n_samples": int(len(y_out)),
        "n_x_features": int(max(len(x_out.columns) - 3, 0)) if not x_out.empty else 0,
        "positive_event_count": int(sum(1 for a in anchors if int(a["event_quality_class_id"]) != 0)),
        "negative_anchor_count": int(sum(1 for a in anchors if int(a["event_quality_class_id"]) == 0)),
        "stage_distribution": {str(k): int(v) for k, v in y_out.get("precursor_stage", pd.Series(dtype=object)).value_counts().to_dict().items()},
        "class_distribution": {str(k): int(v) for k, v in y_out.get("event_quality_class", pd.Series(dtype=object)).value_counts().to_dict().items()},
        "feature_source_count": int(len(feature_cols)),
        "stages": stage_defs,
    }
    return x_out, y_out, summary


def build_kiepgl_event_bag_dataset_v5(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    negative_stride: int = 12,
    max_rows: int | None = None,
) -> dict[str, Any]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    read_kwargs: dict[str, Any] = {"low_memory": False}
    if max_rows is not None and int(max_rows) > 0:
        read_kwargs["nrows"] = int(max_rows)
    x = pd.read_csv(input_dir / "X_process_features.csv", **read_kwargs)
    y = pd.read_csv(input_dir / "y_quality_label.csv", **read_kwargs)
    x_win, y_win, summary = build_event_bag_windows(x, y, negative_stride=int(negative_stride))
    xy_win = y_win.merge(x_win, on=["sample_id", "event_bag_id", "precursor_stage"], how="left", validate="one_to_one")

    output_dir.mkdir(parents=True, exist_ok=True)
    x_win.to_csv(output_dir / "X_event_precursor_windows.csv", index=False, encoding="utf-8-sig")
    y_win.to_csv(output_dir / "y_event_bag_label.csv", index=False, encoding="utf-8-sig")
    xy_win.to_csv(output_dir / "xy_event_bag_windows.csv", index=False, encoding="utf-8-sig")
    for name in ("class_name_mapping.json", "feature_manifest.json", "feature_groups.json", "label_mapping.json"):
        src = input_dir / name
        if src.exists():
            (output_dir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    summary = {
        **summary,
        "source_dir": str(input_dir),
        "source_row_limit": int(max_rows) if max_rows is not None and int(max_rows) > 0 else None,
        "outputs": {
            "X_event_precursor_windows": str(output_dir / "X_event_precursor_windows.csv"),
            "y_event_bag_label": str(output_dir / "y_event_bag_label.csv"),
            "xy_event_bag_windows": str(output_dir / "xy_event_bag_windows.csv"),
        },
    }
    (output_dir / "dataset_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "# KIEP-GL v5 Event-Bag Precursor Dataset",
                "",
                "This dataset converts row-level v4 labels into event-bag precursor-window samples.",
                "",
                "Primary files:",
                "- `X_event_precursor_windows.csv`: window-level process features.",
                "- `y_event_bag_label.csv`: event bag, stage and multiclass labels.",
                "- `xy_event_bag_windows.csv`: joined modeling table.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build KIEP-GL v5 event-bag precursor-window dataset.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--negative-stride", type=int, default=12)
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()
    summary = build_kiepgl_event_bag_dataset_v5(
        Path(args.input_dir),
        Path(args.output_dir),
        negative_stride=int(args.negative_stride),
        max_rows=args.max_rows,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
