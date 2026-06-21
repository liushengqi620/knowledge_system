from __future__ import annotations

import argparse
from pathlib import Path


def render_section() -> str:
    lines: list[str] = []
    lines.append("# Manuscript Method and Theory Section")
    lines.append("")
    lines.append("## Problem Formulation")
    lines.append("")
    lines.append(
        "We study reliability-calibrated use of candidate mechanism evidence in non-interventional "
        "industrial time-series diagnosis. The goal is not causal discovery and not recovery of a true "
        "process causal graph from observational logs. Instead, the model receives candidate mechanism evidence "
        "from experts, LLM proposals, lagged statistical relations, residual dynamics, and graph paths, and must "
        "decide which evidence is safe enough to modify a strong anchor classifier."
    )
    lines.append("")
    lines.append(
        "For each window or sample `i`, let `x_i` denote the observed multivariate time-series features, "
        "`y_i` the diagnosis label, `g_i` the run/unit/stage context, `r_i` residual evidence from normal dynamics, "
        "and `m_k` the `k`-th candidate mechanism item. A candidate may be a lagged edge, graph path, weak-class "
        "rule, source-pruned graph channel, or LLM-proposed verifier."
    )
    lines.append("")
    lines.append("## Anchor and Candidate Challengers")
    lines.append("")
    lines.append("The model separates the primary discriminator from later mechanism corrections:")
    lines.append("")
    lines.append("```math")
    lines.append("p_0(i) = f_0(x_i),")
    lines.append("p_k(i) = f_k(x_i, r_i, g_i, m_k), \\quad k=1,\\ldots,K.")
    lines.append("```")
    lines.append("")
    lines.append(
        "`p_0` is the anchor prediction and remains the default deployed output. `p_k` is a challenger generated "
        "by one admitted candidate evidence source. This anchor/challenger design makes the relationship between "
        "the main classifier and later mechanism layers explicit: mechanism evidence does not overwrite the main "
        "model globally; it must earn permission to act locally."
    )
    lines.append("")
    lines.append("## Evidence Reliability Estimator")
    lines.append("")
    lines.append("A candidate is useful only when it improves the anchor on a local sample or group. We define:")
    lines.append("")
    lines.append("```math")
    lines.append("z_{i,k}=\\mathbf{1}[\\ell(y_i,p_k(i)) < \\ell(y_i,p_0(i))-\\epsilon].")
    lines.append("```")
    lines.append("")
    lines.append("The Evidence Reliability Estimator (ERE) predicts this local usefulness:")
    lines.append("")
    lines.append("```math")
    lines.append("q_\\psi(i,k)=P(z_{i,k}=1\\mid \\phi(p_0(i),p_k(i),x_i,g_i,m_k)).")
    lines.append("```")
    lines.append("")
    lines.append(
        "The training objective combines anchor learning, challenger learning, ERE supervision, and low-tail "
        "safety regularization:"
    )
    lines.append("")
    lines.append("```math")
    lines.append("\\mathcal{L}=\\mathcal{L}_0+\\lambda_c\\mathcal{L}_c+\\lambda_{ERE}\\mathcal{L}_{ERE}+\\lambda_s\\mathcal{L}_s,")
    lines.append("\\mathcal{L}_0=\\sum_i CE(y_i,p_0(i)),")
    lines.append("\\mathcal{L}_c=\\sum_{i,k\\in A_R} CE(y_i,p_k(i)),")
    lines.append("\\mathcal{L}_{ERE}=\\sum_{i,k\\in A_R} BCE(z_{i,k},q_\\psi(i,k)),")
    lines.append("\\mathcal{L}_s=\\sum_{k\\in A_R}\\max(0,\\epsilon_s-Q_\\alpha(\\Delta M_{k,g})).")
    lines.append("```")
    lines.append("")
    lines.append(
        "This objective gives the closed-loop learning target: the model learns a strong anchor, learns candidate "
        "challengers, estimates when a challenger beats the anchor, and penalizes candidates whose validation "
        "benefit collapses in low-tail groups."
    )
    lines.append("")
    lines.append("## Candidate-Level Reliability Certificate")
    lines.append("")
    lines.append("Before deployment, each candidate must pass an evidence certificate:")
    lines.append("")
    lines.append("```math")
    lines.append("R_k=\\beta_1\\Delta M_k")
    lines.append("+\\beta_2 Q_\\alpha(\\Delta M_{k,g})")
    lines.append("+\\beta_3 CF_k")
    lines.append("+\\beta_4 I_k")
    lines.append("+\\beta_5 T_k")
    lines.append("-\\beta_6 C_k.")
    lines.append("```")
    lines.append("")
    lines.append("The admitted set is:")
    lines.append("")
    lines.append("```math")
    lines.append("A_R=\\{k: R_k\\ge \\tau_R,\\; \\Delta M_k\\ge \\eta,\\;")
    lines.append("Q_\\alpha(\\Delta M_{k,g})\\ge -\\epsilon,\\; CF_k\\ge \\zeta,\\; C_k\\le c_{max}\\}.")
    lines.append("```")
    lines.append("")
    lines.append(
        "`Delta M_k` is the validation benefit over the anchor, `Q_alpha(Delta M_{k,g})` is low-tail group "
        "benefit, `CF_k` is counterfactual sensitivity, `I_k` is invariance or stability evidence, `T_k` is "
        "source/role trust, and `C_k` penalizes graph or rule complexity. These terms are externally auditable "
        "evidence signals rather than hidden attention weights."
    )
    lines.append("")
    lines.append("## Deployment Rule")
    lines.append("")
    lines.append("At deployment, the model selects the locally most useful admitted challenger:")
    lines.append("")
    lines.append("```math")
    lines.append("k^*(i)=\\arg\\max_{k\\in A_R} q_\\psi(i,k).")
    lines.append("```")
    lines.append("")
    lines.append("The final prediction is:")
    lines.append("")
    lines.append("```math")
    lines.append("p^*(i)=\\begin{cases}")
    lines.append("(1-\\rho_i)p_0(i)+\\rho_i p_{k^*(i)}(i), & \\max_{k\\in A_R}q_\\psi(i,k)\\ge \\tau_q,\\\\")
    lines.append("p_0(i), & \\text{otherwise.}")
    lines.append("\\end{cases}")
    lines.append("```")
    lines.append("")
    lines.append(
        "Thus the system falls back to the anchor whenever no candidate passes global admission or local "
        "reliability. This fallback is the central safety valve that prevents unvalidated expert or LLM evidence "
        "from globally editing predictions."
    )
    lines.append("")
    lines.append("## Proposition: Empirical Low-Tail Safety")
    lines.append("")
    lines.append(
        "Proposition. On a fixed validation protocol with audited groups `g`, assume every deployed candidate "
        "satisfies `Q_alpha(Delta M_{k,g}) >= -epsilon` and the router falls back to the anchor when "
        "`q_psi(i,k^*) < tau_q`. Then the admitted correction has empirical low-tail degradation bounded by "
        "`epsilon` on the audited groups. This is a validation-protocol certificate, not a distribution-free "
        "causal guarantee."
    )
    lines.append("")
    lines.append(
        "This proposition formalizes what the method can and cannot claim. It certifies that admitted evidence "
        "does not violate the audited low-tail safety condition; it does not prove that the observational data "
        "identify a true causal effect."
    )
    lines.append("")
    lines.append("## Why the LLM Cannot Directly Edit Predictions")
    lines.append("")
    lines.append(
        "The LLM acts as a weak-class mechanism verifier and candidate generator. It may propose important "
        "variables, lag ranges, signs, propagation orders, and confusable counterexamples, but those proposals "
        "become active only if they pass reliability admission. The LLM does not directly change logits and does "
        "not act as a global calibrator."
    )
    lines.append("")
    lines.append("## Difference from Attention, Gates, and Pruning")
    lines.append("")
    lines.append(
        "The certificate is not attention: attention changes internal representation mass, whereas `R_k` decides "
        "whether an external evidence source may affect deployment. It is not an edge gate: a gate can keep a "
        "relation because it helps the training loss, while reliability can reject it if it fails low-tail or "
        "counterfactual checks. It is not graph pruning alone: pruning changes topology, whereas reliability also "
        "decides whether a pruned candidate may locally correct the anchor."
    )
    lines.append("")
    lines.append("## Experiment Links")
    lines.append("")
    lines.append("| Theory component | Dataset evidence |")
    lines.append("|---|---|")
    lines.append("| Validation-benefit admission | SKAB learned reliability `0.8532 +/- 0.0339` vs prior-only `0.8327 +/- 0.0477` |")
    lines.append("| Dense graph contrast | SKAB all-edge `0.8528 +/- 0.0322` with higher gain variance than learned reliability |")
    lines.append("| Source/complexity term | SKAB e5 pruning `0.6730 +/- 0.0519 -> 0.7093 +/- 0.0572` |")
    lines.append("| Counterfactual relevance | SKAB reverse/lag/target perturbations drop `-0.0234`, `-0.0106`, `-0.0203` |")
    lines.append("| Low-tail safety | C-MAPSS TailGuardedERE gives `12/12 non-degradation` |")
    lines.append("| Mechanism non-decoration | TEP full `0.9549 +/- 0.0023` vs no expert/no sequence graph `0.7432 +/- 0.0102` |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render manuscript-ready method and theory section.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    section = render_section()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(section, encoding="utf-8")
    print(section)


if __name__ == "__main__":
    main()
