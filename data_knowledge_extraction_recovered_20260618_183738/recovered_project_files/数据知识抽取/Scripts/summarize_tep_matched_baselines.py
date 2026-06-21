from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


METRICS = [
    ("target_defect_macro_f1", "Target-F1"),
    ("macro_f1", "Sample Macro-F1"),
    ("event_macro_recall", "Event Macro-Recall"),
    ("path_hit_rate", "Path Hit"),
]


@dataclass(frozen=True)
class BaselineSpec:
    label: str
    path: Path | None = None
    variant: str | None = None
    manual_metrics: dict[str, float] | None = None
    role: str = "baseline"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _summary_table_row(data: dict[str, Any]) -> dict[str, Any] | None:
    for row in data.get("summary_table", []) or []:
        if str(row.get("experiment_name", "")) == "full_model":
            return dict(row)
    return None


def _sequence_summary_row(data: dict[str, Any], variant: str | None) -> dict[str, Any] | None:
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return None
    name = str(variant or "")
    if name and isinstance(summary.get(name), dict):
        return dict(summary[name])
    if not name and isinstance(summary.get("residual_gated_lagged"), dict):
        return dict(summary["residual_gated_lagged"])
    if not name and summary:
        first_key = next(iter(summary))
        if isinstance(summary.get(first_key), dict):
            return dict(summary[first_key])
    return None


