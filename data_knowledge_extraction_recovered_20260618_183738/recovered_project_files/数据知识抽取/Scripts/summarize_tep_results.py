from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} +/- {pstdev(values):.4f}"


def _summary_metric(data: dict[str, Any], metric: str) -> list[float]:
    rows = data.get("summary_table", [])
    values: list[float] = []
    for row in rows:
        if str(row.get("experiment_name", "")) != "full_model":
            continue
        value = row.get(metric)
        if value is not None:
            values.append(float(value))
    if values:
        return values
    out: list[float] = []
    for run in data.get("runs", []):
        sample = run.get("sample_multiclass_metrics", {})
        event = run.get("event_warning_metrics", {})
        path = run.get("path_explanation_metrics", {})
        if metric == "target_defect_macro_f1_mean" and "target_defect_macro_f1" in sample:
            out.append(float(sample["target_defect_macro_f1"]))
        elif metric == "macro_f1_mean" and "macro_f1" in sample:
            out.append(float(sample["macro_f1"]))
        elif metric == "event_macro_recall_mean" and "event_macro_recall" in event:
            out.append(float(event["event_macro_recall"]))
        elif metric == "path_hit_rate_mean" and "path_hit_rate" in path:
            out.append(float(path["path_hit_rate"]))
    return out


def summarize(proposed: list[Path], ablation: list[Path]) -> str:
    proposed_target: list[float] = []
    proposed_macro: list[float] = []
    proposed_event: list[float] = []
    proposed_path: list[float] = []
    for path in proposed:
        data = _load(path)
        proposed_target.extend(_summary_metric(data, "target_defect_macro_f1_mean"))
        proposed_macro.extend(_summary_metric(data, "macro_f1_mean"))
        proposed_event.extend(_summary_metric(data, "event_macro_recall_mean"))
        proposed_path.extend(_summary_metric(data, "path_hit_rate_mean"))

    ablation_target: list[float] = []
    for path in ablation:
        data = _load(path)
        ablation_target.extend(_summary_metric(data, "target_defect_macro_f1_mean"))

    delta = "n/a"
    if proposed_target and ablation_target:
        delta = f"{(mean(proposed_target) - mean(ablation_target)):+.4f}"

    lines: list[str] = []
    lines.append("# TEP Mechanism Evidence Summary")
    lines.append("")
    lines.append("| Proposed Target-F1 | Sample Macro-F1 | Event Macro-Recall | Path Hit Rate | No-Pairwise Target-F1 | Delta |")
    lines.append("|---:|---:|---:|---:|---:|---:|")
    lines.append(
        "| {target} | {macro} | {event} | {path_hit} | {ablation} | {delta} |".format(
            target=_mean_std(proposed_target),
            macro=_mean_std(proposed_macro),
            event=_mean_std(proposed_event),
            path_hit=_mean_std(proposed_path),
            ablation=_mean_std(ablation_target),
            delta=delta,
        )
    )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "TEP is the strongest current mechanism-evidence benchmark: it is a 22-class process fault diagnosis "
        "task with delayed propagation, weak-class confusions, and explicit expert/LLM graph priors. The "
        "pairwise/support-gated mechanism evidence is the most important positive ablation signal."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize TEP mechanism-evidence results.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--proposed", nargs="+", required=True)
    parser.add_argument("--ablation", nargs="*", default=[])
    args = parser.parse_args()
    report = summarize([Path(file) for file in args.proposed], [Path(file) for file in args.ablation])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
