from __future__ import annotations

import argparse
from pathlib import Path


def render_figures() -> str:
    lines: list[str] = []
    lines.append("# Core Paper Figures")
    lines.append("")
    lines.append(
        "This file provides editable Mermaid figure drafts and paper-ready captions for the central AAAI "
        "manuscript. The figures are designed to explain the method, not to add another experimental claim."
    )
    lines.append("")
    lines.append("## Figure 1. Reliability-Calibrated Mechanism Evidence Fusion")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph TD")
    lines.append('  X["Industrial time-series window x_i"] --> A["Strong Anchor Model f_0"]')
    lines.append('  A --> P0["Anchor prediction p_0(i)"]')
    lines.append('  X --> R["Residual Dynamics r_i"]')
    lines.append('  E["Expert Knowledge"] --> C["Candidate Mechanism Evidence m_k"]')
    lines.append('  L["LLM Weak-Class Verifier"] --> C')
    lines.append('  S["Lagged Statistical Relations"] --> C')
    lines.append('  G["Graph Paths and Source-Pruned Edges"] --> C')
    lines.append('  R --> C')
    lines.append('  C --> CH["Mechanism Challengers f_k"]')
    lines.append('  P0 --> ERE["Evidence Reliability Estimator q_psi(i,k)"]')
    lines.append('  CH --> PK["Challenger predictions p_k(i)"]')
    lines.append('  PK --> ERE')
    lines.append('  C --> CERT["Reliability certificate R_k"]')
    lines.append('  CERT --> AR["Admitted Mechanism Evidence A_R"]')
    lines.append('  ERE --> ROUTE["Reliability-gated router"]')
    lines.append('  AR --> ROUTE')
    lines.append('  ROUTE --> OUT["Final prediction p^*(i)"]')
    lines.append('  P0 --> OUT')
    lines.append("```")
    lines.append("")
    lines.append(
        "Caption: Overview of the proposed reliability-calibrated mechanism evidence fusion framework. A strong "
        "anchor model remains the default predictor. Expert knowledge, LLM weak-class hypotheses, lagged "
        "statistics, residual dynamics, and graph paths generate candidate mechanism evidence. Evidence can "
        "modify the final prediction only if it passes the reliability certificate and local ERE routing."
    )
    lines.append("")
    lines.append("Where to use: Method section, immediately after the problem formulation.")
    lines.append("")
    lines.append("## Figure 2. Evidence Reliability Admission Loop")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph LR")
    lines.append('  MK["Candidate m_k"] --> VB["Validation benefit Delta M_k"]')
    lines.append('  MK --> LT["Low-tail benefit Q_alpha"]')
    lines.append('  MK --> CF["Counterfactual sensitivity CF_k"]')
    lines.append('  MK --> INV["Invariance / stability I_k"]')
    lines.append('  MK --> TRUST["Source trust T_k"]')
    lines.append('  MK --> COMP["Complexity penalty C_k"]')
    lines.append('  VB --> SCORE["R_k"]')
    lines.append('  LT --> SCORE')
    lines.append('  CF --> SCORE')
    lines.append('  INV --> SCORE')
    lines.append('  TRUST --> SCORE')
    lines.append('  COMP --> SCORE')
    lines.append('  SCORE --> PASS{"Pass thresholds?"}')
    lines.append('  PASS -->|yes| AR["A_R: admitted evidence set"]')
    lines.append('  PASS -->|no| REJ["Reject or fallback to anchor"]')
    lines.append('  AR --> DEPLOY["Allowed to challenge p_0"]')
    lines.append('  REJ --> SAFE["No deployment edit"]')
    lines.append("```")
    lines.append("")
    lines.append(
        "Caption: Reliability admission is an auditable evidence filter. The score `R_k` combines validation gain, "
        "low-tail behavior, counterfactual sensitivity, invariance, source trust, and complexity. This differs "
        "from attention or edge gates because it decides whether an external evidence source may affect deployment."
    )
    lines.append("")
    lines.append("Where to use: Method section or Ablation section before the reliability-term table.")
    lines.append("")
    lines.append("## Figure 3. Anchor-Challenger Deployment Rule")
    lines.append("")
    lines.append("```mermaid")
    lines.append("sequenceDiagram")
    lines.append("  participant X as Window x_i")
    lines.append("  participant A as Anchor f_0")
    lines.append("  participant C as Admitted challengers A_R")
    lines.append("  participant E as ERE q_psi(i,k)")
    lines.append("  participant O as Output p^*(i)")
    lines.append("  X->>A: compute p_0(i)")
    lines.append("  X->>C: compute p_k(i) for admitted candidates")
    lines.append("  A->>E: anchor confidence and loss context")
    lines.append("  C->>E: challenger logits and mechanism features")
    lines.append("  E->>E: select k* if max q_psi(i,k) >= tau_q")
    lines.append("  alt reliable challenger exists")
    lines.append("    E->>O: mix p_0(i) and p_k*(i)")
    lines.append("  else no reliable challenger")
    lines.append("    E->>O: Fallback to anchor p_0(i)")
    lines.append("  end")
    lines.append("```")
    lines.append("")
    lines.append(
        "Caption: Deployment-level anchor/challenger correction. The final predictor `p^*(i)` uses the anchor "
        "`p_0(i)` unless an admitted challenger has sufficient local reliability `q_psi(i,k)`. This explains how "
        "the main classifier is connected to later mechanism layers without allowing unverified global logit edits."
    )
    lines.append("")
    lines.append("Where to use: Theory section after the equation defining `p^*(i)`.")
    lines.append("")
    lines.append("## Paper Integration Notes")
    lines.append("")
    lines.append(
        "Figure 1 should be the primary architecture figure. Figure 2 supports the theoretical claim that reliability "
        "is not merely a learned attention weight, edge gate, or pruning score. Figure 3 should be used when "
        "explaining the exact relationship between the strong main discriminator and later mechanism correction."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render core Mermaid figures for the AAAI manuscript.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = render_figures()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
