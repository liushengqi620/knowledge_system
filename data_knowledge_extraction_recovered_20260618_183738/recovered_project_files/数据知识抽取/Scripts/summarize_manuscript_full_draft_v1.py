from __future__ import annotations

import argparse
from pathlib import Path


def render_draft_v1() -> str:
    lines: list[str] = []
    lines.append("# Reliability-Calibrated Mechanism Evidence Fusion")
    lines.append("")
    lines.append("Subtitle: Safe Use of Candidate Mechanism Evidence for Industrial Time-Series Fault Diagnosis")
    lines.append("")
    lines.append("## Abstract")
    lines.append("")
    lines.append(
        "Industrial time-series fault diagnosis benefits from mechanism knowledge, yet industrial logs usually do "
        "not contain interventions. Control loops, delayed compensations, operating-condition shifts, and sparse "
        "fault labels make it unsafe to interpret every expert relation, statistical lag, or LLM-generated edge as "
        "a true causal effect. This paper studies a reliability-calibrated alternative. We treat expert rules, LLM "
        "proposals, lagged relations, residual dynamics, and graph paths as candidate mechanism evidence rather "
        "than recovered causal truth. A strong anchor discriminator remains the default predictor, and each "
        "mechanism source acts as a challenger that can modify the anchor only after validation-benefit, low-tail "
        "safety, counterfactual sensitivity, and source/complexity checks. The resulting Evidence Reliability "
        "Estimator learns when a candidate source is locally useful enough to correct the anchor. Across TEP, "
        "SKAB, Hydraulic, and C-MAPSS, the current evidence shows that reliability-calibrated mechanism admission "
        "improves or safely preserves strong models, with the strongest positive result on strict 22-class TEP "
        "fault diagnosis."
    )
    lines.append("")
    lines.append("## 1. Introduction")
    lines.append("")
    lines.append(
        "Modern industrial processes are not collections of independent sensors. Variables respond through material "
        "flows, feedback loops, controller actions, and delayed physical propagation. A valve fault can first "
        "appear as a local flow change, then as a pressure deviation, and only later as a downstream quality or "
        "temperature response. This temporal and structural coupling is exactly why mechanism knowledge is useful "
        "for diagnosis. At the same time, practical process logs are usually observational. Operators rarely run "
        "controlled interventions for the sake of model identification, and fault examples are often sparse, "
        "imbalanced, or affected by operating regime changes."
    )
    lines.append("")
    lines.append(
        "This creates the central tension of the paper. We want to use expert knowledge, graph paths, lagged "
        "statistics, and LLM-generated mechanism suggestions, but we cannot claim that these sources directly "
        "recover the true causal graph. A correlation can reflect control compensation rather than physical cause; "
        "an expert edge can be valid in one operating regime but harmful in another; an LLM can produce a plausible "
        "mechanism that is not predictive under the actual plant data. The research question is therefore not "
        "\"how do we discover the true causal graph?\" but \"when is candidate mechanism evidence reliable enough "
        "to correct a strong diagnostic model?\""
    )
    lines.append("")
    lines.append(
        "We answer this question with a reliability-calibrated mechanism evidence fusion framework. The core design "
        "choice is to keep a strong anchor classifier as the primary discriminator. Mechanism evidence is not "
        "allowed to globally rewrite the output. Instead, each evidence source becomes a challenger whose local "
        "usefulness is estimated, audited, and admitted only when it passes explicit reliability checks. This turns "
        "mechanism fusion into a falsifiable evidence-admission problem under non-interventional industrial logs."
    )
    lines.append("")
    lines.append("The contributions are:")
    lines.append("")
    lines.append("1. We formulate industrial mechanism fusion as candidate evidence admission rather than causal discovery.")
    lines.append("2. We introduce an Evidence Reliability Estimator that learns local usefulness relative to a strong anchor.")
    lines.append("3. We convert LLM mechanism suggestions into weak-class verifiers and graph constraints, not direct logit edits.")
    lines.append("4. We validate the framework through main results, reliability ablations, mechanism ablations, and protocol audits across four industrial benchmarks.")
    lines.append("")
    lines.append("## 2. Related Work")
    lines.append("")
    lines.append(
        "Industrial fault diagnosis methods often rely on process variables, temporal windows, and class-specific "
        "fault signatures. Classical models emphasize statistical process monitoring and feature engineering, "
        "while modern methods use neural sequence encoders, reconstruction models, graph neural networks, or "
        "Transformer-style temporal representations. These models can be strong discriminators, but they often "
        "treat process structure implicitly. When failure modes are weak, delayed, or coupled, a purely data-driven "
        "representation may miss mechanistic propagation patterns."
    )
    lines.append("")
    lines.append(
        "Graph-based time-series diagnosis attempts to encode variable relations, sensor dependencies, or learned "
        "adjacency structures. The difficulty is that graph edges learned from observational time series are not "
        "automatically causal. Attention weights, edge gates, or learned adjacency scores can improve training loss "
        "without proving that an edge is safe to use at deployment. Our work differs by making graph use an "
        "audited admission decision: a candidate edge or path must pass validation-benefit, low-tail, and "
        "counterfactual checks before it can correct the anchor."
    )
    lines.append("")
    lines.append(
        "Knowledge-enhanced diagnosis introduces expert rules, mechanism paths, or domain priors. Such knowledge is "
        "valuable but can be incomplete, stale, or regime-dependent. LLM-assisted scientific reasoning adds another "
        "source of candidate mechanisms, because an LLM can propose variables, signs, lag ranges, propagation order, "
        "and confusable counterexamples. We do not use the LLM as a global calibrator. Instead, the LLM verifier "
        "generates candidate evidence that must survive the same reliability checks as expert and statistical "
        "evidence."
    )
    lines.append("")
    lines.append("## 3. Problem Setup")
    lines.append("")
    lines.append(
        "For a window or sample `i`, let `x_i` be the multivariate industrial time-series input, `y_i` the fault or "
        "state label, `r_i` the residual evidence from normal dynamics, `g_i` the operating or group context, and "
        "`m_k` the `k`-th candidate mechanism item. A candidate may be an expert edge, an LLM weak-class rule, a "
        "lagged statistical relation, a residual-triggered graph path, or a source-pruned multi-edge structure."
    )
    lines.append("")
    lines.append("The anchor prediction and candidate challenger predictions are:")
    lines.append("")
    lines.append("```math")
    lines.append("p_0(i) = f_0(x_i),")
    lines.append("p_k(i) = f_k(x_i, r_i, g_i, m_k), \\quad k=1,\\ldots,K.")
    lines.append("```")
    lines.append("")
    lines.append(
        "`p_0` is the default deployed prediction. `p_k` is a mechanism-conditioned challenger. The problem is to "
        "learn when, if ever, `p_k` should be allowed to modify the anchor. This setup makes the connection between "
        "the main classifier and later mechanism layers explicit: mechanism evidence is neither a disconnected "
        "explanation nor an unchecked post-processing module."
    )
    lines.append("")
    lines.append("## 4. Method")
    lines.append("")
    lines.append("### 4.1 Strong Anchor and Mechanism Challengers")
    lines.append("")
    lines.append(
        "The anchor is trained as a strong primary discriminator on the main temporal or window representation. In "
        "the current TEP evidence, the strict mechanism/KIEP-GL-style route provides the strongest anchor-family "
        "result, while TCN, GRU, FT-Transformer, GDN-style, and MTAD-GAT-style heads serve as matched strong "
        "baselines. The anchor must be strong because a weak anchor would make any auxiliary mechanism appear "
        "useful. The proposed framework is therefore evaluated as correction of a strong model, not rescue of an "
        "artificially weak one."
    )
    lines.append("")
    lines.append("### 4.2 Candidate Mechanism Evidence")
    lines.append("")
    lines.append(
        "Candidate mechanism evidence is collected from multiple sources. Expert knowledge provides physical or "
        "process-flow relations. Lagged statistical tests provide temporal precedence hints. Residual dynamics "
        "identify deviations from normal behavior. Graph paths connect variables through candidate propagation "
        "structures. The LLM verifier proposes weak-class variables, signs, lag ranges, propagation sequences, and "
        "confusable counterexamples. All of these are treated as candidate evidence, not guaranteed truth."
    )
    lines.append("")
    lines.append("### 4.3 Evidence Reliability Estimator")
    lines.append("")
    lines.append("A candidate is locally useful only if it improves the anchor by a margin:")
    lines.append("")
    lines.append("```math")
    lines.append("z_{i,k}=1[\\ell(y_i,p_k(i)) < \\ell(y_i,p_0(i))-\\epsilon].")
    lines.append("q_\\psi(i,k)=P(z_{i,k}=1\\mid \\phi(p_0(i),p_k(i),x_i,g_i,m_k)).")
    lines.append("```")
    lines.append("")
    lines.append("The candidate-level certificate is:")
    lines.append("")
    lines.append("```math")
    lines.append("R_k = \\beta_1\\Delta M_k + \\beta_2Q_\\alpha(\\Delta M_{k,g}) + \\beta_3CF_k + \\beta_4I_k + \\beta_5T_k - \\beta_6C_k.")
    lines.append("A_R = \\{k: R_k\\ge\\tau_R, \\Delta M_k\\ge\\eta, Q_\\alpha(\\Delta M_{k,g})\\ge-\\epsilon, CF_k\\ge\\zeta, C_k\\le c_{max}\\}.")
    lines.append("```")
    lines.append("")
    lines.append(
        "`Delta M_k` measures validation benefit over the anchor, `Q_alpha` measures low-tail group behavior, "
        "`CF_k` measures counterfactual sensitivity, `I_k` measures stability, `T_k` measures source trust, and "
        "`C_k` penalizes unsupported complexity. This score is not an attention weight: it is an admission rule for "
        "whether external evidence may affect deployment."
    )
    lines.append("")
    lines.append("### 4.4 Deployment Rule")
    lines.append("")
    lines.append("```math")
    lines.append("p^*(i)=\\begin{cases}")
    lines.append("(1-\\rho_i)p_0(i)+\\rho_i p_{k^*(i)}(i), & \\max_{k\\in A_R}q_\\psi(i,k)\\ge\\tau_q,\\\\")
    lines.append("p_0(i), & \\text{otherwise.}")
    lines.append("\\end{cases}")
    lines.append("```")
    lines.append("")
    lines.append(
        "The router falls back to the anchor when no admitted challenger is locally reliable. This fallback is the "
        "practical safety mechanism that prevents erroneous LLM or expert edges from globally changing the model."
    )
    lines.append("")
    lines.append("## 5. Theory and Claim Boundary")
    lines.append("")
    lines.append(
        "The theoretical claim is empirical low-tail safety under a declared validation protocol. If an admitted "
        "candidate satisfies bounded low-tail degradation on audited groups and the router falls back when local "
        "reliability is low, then admitted corrections are empirically protected against audited negative transfer. "
        "This is not a distribution-free causal guarantee. It does not prove that a graph edge is a true physical "
        "cause; it proves that the candidate evidence passed the paper's reliability checks under the stated data "
        "protocol."
    )
    lines.append("")
    lines.append(
        "This boundary is central to the paper. The method is intentionally conservative: it uses mechanism evidence "
        "because process knowledge matters, but it does not collapse mechanism plausibility into causal truth. The "
        "protocol/SOTA wording in `paper_protocol_sota_audit.md` should be treated as a hard guardrail when writing "
        "the final experiments and limitations."
    )
    lines.append("")
    lines.append("## 6. Experiments")
    lines.append("")
    lines.append(
        "The experiment design assigns each dataset a specific role. TEP is the primary mechanism-diagnosis benchmark. "
        "SKAB tests dynamic LLM/graph reliability filtering. Hydraulic tests near-ceiling non-degradation, especially "
        "on the harder valve target. C-MAPSS tests whether reliability routing transfers to degradation-stage "
        "temporal settings."
    )
    lines.append("")
    lines.append(
        "Table 1 in `paper_final_tables.md` should be the main multi-benchmark table. The current main results are "
        "`0.9549 +/- 0.0023` on TEP and `0.8532 +/- 0.0339` on SKAB, with Hydraulic and C-MAPSS supporting safety "
        "and transfer claims. Figure 1 in `paper_core_figures.md` should be placed before the method details to "
        "show the overall architecture. Figure 2 explains the reliability admission loop, and Figure 3 explains "
        "the anchor/challenger deployment rule."
    )
    lines.append("")
    lines.append(
        "Table 2 is the central reliability ablation table. It shows that prior-only edge scores are unstable, "
        "all-edge graph injection has higher gain variance, counterfactual guards can reject unsafe edges, "
        "source/complexity pruning improves SKAB e5 performance, and C-MAPSS TailGuardedERE achieves `12/12 "
        "non-degradation`. Table 3 isolates TEP mechanism components, including no-expert, no-LLM, and all-edge "
        "variants. Table 4 summarizes strong matched TEP baselines, showing that residual graph evidence improves "
        "tree-free heads but does not yet replace the strict mechanism route."
    )
    lines.append("")
    lines.append(
        "The experiment narrative should avoid overclaiming. According to `paper_protocol_sota_audit.md`, TEP is the "
        "primary SOTA-candidate benchmark under the strict matched protocol, but official SOTA wording requires "
        "exact external protocol alignment. SKAB remains reliability-editing evidence until official repository "
        "alignment and threshold/event-scoring policies are reproduced."
    )
    lines.append("")
    lines.append("## 7. Limitations")
    lines.append("")
    lines.append(
        "The method does not recover a true causal graph from observational logs. It certifies candidate mechanism "
        "evidence under validation audits. It is not universal official SOTA across every benchmark. Hydraulic and "
        "C-MAPSS currently support safety and transfer rather than the main novelty claim. Some external baselines "
        "remain matched reconstructions rather than exact repository reproductions. Final official SOTA wording "
        "requires exact split, preprocessing, metric definition, threshold tuning, delay handling, budget, and "
        "source availability alignment."
    )
    lines.append("")
    lines.append("## 8. Submission Checklist")
    lines.append("")
    lines.append("| Item | Current artifact | Remaining action |")
    lines.append("|---|---|---|")
    lines.append("| Full draft | `manuscript_full_draft_v1.md` | polish into final LaTeX or Word manuscript |")
    lines.append("| Method equations | `manuscript_method_theory_section.md` | synchronize notation and move into Method/Theory |")
    lines.append("| Tables | `paper_final_tables.md` | place Table 1/Table 2 in main text and move support tables to appendix |")
    lines.append("| Figures | `paper_core_figures.md` | render camera-ready figures from Mermaid drafts |")
    lines.append("| Claim boundary | `paper_protocol_sota_audit.md` | complete exact external protocol alignment before official SOTA wording |")
    lines.append("| Related work | this v1 draft | add exact citations and final comparison paragraphs |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render expanded v1 manuscript draft.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    draft = render_draft_v1()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(draft, encoding="utf-8")
    print(draft)


if __name__ == "__main__":
    main()
