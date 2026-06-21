from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetEvidence:
    dataset: str
    task: str
    main: float | None
    proposed: float | None
    delta: float | None
    strong_baselines: list[str]
    protocol_gap: str
    evidence_role: str


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def _missing_evidence(evidence: DatasetEvidence) -> str:
    gaps: list[str] = []
    if len(evidence.strong_baselines) < 2:
        gaps.append("missing strong baselines")
    if evidence.protocol_gap:
        gaps.append(evidence.protocol_gap)
    if evidence.main is None or evidence.proposed is None or evidence.delta is None:
        gaps.append("missing reproducible metric")
    return "; ".join(gaps) if gaps else "none"


def classify_dataset(evidence: DatasetEvidence) -> dict[str, str]:
    missing = _missing_evidence(evidence)
    if evidence.main is None or evidence.proposed is None or evidence.delta is None:
        return {
            "claim_level": "gap",
            "claim": "insufficient reproducible evidence for a benchmark claim",
            "missing_evidence": missing,
            "next_action": "run a complete multi-seed experiment and materialize the JSON output",
        }
    lower_is_better = "lower metric is better" in evidence.evidence_role
    improves = evidence.delta < 0 if lower_is_better else evidence.delta > 0

    if "negative-transfer" in evidence.evidence_role or "safety" in evidence.evidence_role:
        return {
            "claim_level": "safety-evidence",
            "claim": "supports non-degradation and reliability-gated correction evidence",
            "missing_evidence": missing,
            "next_action": "report as a safety/generalization benchmark and add stronger task-specific baselines",
        }

    if not improves:
        return {
            "claim_level": "gap",
            "claim": "current proposed variant does not improve the main model",
            "missing_evidence": missing,
            "next_action": "inspect failure modes before expanding the benchmark claim",
        }

    if len(evidence.strong_baselines) >= 2 and not evidence.protocol_gap:
        return {
            "claim_level": "sota-candidate",
            "claim": "candidate benchmark-leading result under the matched protocol",
            "missing_evidence": "none",
            "next_action": "freeze protocol, add confidence intervals, and prepare leaderboard-style comparison",
        }

    return {
        "claim_level": "method-evidence",
        "claim": "supports the method contribution but not a final leaderboard claim",
        "missing_evidence": missing,
        "next_action": "complete matched strong baselines before making a SOTA claim",
    }


def current_evidence_snapshot() -> list[DatasetEvidence]:
    return [
        DatasetEvidence(
            dataset="TEP",
            task="22-class process fault diagnosis",
            main=0.9122,
            proposed=0.9549,
            delta=0.0428,
            strong_baselines=["TCN20k", "GRU20k", "FT20k", "GDN20k", "MTADGAT20k"],
            protocol_gap="needs external official-protocol reproduction before universal leaderboard wording",
            evidence_role="primary mechanism benchmark",
        ),
        DatasetEvidence(
            dataset="SKAB",
            task="binary anomaly detection",
            main=0.8343,
            proposed=0.8532,
            delta=0.0189,
            strong_baselines=["usad", "tranad"],
            protocol_gap="official GDN/MTAD-GAT replication and protocol-stable leaderboard comparison still missing",
            evidence_role="LLM graph reliability benchmark",
        ),
        DatasetEvidence(
            dataset="Hydraulic",
            task="four-target state diagnosis",
            main=0.9773,
            proposed=0.9784,
            delta=0.0011,
            strong_baselines=[],
            protocol_gap="needs exact comparison against the published four-target table and deep temporal baselines",
            evidence_role="supporting industrial state-diagnosis benchmark",
        ),
        DatasetEvidence(
            dataset="C-MAPSS",
            task="original terminal RUL regression",
            main=20.7559,
            proposed=18.0617,
            delta=-2.6942,
            strong_baselines=["histgb_summary", "extra_trees_summary", "tcn_sequence", "gru_sequence"],
            protocol_gap="needs compatible published C-MAPSS RUL baselines before literature-wide SOTA wording; pseudo-terminal validation rerun RMSE 18.2840 and PHM score trade-off disclosed",
            evidence_role="original-task RUL transfer benchmark with cap/window repair, pseudo-terminal RMSE support, PHM score trade-off, and closed path fusion; lower metric is better",
        ),
    ]


def render_report(evidence_items: list[DatasetEvidence]) -> str:
    lines: list[str] = []
    lines.append("# AAAI/SOTA Readiness Audit")
    lines.append("")
    lines.append(
        "This audit separates method evidence from leaderboard claims. A dataset is treated as SOTA-ready "
        "only when the proposed result is positive, the protocol gap is closed, and at least two strong "
        "matched baselines are available."
    )
    lines.append("")
    lines.append(
        "| Dataset | Task | Main | Proposed | Delta | Evidence Level | Claim | Missing Evidence | Next Action |"
    )
    lines.append("|---|---|---:|---:|---:|---|---|---|---|")
    for evidence in evidence_items:
        audit = classify_dataset(evidence)
        lines.append(
            "| {dataset} | {task} | {main} | {proposed} | {delta} | {level} | {claim} | {missing} | {action} |".format(
                dataset=evidence.dataset,
                task=evidence.task,
                main=_fmt(evidence.main),
                proposed=_fmt(evidence.proposed),
                delta=_fmt(evidence.delta),
                level=audit["claim_level"],
                claim=audit["claim"],
                missing=audit["missing_evidence"],
                action=audit["next_action"],
            )
        )
    lines.append("")
    lines.append("## Current Decision")
    lines.append("")
    lines.append(
        "The current code and results support a reliability-calibrated mechanism-learning paper direction, "
        "with TEP as the main positive benchmark and SKAB/Hydraulic/C-MAPSS as reliability and "
        "generalization evidence. The work should not yet claim universal SOTA until the missing matched "
        "strong baselines are completed."
    )
    lines.append("")
    lines.append("## Minimum Next Experiments")
    lines.append("")
    lines.append("- TEP: keep the matched TCN/GRU/FT/GDN/MTAD-GAT evidence frozen and align external papers' exact protocols before SOTA wording.")
    lines.append("- SKAB: add protocol-stable GDN and MTAD-GAT replications beyond the current USAD/TranAD reconstruction baselines.")
    lines.append("- Hydraulic: reproduce the published four-target table in the same metric format and add a temporal neural baseline.")
    lines.append("- C-MAPSS: report original terminal RUL regression; keep derived degradation-stage labels auxiliary, disclose pseudo-terminal validation rerun RMSE 18.2840 and PHM score trade-off, and add compatible published RUL baselines.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit AAAI/SOTA readiness for current benchmark evidence.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = render_report(current_evidence_snapshot())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
