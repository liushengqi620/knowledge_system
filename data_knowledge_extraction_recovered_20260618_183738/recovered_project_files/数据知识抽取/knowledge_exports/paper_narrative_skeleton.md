# Paper Narrative Skeleton

Date: 2026-06-16

## Working Title

Reliability-Calibrated Mechanism Evidence Fusion for Industrial Time-Series Fault Diagnosis

## Core Problem Statement

Industrial time-series fault diagnosis often requires mechanism knowledge, but real deployments rarely provide interventional data. Control loops, delayed compensation, latent operator states, and fault sparsity make it unsafe to treat correlations, expert edges, or LLM-generated relations as true causal effects. The paper studies a narrower and more defensible problem:

```text
How can a diagnostic model safely use unreliable temporal-mechanism evidence
under non-interventional industrial time-series data, while preventing
wrong expert/LLM/statistical evidence from degrading a strong main model?
```

## Main Thesis

Expert knowledge, LLM suggestions, lagged statistical relations, and normal-dynamics residuals should not be injected as trusted causal truth. They should be treated as candidate mechanism evidence. Each candidate is allowed to affect predictions only when it passes validation benefit, low-tail non-degradation, role constraints, and counterfactual checks. This converts mechanism fusion from a heuristic graph augmentation problem into a reliability-certified evidence admission problem.

## Contributions

1. **Problem reframing.** We formulate industrial mechanism fusion without claiming true causal discovery from observational logs. The key object is falsifiable candidate mechanism evidence, not a recovered causal graph.

2. **Reliability-calibrated evidence admission.** We introduce an Evidence Reliability Estimator that evaluates whether a candidate evidence source is locally beneficial before it can modify the anchor prediction.

3. **Residual-gated mechanism intervention.** We show that graph evidence should enter as a constrained residual verifier rather than direct all-edge smoothing. Across TCN, GRU, FT-Transformer, GDN-style, and MTAD-GAT-style sequence families, residual-gated lagged evidence is safer than direct graph injection.

4. **LLM as weak-class mechanism verifier.** LLM knowledge is not used as a global logit editor. It proposes weak-class variables, signs, lags, and rules, which are admitted only after validation and counterfactual checks.

5. **Multi-benchmark validation.** TEP validates weak-class mechanism diagnosis; SKAB validates dynamic LLM/graph reliability filtering; Hydraulic validates non-degradation near ceiling; C-MAPSS validates tail-risk reliability routing in degradation-stage diagnosis.

## Mathematical Core

For sample/window `i`, the anchor model predicts:

```math
p_0(i)=f_0(x_i).
```

Candidate mechanism evidence `k` produces:

```math
p_k(i)=f_k(x_i,r_i,g_i,m_i),
```

where `r_i` is normal-dynamics residual evidence, `g_i` is run/unit/stage context, and `m_i` is a candidate mechanism rule, lagged edge, graph path, or LLM weak-class verifier.

The group-wise benefit is:

```math
B_{g,k}=M(D_{g}^{val},p_k)-M(D_{g}^{val},p_0).
```

A candidate is admitted only if:

```math
\mathcal A = \{k:
\Delta M_k \ge \eta,
\; Q_\alpha(B_{g,k}) \ge -\epsilon,
\; CF_k \ge \zeta,
\; C_k \le c_{max}
\}.
```

The reliability estimator predicts local usefulness:

```math
q_\psi(i,k)=P[\ell(y_i,p_k(i)) < \ell(y_i,p_0(i))-\epsilon
\mid \phi(p_0,p_k,x_i,g_i,m_i)].
```

The deployed predictor is:

```math
p^*(i)=
\begin{cases}
(1-\rho_i)p_0(i)+\rho_i p_{k^*}(i),
& k^* \in \mathcal A,\; q_\psi(i,k^*) \ge \tau,\\
p_0(i), & \text{otherwise},
\end{cases}
```

with:

```math
k^*=\arg\max_k q_\psi(i,k).
```

This makes the connection between the strong main classifier and later layers explicit: the main classifier is the anchor; later modules are challengers; the reliability layer decides whether a challenger can locally correct the anchor.

## Key Experimental Messages

### TEP

TEP is the primary benchmark. The strict mechanism model reaches:

```text
0.9549 +/- 0.0023 Target-F1
```

compared with:

```text
0.9122 +/- 0.0134 no-pairwise/support-gated baseline
```

The tree-free strong-baseline trend table shows that generic sequence or graph-temporal models remain far below the strict mechanism model, but residual-gated graph evidence improves over no-graph within most families:

```text
TCN20k:      0.5754 -> 0.6034
GRU20k:      0.6150 -> 0.6217
FT20k:       0.4644 -> 0.5136
GDN10k:      0.3051 -> 0.3159
MTADGAT10k:  0.5013 -> 0.5113
```

### SKAB

SKAB supports the dynamic LLM/graph reliability claim:

```text
main baseline:       0.8343 +/- 0.0341
learned reliability: 0.8532 +/- 0.0339
```

Counterfactual edge perturbations reduce performance, showing that admitted edge direction and lag are used as decision evidence rather than decorative explanations.

### Hydraulic

Hydraulic validates safety near ceiling:

```text
main:     0.9773 +/- 0.0321
reliable: 0.9784 +/- 0.0301
```

The important point is non-degradation and small gain on the difficult valve target.

### C-MAPSS

C-MAPSS validates tail-risk routing:

```text
main pooled:      0.7972 +/- 0.0228
Fixed ERE pooled: 0.8030 +/- 0.0236
TailGuardedERE:   12/12 non-degradation
```

## Claim Boundary

The paper can safely claim:

```text
The method provides reliability-certified mechanism evidence fusion and
shows strong method evidence across industrial benchmarks, with TEP as the
primary positive mechanism-diagnosis result.
```

The paper should not yet claim:

```text
Universal official SOTA on every benchmark.
```

Remaining SOTA-critical work is full-budget or official-style baseline alignment, especially for TEP and SKAB.

