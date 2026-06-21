from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METRICS = [
    ("target_defect_macro_f1", "Target-F1"),
    ("macro_f1", "Sample Macro-F1"),
    ("event_macro_recall", "Event Macro-Recall"),
    ("path_hit_rate", "Path Hit"),
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _first_full_row(data: dict[str, Any]) -> dict[str, Any]:
    for row in data.get("summary_table", []) or []:
        if str(row.get("experiment_name", "")) == "full_model":
            return dict(row)
    raise ValueError("summary_table must contain a full_model row")


def _metric_text(row: dict[str, Any], metric: str) -> tuple[str, float]:
    mean_key = f"{metric}_mean"
    std_key = f"{metric}_std"
    if mean_key not in row:
        raise ValueError(f"Missing metric: {mean_key}")
    mean = float(row[mean_key])
    std = float(row.get(std_key, 0.0) or 0.0)
    return f"{mean:.4f} +/- {std:.4f}", mean


def _parse_labeled_path(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError("Input must use Label=path format")
    label, path = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError("Label cannot be empty")
    return label, Path(path.strip())


def _summarize_row(label: str, path: Path, reference_target: float) -> dict[str, Any]:
    data = _load(path)
    full_row = _first_full_row(data)
    metric_texts: dict[str, str] = {}
    metric_values: dict[str, float] = {}
    for metric, _title in METRICS:
        text, value = _metric_text(full_row, metric)
        metric_texts[metric] = text
        metric_values[metric] = value
    return {
        "variant": label,
        "path": path.name,
        "target": metric_texts["target_defect_macro_f1"],
        "macro": metric_texts["macro_f1"],
        "event": metric_texts["event_macro_recall"],
        "path_hit": metric_texts["path_hit_rate"],
        "delta": metric_values["target_defect_macro_f1"] - reference_target,
    }


def summarize(reference: tuple[str, Path], variants: list[tuple[str, Path]]) -> str:
    reference_label, reference_path = reference
    reference_data = _load(reference_path)
    reference_row = _first_full_row(reference_data)
    reference_target_text, reference_target = _metric_text(reference_row, "target_defect_macro_f1")

    rows = [_summarize_row(label, path, reference_target) for label, path in variants]

    lines: list[str] = []
    lines.append("# TEP Tree-Free Risk-Head Baseline Summary")
    lines.append("")
    lines.append("## Reference")
    lines.append("")
    lines.append(
        f"- {reference_label}: Target-F1 {reference_target_text}; file `{reference_path.name}`."
    )
    lines.append("")
    lines.append("## Tree-Free Baselines")
    lines.append("")
    lines.append("| Variant | Target-F1 | Delta vs Reference | Sample Macro-F1 | Event Macro-Recall | Path Hit | Source File |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for row in rows:
        lines.append(
            "| {variant} | {target} | {delta:+.4f} | {macro} | {event} | {path_hit} | `{path}` |".format(
                **row
            )
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The current tree-free result is a baseline, not yet a replacement for the strict TEP mechanism model. "
        "A direct TCN risk head without expert/LLM prior performs far below the reliability-calibrated mechanism "
        "variant, so the next research step should focus on coupling temporal encoders with validated mechanism "
        "evidence instead of simply swapping out the tree anchor."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize TEP tree-free risk-head baselines.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--reference", required=True, help="Use Label=path")
    parser.add_argument("--variant", action="append", required=True, help="Use Label=path")
    args = parser.parse_args()

    report = summarize(
        reference=_parse_labeled_path(args.reference),
        variants=[_parse_labeled_path(item) for item in args.variant],
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
