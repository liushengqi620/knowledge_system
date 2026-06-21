# UGMC-ERE Theoretical Framework

## 1. Main Research Scope

The main claim should focus on four industrial time-series/process datasets:

```text
TEP        fault propagation, weak fault classes, mechanism graph, LLM prior
C-MAPSS    degradation-stage diagnosis, unit-held-out generalization
SKAB       collective anomaly detection, run-level temporal persistence
Hydraulic  multi-component diagnosis, saturated-main-classifier safety
```

SECOM should be moved to an appendix or robustness note. It is high-dimensional and imbalanced, but it is not a strong fit for the temporal-mechanism theory because it has no natural run lifecycle, fault propagation path, or process-time causal structure. A weak SECOM result should not define the paper's main contribution.

## 2. Research Problem

In industrial fault diagnosis, strict causal discovery is usually not feasible:

```text
1. intervention data are unavailable or unsafe;
2. control loops create feedback and delayed compensation;
3. operators, controllers, and hidden states act as latent confounders;
4. faults are sparse and class imbalance is severe;
5. validation units/runs may not represent the deployment distribution.
```

Therefore the paper should not claim that the model recovers true causal effects. The more defensible problem is:

```text
Can a model use temporal-mechanism evidence as falsifiable decision evidence,
while preventing unreliable evidence from causing negative transfer?
```

This changes the research target from "causal discovery" to "reliable causal-mechanism evidence selection".

## 3. Candidate Evidence Model

For a sample or time window `i`, the base classifier outputs:

```math
p_0(i) = f_0(x_i)
```

The model then constructs `K` candidate evidence predictors:

```math
p_k(i) = f_k(x_i, r_i, g_i, m_i),  k = 1,...,K
```

where:

```text
x_i  observed process/window features
r_i  normal-dynamics residual or reconstruction residual
g_i  group context, such as unit, run, operating condition, or stage
m_i  mechanism prior, such as lag path, graph constraint, or LLM weak-class rule
```

Candidate types are not treated as guaranteed improvements. Each one is only a hypothesis:

```text
temporal residual candidate      detects deviation from learned normal dynamics
mechanism graph candidate        encodes lagged process propagation
LLM weak-class candidate         proposes class-specific variables, signs, and lags
stable/simple candidate          prevents negative transfer when the main head is already strong
```

## 4. Validation Evidence and Stability Evidence

For a candidate `k`, define a validation utility:

```math
S_k = M(D_val, p_k)
```

where `M` is the target metric, such as macro-F1 for balanced multi-class evaluation.

Because validation gains may concentrate in a small number of units or runs, the model also computes a group-stability score:

```math
\tilde S_k =
S_k
- \lambda \operatorname{Std}_g(S_{k,g})
- \gamma \max(0, S_k - \min_g S_{k,g})
- \omega C_k
```

where:

```text
S_{k,g}  candidate score in validation group g
C_k      complexity penalty for high-variance candidates
lambda   dispersion penalty
gamma    worst-group penalty
omega    candidate complexity penalty
```

This score does not replace the target metric. It answers a different question:

```text
S_k says: does this candidate look strong on validation?
\tilde S_k says: is this candidate stable enough to deploy?
```

## 5. Role-Split Reliability Guard

The latest algorithm separates two roles that were previously mixed:

```text
reference candidate r:
  the strongest temporal/mechanism candidate used to challenge ERE

fallback candidate b:
  the safest deployment candidate used when ERE evidence is not reliable enough
```

The reference candidate is selected from mechanism candidates:

```math
r = \arg\max_{k \in K_mech} S_k
```

The fallback candidate starts as the reference candidate, but can be replaced if the reference is high-complexity and unstable:

```math
b =
\begin{cases}
\arg\max_k \tilde S_k, & \text{if stability loss is large and mechanism recovery is unsafe} \\
\arg\max_{k \in K_mech} S_k, & \text{if a mechanism candidate is worst-group safe} \\
r, & \text{otherwise}
\end{cases}
```

