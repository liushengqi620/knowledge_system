from __future__ import annotations

import argparse
from pathlib import Path


def render_tables() -> str:
    lines: list[str] = []
    lines.append("# Paper Final Tables")
    lines.append("")
    lines.append(
        "This file compresses the current evidence package into the tables that should appear in the main "
        "manuscript or immediately adjacent appendix. The goal is to keep the paper readable: the detailed "
        "reports remain as provenance, while these tables carry the paper-level argument."
    )
    lines.append("")
    lines.append("## Table 1. Main Multi-Benchmark Results")
    lines.append("")
    lines.append("| Dataset | Task role | Anchor/Main | Proposed reliable route | Delta | Paper claim |")
    lines.append("|---|---|---:|---:|---:|---|")
    lines.append("| TEP | strict 22-class process fault diagnosis | 0.9122 +/- 0.0134 | 0.9549 +/- 0.0023 | +0.0428 | strongest method evidence; SOTA candidate only under matched protocol |")
    lines.append("| SKAB | binary anomaly detection and dynamic graph editing | 0.8343 +/- 0.0341 | 0.8532 +/- 0.0339 | +0.0189 | reliability-filtered LLM/graph evidence |")
    lines.append("| Hydraulic | four-target state diagnosis | 0.9773 +/- 0.0321 | 0.9784 +/- 0.0301 | +0.0011 | near-ceiling non-degradation support |")
    lines.append("| C-MAPSS | original terminal RUL regression | GRU w80/cap125 RMSE 20.7559 | GRU w160/cap150 RMSE 18.0617; pseudo-terminal rerun RMSE 18.2840 | RMSE -2.6942 archived / -2.3982 validation-safe | original-task RUL gain from cap/window correction; PHM score trade-off disclosed; path fusion closed |")
    lines.append("")
    lines.append("Where to use: main experiment section.")
    lines.append("")
    lines.append("## Table 2. Reliability Evidence Ablation")
    lines.append("")
    lines.append("| Reliability question | Dataset | Contrast | Result | Interpretation |")
    lines.append("|---|---|---|---:|---|")
    lines.append("| Validation-benefit admission | SKAB | learned vs prior-only | learned 0.8532 +/- 0.0339; prior-only 0.8327 +/- 0.0477 | prior scores alone are unstable |")
    lines.append("| Dense graph injection | SKAB | learned vs all-edge | learned delta +0.0189 +/- 0.0015; all-edge delta +0.0185 +/- 0.0146 | all-edge can match mean but has higher gain variance |")
    lines.append("| Counterfactual pre-admission | SKAB | CF-guarded admission | 0.8398 +/- 0.0297; kept edges 0.3333 +/- 0.4714 | conservative guard rejects unsafe edges before deployment |")
    lines.append("| Source/complexity pruning | SKAB | full MSFG vs pruned MSFG | e5 0.6730 +/- 0.0519 -> 0.7093 +/- 0.0572; FAR 17.4899 -> 12.2486 | unsupported edge accumulation should be constrained |")
    lines.append("| Original-task correction | C-MAPSS | cap/window temporal anchor vs path challenger | GRU w80/cap125 RMSE 20.7559 -> GRU w160/cap150 RMSE 18.0617; pseudo-terminal validation rerun RMSE 18.2840; PHM score favors GRU w80/cap150 by 408.20; AnchorPath w80/cap150 RMSE 18.6666 is not admitted | derived stage labels are auxiliary; final claim uses RMSE-oriented terminal RUL with score trade-off disclosed |")
    lines.append("| Attention/gate objection | TEP sequence family | edge gate vs reliability-pruned residual gate | 0.5501 +/- 0.0089 vs 0.5514 +/- 0.0109 | reliability is not an attention weight or ordinary edge gate |")
    lines.append("| Mechanism non-decoration | TEP strict 22-class | full vs no expert/no sequence graph | 0.9549 +/- 0.0023 vs 0.7432 +/- 0.0102 | mechanism evidence materially affects decisions |")
    lines.append("")
    lines.append("Where to use: ablation section; detailed provenance remains in `final_reliability_ablation_table.md`.")
    lines.append("")
    lines.append("## Table 3. TEP Mechanism Ablation")
    lines.append("")
    lines.append("| Variant | Target-F1 | Delta vs full | Main interpretation |")
    lines.append("|---|---:|---:|---|")
    lines.append("| Full | 0.9549 +/- 0.0023 | +0.0000 | anchor plus admitted mechanism corrections |")
    lines.append("| No expert graph / no sequence graph | 0.7432 +/- 0.0102 | -0.2118 | mechanism evidence is necessary, not decorative |")
    lines.append("| No LLM graph | 0.9337 +/- 0.0229 | -0.0212 | LLM graph refinement provides measurable secondary gain |")
    lines.append("| All edges / no sequence reliability pruning | 0.9260 +/- 0.0344 | -0.0290 | unfiltered graph evidence is less stable than reliability-pruned intervention |")
    lines.append("| No residual-gated sequence verifier | 0.9398 +/- 0.0160 | -0.0151 | residual temporal verifier contributes beyond static mechanism features |")
    lines.append("| No pairwise weak-class guard | 0.9122 +/- 0.0134 | -0.0428 | weak-class pairwise correction remains an important contributor |")
    lines.append("")
    lines.append("Where to use: TEP subsection of the ablation section.")
    lines.append("")
    lines.append("## Table 4. TEP Matched Strong Baselines")
    lines.append("")
    lines.append("| Method | Target-F1 | Delta vs strict mechanism | Residual graph gain | Paper use |")
    lines.append("|---|---:|---:|---:|---|")
    lines.append("| TCN20k-NoGraph | 0.5754 +/- 0.0141 | -0.3795 | +0.0000 | tree-free temporal baseline |")
    lines.append("| TCN20k-ResidualGatedLagged | 0.6034 +/- 0.0096 | -0.3515 | +0.0280 | graph evidence helps TCN but does not replace the strict mechanism model |")
    lines.append("| GRU20k-NoGraph | 0.6150 +/- 0.0030 | -0.3399 | +0.0000 | recurrent temporal baseline |")
    lines.append("| GRU20k-ResidualGatedLagged | 0.6217 +/- 0.0073 | -0.3332 | +0.0067 | residual graph channel gives modest gain |")
    lines.append("| FT20k-NoGraph | 0.4644 +/- 0.0110 | -0.4905 | +0.0000 | tabular-transformer temporal baseline |")
    lines.append("| FT20k-ResidualGatedLagged | 0.5136 +/- 0.0218 | -0.4413 | +0.0492 | graph evidence gives the largest tree-free relative gain |")
    lines.append("| GDN20k-ResidualGatedLagged | 0.5179 +/- 0.0372 | -0.4370 | +0.1257 | residual-gated path evidence gives a large family-local gain but remains below strict mechanism route |")
    lines.append("| MTADGAT20k-ResidualGatedLagged | 0.6447 +/- 0.0038 | -0.3102 | +0.0078 | strongest tree-free temporal graph baseline; still below strict mechanism route |")
    lines.append("")
    lines.append("Where to use: main text if space allows; otherwise appendix with the key pattern summarized in text.")
    lines.append("")
    lines.append("## Table 5. Claim Boundary and Paper Use")
    lines.append("")
    lines.append("| Dataset | Current evidence level | Safe wording | Unsafe wording |")
    lines.append("|---|---|---|---|")
    lines.append("| TEP | primary positive benchmark | strict 22-class matched-protocol SOTA candidate only under matched protocol | official universal SOTA without exact external protocol reproduction |")
    lines.append("| SKAB | reliability graph-editing benchmark | matched-protocol evidence for dynamic LLM/graph reliability filtering | official leaderboard SOTA before repository/protocol alignment |")
    lines.append("| Hydraulic | supporting safety benchmark | near-ceiling non-degradation evidence | main novelty or standalone SOTA claim |")
    lines.append("| C-MAPSS | original RUL transfer benchmark | terminal-test RUL regression gain from cap/window-corrected temporal anchor; pseudo-terminal validation supports RMSE selection; PHM score trade-off is disclosed; path fusion remains closed | literature-wide RUL SOTA without exact published-protocol alignment or claiming path-fusion gain before admission |")
    lines.append("| Overall paper | method evidence | reliability-calibrated mechanism evidence fusion under non-interventional logs | not universal official SOTA and not true causal graph discovery |")
    lines.append("")
    lines.append("Where to use: claim-boundary paragraph in experiments and limitations.")
    lines.append("")
    lines.append("## Table 6. Efficiency Audit")
    lines.append("")
    lines.append("| Dataset | Branch | Status | Params | Train seconds | Test samples/s | Paper use |")
    lines.append("|---|---|---|---:|---:|---:|---|")
    lines.append("| SKAB | strong_anchor | measured, 3 seeds | 88716 | 340.54 | 2988.7 | formal anomaly-anchor efficiency |")
    lines.append("| SKAB | llm_condition_candidate_gate | measured, 3 seeds | 88716 | 345.44 | 2939.9 | LLM condition-verifier overhead is small |")
    lines.append("| C-MAPSS | original_rul_anchor | measured, 3 seeds | 119183 | 62.84 | 9667.1 | terminal RUL anchor efficiency |")
    lines.append("| C-MAPSS | anchorpath_bigru_cls020 | measured, 3 seeds | 382162 | 147.46 | 8341.6 | path-fusion challenger efficiency; not admitted as current C-MAPSS main branch |")
    lines.append("| TEP | GDN20k no/residual | measured, 3 seeds | 17942 / 35885 | 0.47 / 0.63 | 586309.7 / 330096.4 | timed efficiency rerun; not the best-performance row |")
    lines.append("| TEP | MTADGAT20k no/residual | measured, 3 seeds | 92055 / 184111 | 0.66 / 1.07 | 476639.1 / 254825.4 | timed efficiency rerun; close to recovered performance |")
    lines.append("")
    lines.append("Where to use: appendix efficiency table; TEP performance claims should still cite the best recovered performance rows in Table 4.")
    lines.append("")
    lines.append("## Integration Notes")
    lines.append("")
    lines.append(
        "Use Table 1 as the paper's main result table and Table 2 as the central ablation table. Tables 3 and 4 "
        "support the TEP mechanism story and strong-baseline audit. Table 5 prevents overclaiming by explicitly "
        "separating method evidence from official leaderboard claims. Table 6 reports measured efficiency rows; "
        "TEP efficiency uses timed reruns, while TEP performance claims use the best recovered performance rows."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render compressed final tables for the AAAI manuscript.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = render_tables()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