def _normalise_manual(metrics: dict[str, float] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in (metrics or {}).items():
        out[str(key)] = float(value)
    return out


def _row_for_spec(spec: BaselineSpec) -> dict[str, Any]:
    if spec.manual_metrics:
        return _normalise_manual(spec.manual_metrics)
    if spec.path is None:
        raise ValueError(f"Baseline {spec.label} requires either path or manual_metrics")
    data = _load(spec.path)
    row = _summary_table_row(data)
    if row is not None:
        return row
    row = _sequence_summary_row(data, spec.variant)
    if row is not None:
        return row
    raise ValueError(f"Cannot find metrics for {spec.label} in {spec.path}")


def _metric_value(row: dict[str, Any], metric: str) -> tuple[float | None, float | None]:
    mean_key = f"{metric}_mean"
    std_key = f"{metric}_std"
    if mean_key not in row:
        return None, None
    return float(row[mean_key]), float(row.get(std_key, 0.0) or 0.0)


def _fmt(mean: float | None, std: float | None) -> str:
    if mean is None:
        return "n/a"
    return f"{mean:.4f} +/- {float(std or 0.0):.4f}"


def _source(spec: BaselineSpec) -> str:
    if spec.path is None:
        return "manual-record"
    name = Path(spec.path).name
    if spec.variant:
        return f"{name}::{spec.variant}"
    return name


def _parse_spec(raw: str) -> BaselineSpec:
    if "=" not in raw:
        raise ValueError("Spec must use Label=path or Label=path::variant")
    label, rest = raw.split("=", 1)
    variant = None
    path_raw = rest.strip()
    if "::" in path_raw:
        path_raw, variant = path_raw.split("::", 1)
    return BaselineSpec(label=label.strip(), path=Path(path_raw.strip()), variant=(variant.strip() if variant else None))


def _parse_manual(raw: str) -> BaselineSpec:
    parts = [part.strip() for part in str(raw).split(",") if part.strip()]
    if len(parts) < 2 or "=" not in parts[0]:
        raise ValueError("Manual spec must look like Label=0.9549,std=0.0023")
    label, value = parts[0].split("=", 1)
    metrics = {"target_defect_macro_f1_mean": float(value)}
    for item in parts[1:]:
        key, raw_value = item.split("=", 1)
        if key.strip() == "std":
            metrics["target_defect_macro_f1_std"] = float(raw_value)
        else:
            metrics[str(key).strip()] = float(raw_value)
    return BaselineSpec(label=label.strip(), manual_metrics=metrics)


def _family_key(label: str) -> str:
    raw = str(label)
    if "-" in raw:
        return raw.split("-", 1)[0]
    return raw


def _sort_key(row: dict[str, Any]) -> tuple[int, str]:
    label = str(row.get("label", ""))
    order = {
        "TCN20k": 0,
        "GRU20k": 1,
        "FT20k": 2,
        "GDN20k": 3,
        "MTADGAT20k": 4,
    }
    return order.get(_family_key(label), 99), label


def summarize(reference: BaselineSpec, baselines: list[BaselineSpec]) -> str:
    reference_row = _row_for_spec(reference)
    reference_target, reference_target_std = _metric_value(reference_row, "target_defect_macro_f1")
    if reference_target is None:
        raise ValueError("Reference must include target_defect_macro_f1_mean")

    resolved: list[dict[str, Any]] = []
    for spec in baselines:
        row = _row_for_spec(spec)
        target, target_std = _metric_value(row, "target_defect_macro_f1")
        macro, macro_std = _metric_value(row, "macro_f1")
        event, event_std = _metric_value(row, "event_macro_recall")
        path_hit, path_hit_std = _metric_value(row, "path_hit_rate")
        delta_ref = None if target is None else target - reference_target
        resolved.append(
            {
                "label": spec.label,
                "target": target,
                "target_std": target_std,
                "macro": macro,
                "macro_std": macro_std,
                "event": event,
                "event_std": event_std,
                "path_hit": path_hit,
                "path_hit_std": path_hit_std,
                "delta_ref": delta_ref,
                "source": _source(spec),
                "role": spec.role,
            }
        )

    resolved.sort(key=_sort_key)
    family_no_graph: dict[str, float] = {}
    for row in resolved:
        if "NoGraph" in str(row["label"]) and row["target"] is not None:
            family_no_graph[_family_key(str(row["label"]))] = float(row["target"])
    lines: list[str] = []
    lines.append("# TEP Matched Baseline Evidence")
    lines.append("")
    lines.append("## Reference")
    lines.append("")
    lines.append(
        f"- {reference.label}: Target-F1 {_fmt(reference_target, reference_target_std)}; source `{_source(reference)}`."
    )
    lines.append("")
    lines.append("## Matched TEP Protocol Baselines")
    lines.append("")
    lines.append("| Method | Target-F1 | Delta vs Strict | Delta vs Family NoGraph | Sample Macro-F1 | Event Macro-Recall | Path Hit | Source |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for row in resolved:
        delta_no_graph = "n/a"
        local_no_graph = family_no_graph.get(_family_key(str(row["label"])))
        if local_no_graph is not None and row["target"] is not None:
            delta_no_graph = f"{(float(row['target']) - float(local_no_graph)):+.4f}"
        delta_ref = "n/a" if row["delta_ref"] is None else f"{float(row['delta_ref']):+.4f}"
        lines.append(
            "| {label} | {target} | {delta_ref} | {delta_no_graph} | {macro} | {event} | {path_hit} | `{source}` |".format(
                label=row["label"],
                target=_fmt(row["target"], row["target_std"]),
                delta_ref=delta_ref,
                delta_no_graph=delta_no_graph,
                macro=_fmt(row["macro"], row["macro_std"]),
                event=_fmt(row["event"], row["event_std"]),
                path_hit=_fmt(row["path_hit"], row["path_hit_std"]),
                source=row["source"],
            )
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This report separates matched TEP protocol evidence into two questions. First, the strict mechanism "
        "model remains the main high-performing classifier. Second, within the tree-free sequence family, "
        "lagged residual-gated graph evidence should improve over the no-graph temporal baseline before it "
        "is treated as a meaningful replacement direction. The current table is therefore a baseline and "
        "mechanism-ablation audit, not a claim that tree-free sequence heads already beat KIEP-GL."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize matched TEP strict and tree-free baseline evidence.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--reference", required=True, help="Label=path[::variant]")
    parser.add_argument("--reference-manual", default="", help="Alternative manual reference: Label=mean,std=value")
    parser.add_argument("--baseline", action="append", default=[], help="Label=path[::variant]")
    parser.add_argument("--manual-baseline", action="append", default=[], help="Label=mean,std=value")
    args = parser.parse_args()

    reference = _parse_manual(args.reference_manual) if str(args.reference_manual).strip() else _parse_spec(args.reference)
    baselines = [_parse_spec(item) for item in args.baseline] + [_parse_manual(item) for item in args.manual_baseline]
    report = summarize(reference, baselines)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
