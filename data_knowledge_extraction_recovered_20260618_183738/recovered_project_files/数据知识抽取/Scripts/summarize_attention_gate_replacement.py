from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _metric_row(summary: dict[str, Any], variant: str) -> dict[str, Any]:
    row = summary.get(variant)
    if not isinstance(row, dict):
        raise ValueError(f"Missing variant in summary: {variant}")
    if "target_defect_macro_f1_mean" not in row:
        raise ValueError(f"Missing target_defect_macro_f1_mean for variant: {variant}")
    return row


def _fmt(row: dict[str, Any]) -> str:
    mean = float(row["target_defect_macro_f1_mean"])
    std = float(row.get("target_defect_macro_f1_std", 0.0) or 0.0)
    return f"{mean:.4f} +/- {std:.4f}"


def _mean(row: dict[str, Any]) -> float:
    return float(row["target_defect_macro_f1_mean"])


def summarize(
    *,
    tep_gatehead_path: Path,
    skab_plan_name: str,
    replacement_command: str,
) -> str:
    data = _load_json(tep_gatehead_path)
    summary = data.get("summary", {}) or {}
    no_graph = _metric_row(summary, "no_graph")
    all_lagged = _metric_row(summary, "all_lagged")
    reliable = _metric_row(summary, "reliable_lagged")
    residual_gate = _metric_row(summary, "residual_gated_lagged")

    gate_delta = _mean(residual_gate) - _mean(no_graph)
    all_delta = _mean(all_lagged) - _mean(no_graph)
    reliable_delta = _mean(reliable) - _mean(no_graph)

    lines: list[str] = []
    lines.append("# Attention/Edge-Gate Replacement Readiness")
    lines.append("")
    lines.append(
        "This report tracks the reviewer-facing question: whether reliability-calibrated evidence admission "
        "is more than a learned attention weight or ordinary edge gate."
    )
    lines.append("")
    lines.append("## Current Proxy Evidence")
    lines.append("")
    lines.append(
        "The current TEP residual gate-head run is useful proxy evidence because it compares direct lagged "
        "graph use, reliability-pruned lagged use, and a residual gated channel under the same seeds. It is "
        "not yet a decisive replacement baseline, because the gate is still attached to the reliability-pruned "
        "graph channel rather than replacing the admission rule with a purely learned edge gate."
    )
    lines.append("")
    lines.append("| Variant | Target-F1 | Delta vs no_graph | Interpretation |")
    lines.append("|---|---:|---:|---|")
    lines.append(f"| no_graph | {_fmt(no_graph)} | +0.0000 | anchor sequence head without graph evidence |")
    lines.append(
        f"| all_lagged | {_fmt(all_lagged)} | {all_delta:+.4f} | all candidate edges admitted, no reliability admission |"
    )
    lines.append(
        f"| reliable_lagged | {_fmt(reliable)} | {reliable_delta:+.4f} | prior reliability pruning with direct graph message |"
    )
    lines.append(
        f"| residual_gated_lagged | {_fmt(residual_gate)} | {gate_delta:+.4f} | reliability-pruned evidence enters through a residual gate |"
    )
    lines.append("")
    lines.append("## Why This Is Not Enough")
    lines.append("")
    lines.append(
        "The residual gate-head result shows that a gate can help when it receives already-pruned mechanism "
        "evidence. It does not prove that a learned gate can replace reliability admission, because it does "
        "not expose the gate to the same noisy expert/LLM/statistical candidate pool without validation, "
        "low-tail, and counterfactual admission constraints."
    )
    lines.append("")
    lines.append("## Decisive Replacement Run")
    lines.append("")
    lines.append(
        "The next paper-grade contrast should train a learned attention/edge-gate route that sees the same "
        "candidate edges but removes the external reliability certificate. The decisive table should compare "
        "`no_graph`, `all_lagged`, `attention_or_edge_gate_only`, and `reliability_admission` under identical "
        "seeds and protocol."
    )
    lines.append("")
    lines.append("Suggested command skeleton:")
    lines.append("")
    lines.append("```powershell")
    lines.append(replacement_command)
    lines.append("```")
    lines.append("")
    lines.append(
        f"The SKAB side should be synchronized with `{skab_plan_name}` so the paper can contrast learned gates "
        "against validation and counterfactual admission rather than only against static graph pruning."
    )
    lines.append("")
    lines.append("## Current Status")
    lines.append("")
    lines.append(
        "Status: partial proxy evidence. The row should move from pure Missing to Planned/Partial in the "
        "ablation matrix, but it is not yet complete enough for the final AAAI body table."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Summarize attention/edge-gate replacement readiness.")
    parser.add_argument("--tep-gatehead", required=True)
    parser.add_argument("--skab-plan-name", default="skab_cf_guarded_admission_suite_plan.md")
    parser.add_argument("--replacement-command", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    report = summarize(
        tep_gatehead_path=Path(args.tep_gatehead),
        skab_plan_name=args.skab_plan_name,
        replacement_command=args.replacement_command,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
