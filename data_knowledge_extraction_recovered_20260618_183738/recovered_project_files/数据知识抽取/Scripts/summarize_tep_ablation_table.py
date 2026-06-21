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


def _parse_variant(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError("Variant must use Label=path format")
    label, path = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError("Variant label cannot be empty")
    return label, Path(path.strip())


def summarize(variants: list[tuple[str, Path]]) -> str:
    rows: list[dict[str, Any]] = []
    full_target: float | None = None
    for label, path in variants:
        data = _load(path)
        row = _first_full_row(data)
        metric_texts: dict[str, str] = {}
        metric_values: dict[str, float] = {}
        for metric, _title in METRICS:
            text, value = _metric_text(row, metric)
            metric_texts[metric] = text
            metric_values[metric] = value
        if full_target is None:
            full_target = metric_values["target_defect_macro_f1"]
        rows.append(
            {
                "variant": label,
                "path": path.name,
                "target": metric_texts["target_defect_macro_f1"],
                "macro": metric_texts["macro_f1"],
                "event": metric_texts["event_macro_recall"],
                "path_hit": metric_texts["path_hit_rate"],
                "delta": metric_values["target_defect_macro_f1"] - float(full_target),
            }
        )

    lines: list[str] = []
    lines.append("# TEP Matched-Protocol Ablation Table")
    lines.append("")
    lines.append("| Variant | Target-F1 | Delta vs Full | Sample Macro-F1 | Event Macro-Recall | Path Hit |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            "| {variant} | {target} | {delta:+.4f} | {macro} | {event} | {path_hit} |".format(
                **row
            )
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "All rows use the matched TEP 20k/raw/t160/d16/l1 strict protocol. The ablation isolates "
        "which mechanism-evidence modules contribute under the same split, feature interface, and tree capacity."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize matched-protocol TEP ablations.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--variant", action="append", required=True, help="Use Label=path. First variant is Full.")
    args = parser.parse_args()
    report = summarize([_parse_variant(item) for item in args.variant])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
