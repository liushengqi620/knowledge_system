from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


@dataclass(frozen=True)
class ResultRow:
    label: str
    path: str
    mode: str
    changed_edges: int
    baseline_macro_f1: float
    macro_f1: float
    delta_vs_baseline: float
    drop_vs_original: float
    binary_f1: float
    far: float
    mar: float
    edge_policy: str
    kept_edges: int


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _row(label: str, path: Path, *, original_macro: float | None = None) -> ResultRow:
    data = _load(path)
    dynamic = data["dynamic_llm_kg"]
    baseline = data["baseline"]
    binary = dynamic["protocol"]["binary"]
    policy = data.get("edge_policy", {}) or {}
    cf = data.get("edge_counterfactual", {}) or {}
    macro = float(dynamic["metrics"]["macro_f1"])
    base = float(baseline["metrics"]["macro_f1"])
    return ResultRow(
        label=str(label),
        path=path.name,
        mode=str(cf.get("mode", "none")),
        changed_edges=int(cf.get("n_changed_edges", 0) or 0),
        baseline_macro_f1=base,
        macro_f1=macro,
        delta_vs_baseline=float(data.get("macro_f1_delta", macro - base)),
        drop_vs_original=0.0 if original_macro is None else macro - float(original_macro),
        binary_f1=float(binary["f1"]),
        far=float(binary["far_percent"]),
        mar=float(binary["mar_percent"]),
        edge_policy=str(policy.get("policy", "unknown")),
        kept_edges=int(policy.get("n_kept_edges", len(data.get("dynamic_edges", []) or [])) or 0),
    )


def _fmt(value: float) -> str:
    return f"{float(value):.4f}"


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} +/- {pstdev(values):.4f}"


def summarize(*, original: Path, perturbations: list[tuple[str, Path]]) -> str:
    original_row = _row("No-CF Admission", original)
    rows = [original_row] + [
        _row(label, path, original_macro=original_row.macro_f1) for label, path in perturbations
    ]
    drops = [row.drop_vs_original for row in rows[1:]]
    far_increases = [row.far - original_row.far for row in rows[1:]]
    lines: list[str] = []
    lines.append("# SKAB Counterfactual Admission Ablation")
    lines.append("")
    lines.append(
        "This report treats the learned-reliability SKAB route as the no-CF admission route: candidate "
        "LLM/mechanism edges are admitted by validation-style reliability and FAR guards, while `CF_k` is "
        "not used as a pre-admission requirement. The perturbation rows are post-admission perturbation "
        "diagnostics over the admitted edge set."
    )
    lines.append("")
    lines.append("| Variant | Mode | Changed Edges | Macro-F1 | Delta vs Baseline | Drop vs No-CF | Binary F1 | FAR | MAR | Edge Policy | Kept Edges |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|")
    for row in rows:
        lines.append(
            "| {label} | {mode} | {changed} | {macro} | {delta} | {drop} | {bf1} | {far:.2f} | {mar:.2f} | {policy} | {edges} |".format(
                label=row.label,
                mode=row.mode,
                changed=row.changed_edges,
                macro=_fmt(row.macro_f1),
                delta=f"{row.delta_vs_baseline:+.4f}",
                drop=f"{row.drop_vs_original:+.4f}",
                bf1=_fmt(row.binary_f1),
                far=row.far,
                mar=row.mar,
                policy=row.edge_policy,
                edges=row.kept_edges,
            )
        )
    lines.append("")
    lines.append("## Diagnostic Summary")
    lines.append("")
    lines.append(f"- No-CF admission route Macro-F1: {_fmt(original_row.macro_f1)}")
    lines.append(f"- No-CF admission route delta vs baseline: {original_row.delta_vs_baseline:+.4f}")
    lines.append(f"- mean perturbation drop vs no-CF admission: {_mean_std(drops)}")
    lines.append(f"- mean FAR increase under perturbation: {_mean_std(far_increases)}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The no-CF admission route is useful, but its admitted edge set is sensitive to counterfactual "
        "perturbations. This supports the theory term `CF_k`: edge direction, lag, and target structure are "
        "decision-relevant. However, this is not yet a pre-admission CF guard, because the perturbations are "
        "applied after edge admission rather than used to reject edges before deployment."
    )
    lines.append("")
    lines.append("AAAI status: Partial.")
    lines.append("")
    lines.append(
        "Run next: implement a true pre-admission counterfactual guard that rejects an edge or edge set unless "
        "its validation benefit is reduced by a required amount under reverse-direction, lag-shift, or "
        "random-target perturbation."
    )
    lines.append("")
    return "\n".join(lines)


def _parse_item(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError(f"Expected label=path item, got: {raw}")
    label, path = raw.split("=", 1)
    return label.strip(), Path(path.strip())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Summarize SKAB no-counterfactual admission ablation.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--original", required=True)
    parser.add_argument("--perturbation", action="append", default=[], help="Items in label=path form.")
    args = parser.parse_args(argv)

    report = summarize(
        original=Path(args.original),
        perturbations=[_parse_item(item) for item in args.perturbation],
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
