from __future__ import annotations

import argparse
from pathlib import Path


def render_draft() -> str:
    lines: list[str] = []
    lines.append("# Reliability-Calibrated Mechanism Evidence Fusion")
    lines.append("")
    lines.append("Working subtitle: Safe Use of Candidate Mechanism Evidence for Industrial Time-Series Fault Diagnosis")
    lines.append("")
    lines.append("## Abstract")
    lines.append("")
    lines.append(
        "Industrial fault diagnosis often requires mechanism knowledge, but non-interventional industrial "
        "time-series logs do not support a simple claim that observed correlations reveal true causal effects. "
        "We study a safer formulation: expert rules, LLM proposals, lagged relations, residual dynamics, and "
        "graph paths are treated as candidate mechanism evidence. A strong anchor model remains the primary "
        "discriminator, while each mechanism source acts as a challenger that may correct the anchor only after "
        "validation-benefit, low-tail safety, counterfactual sensitivity, and source/complexity checks. The "
        "resulting Evidence Reliability Estimator learns when candidate evidence is locally useful enough to "
        "modify predictions. Across TEP, SKAB, Hydraulic, and C-MAPSS, the current evidence shows that reliable "
        "mechanism admission improves or safely preserves strong models, with the strongest positive result on "
        "TEP strict 22-class diagnosis."
    )
    lines.append("")
    lines.append("## 1. Introduction")
    lines.append("")
    lines.append(
        "Industrial processes exhibit delayed propagation, feedback control, coupled variables, and changing "
        "operating regimes. These properties make abnormal diagnosis difficult: a fault is rarely expressed as "
        "one isolated sensor spike, and many variables respond indirectly after a lag. Domain experts can offer "
        "valuable mechanism knowledge, but actual process logs usually lack intervention records. Therefore, a "
        "diagnosis method cannot simply replace causality with correlation, and it should not assume that every "
        "expert or LLM edge is a true causal relation."
    )
    lines.append("")
    lines.append(
        "The paper targets this gap. Instead of claiming causal discovery from observational logs, we ask a more "
        "testable question: when is candidate mechanism evidence reliable enough to correct a strong anchor "
        "classifier? This reframing creates a direct research problem for industrial AI: mechanism knowledge "
        "should be useful, but only after it earns permission to affect deployment."
    )
    lines.append("")
    lines.append("Main contributions:")
    lines.append("")
    lines.append("1. We formulate mechanism fusion as evidence admission rather than true causal graph recovery.")
    lines.append("2. We introduce an Evidence Reliability Estimator that learns local usefulness of candidate evidence.")
    lines.append("3. We connect LLM-generated mechanism hypotheses to verifiable weak-class rules, not direct logit editing.")
    lines.append("4. We validate the framework across process diagnosis, anomaly detection, state diagnosis, and original RUL regression tasks.")
    lines.append("")
    lines.append("## 2. Related Work Positioning")
    lines.append("")
    lines.append(
        "The method sits between four lines of work: industrial fault diagnosis, graph-based process modeling, "
        "time-series anomaly detection, and knowledge/LLM-enhanced diagnosis. Compared with pure temporal "
        "encoders, it preserves explicit mechanism evidence. Compared with static knowledge graphs, it requires "
        "lagged residual and validation checks before graph evidence changes predictions. Compared with LLM-based "
        "reasoning, it constrains the LLM to propose candidates that must be verified by data. Compared with "
        "attention or edge-gate models, it separates representation weighting from deployment-level evidence "
        "admission."
    )
    lines.append("")
    lines.append("## 3. Problem Formulation")
    lines.append("")
    lines.append(
        "For sample or window `i`, let `x_i` be the multivariate temporal input, `y_i` the label, `r_i` residual "
        "features from normal dynamics, `g_i` the group or operating context, and `m_k` the `k`-th candidate "
        "mechanism item. The anchor prediction and mechanism challenger predictions are:"
    )
    lines.append("")
    lines.append("```math")
    lines.append("p_0(i) = f_0(x_i),")
    lines.append("p_k(i) = f_k(x_i, r_i, g_i, m_k), \\quad k=1,\\ldots,K.")
    lines.append("```")
    lines.append("")
    lines.append(
        "The anchor `p_0` is the default deployed prediction. A candidate `p_k` can be produced by an expert edge, "
        "LLM weak-class rule, lagged graph path, residual channel, or pruned multi-source graph component. The "
        "central learning problem is to decide which `m_k` is reliable enough to enter the correction set."
    )
    lines.append("")
    lines.append("## 4. Method")
    lines.append("")
    lines.append("### 4.1 Anchor Model")
    lines.append("")
    lines.append(
        "The anchor is a strong discriminator trained on the main temporal/window representation. In the current "
        "TEP evidence, this role is filled by the strict mechanism/KIEP-GL-style model family; tree-free temporal "
        "heads such as TCN, GRU, and FT-Transformer are evaluated as matched alternatives. The anchor should be "
        "strong enough that mechanism evidence is not used to compensate for an artificially weak baseline."
    )
    lines.append("")
    lines.append("### 4.2 Mechanism Evidence Generation")
    lines.append("")
    lines.append(
        "Mechanism candidates come from experts, LLM proposals, lagged statistical relations, residual dynamics, "
        "and graph paths. The LLM proposes weak-class variables, signs, lag ranges, propagation order, and "
        "confusable counterexamples. These proposals are converted into candidate graph edges, path constraints, "
        "or local verifier rules; they are not allowed to directly edit logits."
    )
    lines.append("")
    lines.append("### 4.3 Evidence Reliability Estimator")
    lines.append("")
    lines.append("A local usefulness label is defined by whether a candidate improves the anchor:")
    lines.append("")
    lines.append("```math")
    lines.append("z_{i,k}=1[ell(y_i,p_k(i)) < ell(y_i,p_0(i))-epsilon].")
    lines.append("q_psi(i,k)=P(z_{i,k}=1 | phi(p_0(i),p_k(i),x_i,g_i,m_k)).")
    lines.append("```")
    lines.append("")
    lines.append("The candidate-level reliability certificate is:")
    lines.append("")
    lines.append("```math")
    lines.append("R_k = beta_1 Delta M_k + beta_2 Q_alpha(Delta M_{k,g}) + beta_3 CF_k + beta_4 I_k + beta_5 T_k - beta_6 C_k.")
    lines.append("A_R = {k: R_k >= tau_R, Delta M_k >= eta, Q_alpha(Delta M_{k,g}) >= -epsilon, CF_k >= zeta, C_k <= c_max}.")
    lines.append("```")
    lines.append("")
    lines.append("The deployed output is:")
    lines.append("")
    lines.append("```math")
    lines.append("p^*(i) = (1-rho_i)p_0(i) + rho_i p_{k^*(i)}(i), if max_{k in A_R} q_psi(i,k) >= tau_q; otherwise p_0(i).")
    lines.append("```")
    lines.append("")
    lines.append(
        "This rule makes the relationship between the main classifier and mechanism layers explicit: mechanism "
        "evidence is a verified challenger, not a global post-hoc calibration layer."
    )
    lines.append("")
    lines.append("## 5. Theoretical Claim Boundary")
    lines.append("")
    lines.append(
        "The framework provides a validation-protocol certificate, not a distribution-free causal guarantee. If "
        "an admitted candidate satisfies non-negative or bounded low-tail validation benefit on audited groups, "
        "and the local router falls back to the anchor when reliability is low, then deployment is empirically "
        "protected against audited negative transfer. This does not prove that the candidate edge is a true causal "
        "effect; it proves that the candidate has passed the paper's declared reliability checks."
    )
    lines.append("")
    lines.append("## 6. Experiments")
    lines.append("")
    lines.append("### 6.1 Dataset Roles")
    lines.append("")
    lines.append("| Dataset | Role | Main question |")
    lines.append("|---|---|---|")
    lines.append("| TEP | Primary 22-class process fault diagnosis | Does mechanism evidence materially improve strict fault diagnosis? |")
    lines.append("| SKAB | Binary anomaly detection | Does dynamic LLM/graph evidence need reliability admission? |")
    lines.append("| Hydraulic | Four-target state diagnosis | Can the method preserve near-ceiling targets? |")
    lines.append("| C-MAPSS | Original terminal RUL regression | Does cap/window-corrected temporal evidence improve the original prognostics task while rejecting unsafe path fusion? |")
    lines.append("")
    lines.append("### 6.2 Main Result Table")
    lines.append("")
    lines.append("| Dataset | Anchor/Main | Reliable/Proposed | Delta | Current claim |")
    lines.append("|---|---:|---:|---:|---|")
    lines.append("| TEP | 0.9122 +/- 0.0134 | 0.9549 +/- 0.0023 | +0.0428 | strongest method evidence; SOTA candidate under matched protocol |")
    lines.append("| SKAB | 0.8343 +/- 0.0341 | 0.8532 +/- 0.0339 | +0.0189 | reliability-filtered dynamic graph evidence |")
    lines.append("| Hydraulic | 0.9773 +/- 0.0321 | 0.9784 +/- 0.0301 | +0.0011 | near-ceiling non-degradation support |")
    lines.append("| C-MAPSS | GRU w80/cap125 RMSE 20.7559 | GRU w160/cap150 RMSE 18.0617; pseudo-terminal rerun RMSE 18.2840 | RMSE -2.6942 archived / -2.3982 validation-safe | RMSE-oriented original-task RUL transfer evidence; PHM-score trade-off disclosed; path fusion closed |")
    lines.append("")
    lines.append("## 7. Ablation and Reliability Analysis")
    lines.append("")
    lines.append("| Question | Evidence | Interpretation |")
    lines.append("|---|---|---|")
    lines.append("| Is prior score enough? | SKAB learned `0.8532 +/- 0.0339` vs prior-only `0.8327 +/- 0.0477` | learned validation-benefit admission is needed |")
    lines.append("| Is adding every LLM edge enough? | SKAB all-edge `0.8528 +/- 0.0322`, delta variance larger than learned reliability | dense graph injection is less stable |")
    lines.append("| Does graph structure matter? | reverse, lag-shift, and target perturbations drop SKAB Macro-F1 | admitted edges are decision-relevant |")
    lines.append("| Does source/complexity pruning matter? | SKAB e5 `0.6730 +/- 0.0519 -> 0.7093 +/- 0.0572` | unsupported edge accumulation should be constrained |")
    lines.append("| Does original-task correction matter? | C-MAPSS GRU w80/cap125 RMSE `20.7559` -> GRU w160/cap150 RMSE `18.0617`; train-unit pseudo-terminal validation rerun RMSE `18.2840`; PHM score favors GRU w80/cap150 by `408.20`; AnchorPath w80/cap150 RMSE `18.6666` is not admitted | derived degradation labels are auxiliary; final claim is RMSE-oriented terminal RUL with score trade-off disclosed |")
    lines.append("| Is reliability just an edge gate? | TEP edge-gate `0.5501 +/- 0.0089` vs reliability-pruned `0.5514 +/- 0.0109` | reliability is deployment admission, not only internal gating |")
    lines.append("| Is mechanism evidence decorative? | TEP full `0.9549 +/- 0.0023` vs no expert/no sequence graph `0.7432 +/- 0.0102` | mechanism evidence materially affects diagnosis |")
    lines.append("")
    lines.append("## 8. Limitations")
    lines.append("")
    lines.append(
        "The current work should not claim universal official SOTA on every benchmark. Some external baselines are "
        "matched reconstructions rather than exact repository reproductions. The method does not recover a true "
        "causal graph, and the reliability certificate is tied to the declared validation protocol and audited "
        "groups. Hydraulic and C-MAPSS are supporting safety/generalization and original-task transfer benchmarks rather than the main "
        "novelty benchmarks."
    )
    lines.append("")
    lines.append("## 9. Current Missing Pieces Before Submission")
    lines.append("")
    lines.append("1. Complete exact external protocol alignment for any official SOTA wording, especially TEP and SKAB.")
    lines.append("2. Compress the many reports into one main experiment table, one reliability ablation table, and appendix tables.")
    lines.append("3. Add 2-3 figures: architecture, reliability admission loop, and anchor/challenger correction flow.")
    lines.append("4. Write the final related-work comparison against graph-temporal, knowledge-enhanced, and LLM-assisted diagnosis.")
    lines.append("5. Decide final claim wording: TEP as primary SOTA-candidate evidence; SKAB/Hydraulic/C-MAPSS as reliability, safety, and RUL-transfer evidence unless exact official alignment is finished.")
    lines.append("")
    lines.append("## Artifact Map")
    lines.append("")
    lines.append("| Artifact | Paper use |")
    lines.append("|---|---|")
    lines.append("| `manuscript_method_theory_section.md` | Method equations, ERE objective, deployment rule, safety proposition |")
    lines.append("| `final_reliability_ablation_table.md` | Main reliability ablation table |")
    lines.append("| `final_aaai_paper_package.md` | Contribution wording, claim boundary, manuscript assembly guide |")
    lines.append("| `v1_evidence_package.md` | Dataset-by-dataset evidence record |")
    lines.append("| `aaai_completion_matrix.md` | Remaining gates before submission |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render a manuscript-level v0 draft from the current evidence package.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    draft = render_draft()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(draft, encoding="utf-8")
    print(draft)


if __name__ == "__main__":
    main()
