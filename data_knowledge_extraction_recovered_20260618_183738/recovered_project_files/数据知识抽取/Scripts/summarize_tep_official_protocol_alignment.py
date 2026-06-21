from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MetricRecord:
    method: str
    target_f1: str
    role: str
    source: str


@dataclass(frozen=True)
class ProtocolEvidence:
    task: str
    protocol: str
    primary_metric: str
    secondary_metrics: tuple[str, ...]
    strict_results: tuple[MetricRecord, ...]
    treefree_results: tuple[MetricRecord, ...]

    @classmethod
    def current(cls) -> "ProtocolEvidence":
        return cls(
            task="TEP 22-class process fault diagnosis",
            protocol=(
                "Strict 22-class matched protocol using raw 52-variable graph interface, metadata split, "
                "20k training rows, seeds 42/43/44, Target-F1 as the primary metric, and event/path "
                "metrics as secondary diagnostics."
            ),
            primary_metric="Target-F1",
            secondary_metrics=("Event Macro-Recall", "Path Hit"),
            strict_results=(
                MetricRecord(
                    method="StrictMechanism",
                    target_f1="0.9549 +/- 0.0023",
                    role="anchor plus reliability-admitted mechanism evidence",
                    source="tep_main_model_ablation_evidence.md",
                ),
                MetricRecord(
                    method="NoExpertNoSequenceGraph",
                    target_f1="0.7432 +/- 0.0102",
                    role="removes expert/LLM graph evidence from main prior and sequence branch",
                    source="tep_main_model_ablation_evidence.md",
                ),
                MetricRecord(
                    method="NoLLMExpertOnlyGraph",
                    target_f1="0.9337 +/- 0.0229",
                    role="keeps expert graph while removing LLM graph refinement",
                    source="tep_main_model_ablation_evidence.md",
                ),
                MetricRecord(
                    method="AllEdgesNoReliability",
                    target_f1="0.9260 +/- 0.0344",
                    role="admits all graph edges without sequence reliability pruning",
                    source="tep_main_model_ablation_evidence.md",
                ),
            ),
            treefree_results=(
                MetricRecord(
                    method="TCN20k-NoGraph",
                    target_f1="0.5754 +/- 0.0141",
                    role="tree-free temporal no-graph baseline",
                    source="tep_matched_strong_baseline_evidence.md",
                ),
                MetricRecord(
                    method="TCN20k-ResidualGatedLagged",
                    target_f1="0.6034 +/- 0.0096",
                    role="TCN with residual-gated lagged graph evidence",
                    source="tep_matched_strong_baseline_evidence.md",
                ),
                MetricRecord(
                    method="GRU20k-NoGraph",
                    target_f1="0.6150 +/- 0.0030",
                    role="tree-free temporal no-graph baseline",
                    source="tep_matched_strong_baseline_evidence.md",
                ),
                MetricRecord(
                    method="GRU20k-ResidualGatedLagged",
                    target_f1="0.6217 +/- 0.0073",
                    role="GRU with residual-gated lagged graph evidence",
                    source="tep_matched_strong_baseline_evidence.md",
                ),
                MetricRecord(
                    method="FT20k-NoGraph",
                    target_f1="0.4644 +/- 0.0110",
                    role="tree-free tabular transformer no-graph baseline",
                    source="tep_matched_strong_baseline_evidence.md",
                ),
                MetricRecord(
                    method="FT20k-ResidualGatedLagged",
                    target_f1="0.5136 +/- 0.0218",
                    role="FT-Transformer with residual-gated lagged graph evidence",
                    source="tep_matched_strong_baseline_evidence.md",
                ),
                MetricRecord(
                    method="GDN20k-NoGraph",
                    target_f1="0.3922 +/- 0.0510",
                    role="GDN-style no-graph baseline under matched budget",
                    source="tep_gdn_20k_e10_recovered.json",
                ),
                MetricRecord(
                    method="GDN20k-ResidualGatedLagged",
                    target_f1="0.5179 +/- 0.0372",
                    role="GDN-style residual-gated lagged graph channel",
                    source="tep_gdn_20k_e10_recovered.json",
                ),
                MetricRecord(
                    method="MTADGAT20k-NoGraph",
                    target_f1="0.6369 +/- 0.0050",
                    role="MTAD-GAT-style no-graph baseline under matched budget",
                    source="tep_mtad_20k_e10_recovered.json",
                ),
                MetricRecord(
                    method="MTADGAT20k-ResidualGatedLagged",
                    target_f1="0.6447 +/- 0.0038",
                    role="MTAD-GAT-style residual-gated lagged graph channel",
                    source="tep_mtad_20k_e10_recovered.json",
                ),
            ),
        )


def _append_table(lines: list[str], rows: tuple[MetricRecord, ...]) -> None:
    lines.append("| Method | Target-F1 | Role | Source |")
    lines.append("|---|---:|---|---|")
    for row in rows:
        lines.append(f"| {row.method} | {row.target_f1} | {row.role} | `{row.source}` |")


def render_report(evidence: ProtocolEvidence) -> str:
    lines: list[str] = []
    lines.append("# TEP Official-Style Protocol Alignment Note")
    lines.append("")
    lines.append("## Protocol-aligned claim boundary")
    lines.append("")
    lines.append(f"- Task: {evidence.task}.")
    lines.append(f"- Current protocol: {evidence.protocol}")
    lines.append(f"- Primary metric: {evidence.primary_metric}.")
    lines.append(f"- Secondary diagnostics: {', '.join(evidence.secondary_metrics)}.")
    lines.append("")
    lines.append("## Matched strict mechanism evidence")
    lines.append("")
    _append_table(lines, evidence.strict_results)
    lines.append("")
    lines.append("## Matched tree-free and graph-temporal evidence")
    lines.append("")
    _append_table(lines, evidence.treefree_results)
    lines.append("")
    lines.append("## Official-style boundary")
    lines.append("")
    lines.append(
        "These results are matched-protocol method evidence. They are not a direct leaderboard claim unless "
        "an external paper's exact split, preprocessing, class taxonomy, training regime, delay handling, "
        "and metric definition are reproduced."
    )
    lines.append("")
    lines.append(
        "Do not compare directly against 2-class anomaly detection, 21-fault-only settings, random point "
        "splits, normal-only detection protocols, point-adjusted event metrics, or any report that changes "
        "the fault taxonomy or delay treatment."
    )
    lines.append("")
    lines.append("## Safe claim")
    lines.append("")
    lines.append(
        "Under our strict 22-class matched TEP protocol, reliability-calibrated mechanism evidence strongly "
        "outperforms tree-free graph/temporal baselines, and ablations show that the mechanism evidence is "
        "not merely decorative."
    )
    lines.append("")
    lines.append("## Unsafe claim")
    lines.append("")
    lines.append("Universal official SOTA on TEP.")
    lines.append("")
    lines.append("## Next action")
    lines.append("")
    lines.append(
        "When citing external TEP papers, reproduce their exact protocol or report their numbers only as "
        "non-identical reference evidence."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render the TEP official-style protocol boundary note.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    report = render_report(ProtocolEvidence.current())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