The key rule is:

```text
simple candidates can be fallback options,
but they cannot steal the reference role from temporal/mechanism evidence.
```

This is the core theoretical improvement over a generic ensemble or post-hoc calibration layer.

## 6. Evidence Reliability Estimator

ERE learns whether candidate evidence is locally beneficial. For each candidate `k`, define a per-sample benefit label on validation data:

```math
z_{i,k} = 1[ \ell(y_i, p_k(i)) < \ell(y_i, p_0(i)) - \epsilon ]
```

ERE estimates:

```math
q_k(i) = P(z_{i,k}=1 | \phi(p_0(i), p_k(i), x_i, g_i))
```

where `phi` includes confidence, margin, entropy, candidate disagreement, stage/condition context, and other reliability features.

The routed predictor is:

```math
p_{ERE}(i) =
\begin{cases}
p_{k^*(i)}(i), & \max_k q_k(i) > \tau \\
p_0(i), & \text{otherwise}
\end{cases}
```

with:

```math
k^*(i) = \arg\max_k q_k(i)
```

## 7. Reliability Margin and Deployment Output

ERE is only deployed when it beats the reference candidate by a validation margin:

```math
M(D_val, p_{ERE}) - M(D_val, p_r) \ge \delta
```

Otherwise, the final output is the fallback candidate:

```math
p^*(i) =
\begin{cases}
p_{ERE}(i), & M(D_val, p_{ERE}) - M(D_val, p_r) \ge \delta \\
p_b(i), & \text{otherwise}
\end{cases}
```

This creates a falsifiable safety property:

```text
ERE must prove that local routing is better than the strongest mechanism reference.
If it cannot prove that, deployment falls back to the safest validated candidate.
```

## 8. Theory Claims

The paper should make three precise claims.

### Claim 1: Causal Evidence Is Falsifiable, Not Assumed

Mechanism edges, LLM rules, residual dynamics, and lagged paths are candidate evidence. They are admitted only if validation and stability evidence support them. This avoids overclaiming true causality in non-interventional industrial data.

### Claim 2: Role Separation Prevents Two Opposite Failure Modes

A single best-validation candidate can overfit validation units, while a purely conservative fallback can suppress useful temporal evidence. Separating reference and fallback roles handles both:

```text
reference role  protects temporal/mechanism evidence from being erased too early
fallback role   protects deployment from unstable high-complexity evidence
```

### Claim 3: Reliability Is a Group-Conditional Property

Evidence should not be judged only by global validation score. A candidate is reliable only if its benefit is not overly concentrated in one run, unit, condition, or stage. This is why `\tilde S_k` is necessary.

## 9. Required Experiments for AAAI-Level Evidence

The main experimental table should use TEP, C-MAPSS, SKAB, and Hydraulic. SECOM can be a secondary robustness appendix.

Required ablations:

```text
Base only
Base + plain residual fusion
Base + UGMC selective correction
Base + temporal/mechanism candidate
Base + ERE without margin guard
Base + ERE with margin guard
Base + role-split guard
Base + role-split guard without mechanism recovery
Base + role-split guard without group stability
Full model
```

Required diagnostic evidence:

```text
candidate validation score S_k
stable-adjusted score \tilde S_k
reference candidate
fallback candidate
ERE acceptance rate
ERE margin over reference
per-class recall/F1 for weak classes
per-run or per-unit worst-group score
```

## 10. Current Evidence Snapshot

Latest C-MAPSS single-seed role-split results:

```text
FD001 final 0.8089
FD002 final 0.8142
FD003 final 0.8460
FD004 final 0.7704
```

The current result is not yet SOTA-level for C-MAPSS, but the theory is becoming clearer: the contribution is not a stronger classifier alone; it is a reliability-theoretic mechanism for deciding when temporal and causal evidence should be trusted.

