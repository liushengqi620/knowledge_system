# Final Ablation Experiment Matrix

Date: 2026-06-16

This matrix defines the final ablation table required for an AAAI-level version of the paper. The goal is not to add more modules, but to prove which evidence sources and reliability mechanisms are necessary.

## A. TEP Main-Model Ablation

| Row | Purpose | Current Status | Evidence Needed |
|---|---|---|---|
| Main anchor only | Strong discriminator without later mechanism correction | Partially available through no-pairwise/support-gated references | Final strict-protocol row with seeds 42/43/44 |
| + Expert mechanism graph | Tests expert knowledge as candidate evidence | Needs final row | Matched run with LLM disabled |
| + LLM weak-class rules | Tests LLM as weak-class verifier, not global editor | Partial diagnostics exist | Matched run with expert graph fixed and LLM rule verifier toggled |
| + Pairwise weak-class guard | Tests hard-class confusion correction | Strong positive reference exists | Include current `0.9122 -> 0.9549` path |
| + Support-gated persistence | Tests temporal persistence only when mechanism support exists | Strong reference exists | Include event macro-recall effect |
| + Residual-gated sequence verifier | Tests constrained graph intervention route | Available in strict tree-anchor result | Include `0.9520 -> 0.9549` and event recall `0.8413 -> 0.9048` |

## B. Graph Injection Ablation

| Row | Purpose | Current Status | Evidence Needed |
|---|---|---|---|
| No graph | Tree-free temporal baseline | Available for TCN/GRU/FT/GDN/MTAD-GAT | Use matched family-local deltas |
| All lagged edges | Tests naive graph injection | Available for TCN/GDN/MTAD-GAT and likely GRU/FT variants | Summarize as negative or neutral baseline |
| Reliability-pruned lagged edges | Tests edge admission without residual intervention | Available | Show direct pruning alone is insufficient |
| Residual-gated lagged graph | Tests edge-plus-intervention reliability | Available and positive for TCN/GRU/FT/MTAD-GAT trend | Main graph-injection ablation row |
| Validation-probe residual graph | Tests lag selection by validation/low-tail evidence | Available for TCN/GRU/FT | Include as reliability variant |

## C. ERE Reliability-Term Ablation

| Row | Purpose | Current Status | Evidence Needed |
|---|---|---|---|
| Full ERE | Learns local candidate usefulness | Available on SKAB/C-MAPSS, partial TEP | Final table row by dataset |
| No low-tail guard | Tests negative-transfer control | Partial | Run/report candidate selected only by mean validation gain |
| No complexity penalty | Tests protection against high-variance candidates | Unit tests exist; dataset row missing | Add public benchmark ablation |
| No counterfactual consistency | Tests whether edge direction/lag matters | SKAB counterfactual result exists; final row missing | Add row: original vs reverse/lag-shift/random-target |
| No source/role prior | Tests expert/LLM/source role separation | Missing | Add ablation where all evidence roles share one admission rule |

## D. LLM-Specific Ablation

| Row | Purpose | Current Status | Evidence Needed |
|---|---|---|---|
| No LLM evidence | Checks dependence on LLM | Needs final TEP/SKAB row | Disable LLM weak rules and dynamic LLM graph |
| LLM all edges | Tests harmful unfiltered LLM graph | Partial from SKAB observations | Materialize report row |
| LLM reliability-filtered edges | Tests proposed LLM role | Available in SKAB learned reliability | Include `0.8343 -> 0.8532` |
| LLM weak-class verifier only | Tests LLM as local verifier, not global calibrator | Partial | Final TEP weak-class row |
| LLM global logit editor | Negative control | Conceptually rejected | Optional appendix if already run |

## E. Strong Baseline Table

| Method Family | Status | Current Target-F1 Evidence |
|---|---|---:|
| Strict mechanism/KIEP-GL-style | Main result | `0.9549 +/- 0.0023` |
| TCN no graph | Complete | `0.5754 +/- 0.0141` |
| TCN residual-gated lagged graph | Complete | `0.6034 +/- 0.0096` |
| GRU no graph | Complete | `0.6150 +/- 0.0030` |
| GRU residual-gated lagged graph | Complete | `0.6217 +/- 0.0073` |
| FT-Transformer no graph | Complete | `0.4644 +/- 0.0110` |
| FT-Transformer residual-gated lagged graph | Complete | `0.5136 +/- 0.0218` |
| GDN-style no graph | Low-budget trend only | `0.1461 +/- 0.0221` at 5k/3epoch |
| GDN-style residual-gated lagged graph | Low-budget trend only | `0.1448 +/- 0.0190` at 5k/3epoch |
| MTAD-GAT-style no graph | 5k/3epoch trend | `0.2528 +/- 0.0225` |
| MTAD-GAT-style residual-gated lagged graph | 5k/3epoch trend | `0.2607 +/- 0.0261` |

## Completion Gate

The final paper table should contain:

1. A primary TEP table with strict mechanism result and strong baselines.
2. A mechanism ablation table showing expert/LLM/pairwise/persistence/residual-verifier contributions.
3. A graph-injection table showing direct all-edge injection is unsafe and residual-gated injection is safer.
4. An ERE term ablation table showing low-tail, counterfactual, complexity, and role constraints are necessary.
5. A multi-dataset role table showing TEP as main evidence, SKAB as LLM/dynamic graph evidence, Hydraulic as non-degradation evidence, and C-MAPSS as tail-risk transfer evidence.

