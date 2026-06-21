from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AblationRow:
    component: str
    status: str
    current_evidence: str
    missing_contrast: str
    decisive_run: str
    priority: str


def current_ablation_rows() -> list[AblationRow]:
    return [
        AblationRow(
            component="validation-benefit admission",
            status="Partial",
            current_evidence="SKAB baseline 0.8343 +/- 0.0341 -> learned reliability 0.8532 +/- 0.0339",
            missing_contrast="explicit admit-without-validation-benefit route",
            decisive_run="SKAB route that admits candidate edges without validation gain filtering",
            priority="AAAI blocking",
        ),
        AblationRow(
            component="low-tail guard",
            status="Covered",
            current_evidence="C-MAPSS FixedERE improves mean F1 while TailGuardedERE gives 12/12 non-degradation",
            missing_contrast="paper table should label FixedERE as the no-low-tail contrast",
            decisive_run="no-low-tail FixedERE vs TailGuardedERE table, already materialized in reliability_term_evidence_table.md",
            priority="Paper table cleanup",
        ),
        AblationRow(
            component="counterfactual-free admission",
            status="Partial",
            current_evidence="SKAB edge perturbations drop Macro-F1 under reverse, lag-shift, and random-target changes",
            missing_contrast="training/admission variant that ignores CF_k before accepting edges",
            decisive_run="SKAB no-counterfactual admission run plus perturbation sensitivity after training",
            priority="AAAI blocking",
        ),
        AblationRow(
            component="source/complexity pruning",
            status="Partial",
            current_evidence="SKAB low-budget paired pruning improves 0.5993 +/- 0.0412 -> 0.7217 +/- 0.0529",
            missing_contrast="higher-budget e3/e5 source-role confirmation",
            decisive_run="SKAB MSFG pruning/source-role ablation with e3/e5 and seeds 42,43,44",
            priority="AAAI blocking",
        ),
        AblationRow(
            component="attention/edge-gate replacement",
            status="Missing",
            current_evidence="Theory text distinguishes reliability admission from attention and edge gates",
            missing_contrast="model variant that replaces reliability admission with learned attention or edge gate",
            decisive_run="TEP or SKAB replacement baseline: edge-gate/attention only vs reliability admission",
            priority="Run next",
        ),
        AblationRow(
            component="all LLM edges without reliability filtering",
            status="Partial",
            current_evidence="TEP all-edge/no sequence reliability pruning drops to 0.9260 +/- 0.0344",
            missing_contrast="SKAB/LLM-specific all-edge route without reliability filtering",
            decisive_run="SKAB dynamic LLM graph run with all proposed LLM edges admitted and no reliability pruning",
            priority="Run next",
        ),
        AblationRow(
            component="mechanism non-decoration",
            status="Covered",
            current_evidence="TEP full 0.9549 +/- 0.0023 vs no expert/no sequence graph 0.7432 +/- 0.0102",
            missing_contrast="none for the current TEP strict protocol",
            decisive_run="keep the strict no-expert/no-sequence row in the final ablation table",
            priority="Paper table cleanup",
        ),
    ]


def render_report(rows: list[AblationRow]) -> str:
    lines: list[str] = []
    lines.append("# Theory-Critical Reliability Ablation Matrix")
    lines.append("")
    lines.append(
        "This matrix connects the paper-ready formulation in `reliability_theory_model.md` with the "
        "current evidence in `reliability_term_evidence_table.md`. It separates evidence that is already "
        "paper-body ready from evidence that still needs one-factor ablations."
    )
    lines.append("")
    lines.append("| Component | Status | Current evidence | Missing contrast | Decisive run | Priority |")
    lines.append("|---|---|---|---|---|---|")
    for row in rows:
        lines.append(
            "| {component} | {status} | {current_evidence} | {missing_contrast} | {decisive_run} | {priority} |".format(
                component=row.component,
                status=row.status,
                current_evidence=row.current_evidence,
                missing_contrast=row.missing_contrast,
                decisive_run=row.decisive_run,
                priority=row.priority,
            )
        )
    lines.append("")
    lines.append("## Run Order")
    lines.append("")
    lines.append(
        "1. Run the SKAB no-counterfactual admission variant, because it directly tests whether `CF_k` is an "
        "admission requirement rather than a decorative diagnostic."
    )
    lines.append(
        "2. Upgrade SKAB MSFG source/complexity pruning to e3/e5 across seeds 42,43,44, because this is the "
        "weakest reliability term by budget."
    )
    lines.append(
        "3. Add an attention/edge-gate replacement baseline on TEP or SKAB, because this is the cleanest "
        "answer to the reviewer question: why not just use attention or gates?"
    )
    lines.append(
        "4. Add the SKAB all LLM edges without reliability filtering run, because it isolates whether LLM "
        "proposal must be separated from evidence admission."
    )
    lines.append(
        "5. In the final paper table, label FixedERE as the no-low-tail contrast and TailGuardedERE as the "
        "low-tail guarded route."
    )
    lines.append("")
    lines.append("## Current Conclusion")
    lines.append("")
    lines.append(
        "The theory is now formalized, but AAAI-level evidence still requires the missing and partial "
        "ablation rows to be executed or explicitly marked as appendix limitations. The most urgent "
        "blocking rows are validation-benefit admission, counterfactual-free admission, and higher-budget "
        "source/complexity pruning."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render theory-critical reliability ablation matrix.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    report = render_report(current_ablation_rows())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
