# Reliability-Calibrated Mechanism Graph Progress

## Core Hypothesis

Expert and LLM mechanism graphs in observational industrial time-series data should be treated as noisy candidate evidence rather than ground-truth causal graphs. A candidate edge should affect the temporal graph model only after it passes a reliability check based on validation benefit, false-alarm risk, and mechanism-role plausibility.

## Implemented Model Upgrade

The SKAB dynamic graph experiment now supports an automatic `learned_reliability` policy. It replaces hand-written edge filtering with a single-edge probe calibration procedure:

1. Load or generate LLM candidate lagged edges.
2. Train the baseline MSFG-Time-TCN without dynamic LLM edges.
3. Probe each candidate edge individually on the validation split.
4. Score each edge using validation Macro-F1 gain, binary F1 gain, FAR/MAR deltas, edge complexity, slow-variable penalty, and mechanism-role bonus.
5. Admit only reliable low-risk edges into the final MSFG-Time-TCN.

This turns the model from `LLM edges + graph + TCN` into a reliability-calibrated graph-learning pipeline.

## Mathematical Form

For a candidate edge `e = (u -> v, lags, weight, reliability)`, the implemented score is:

```text
r_e = sigmoid(4 * (s_e - 0.30))

s_e =
  0.65 * prior_e
  + 2.75 * DeltaMacroF1_e
  + 1.25 * DeltaBinaryF1_e
  - 2.00 * max(DeltaFAR_e / 100, 0)
  - 0.50 * max(DeltaMAR_e / 100, 0)
  - 0.015 * complexity_e
  - slow_variable_penalty_e
  + mechanism_role_bonus_e
```

Only edges with `r_e >= tau` and `DeltaFAR_e <= rho` enter the final graph.

## SKAB Evidence

Three-seed run-level split results:

| Seed | Baseline Macro-F1 | Learned Macro-F1 | Delta Macro-F1 | Binary F1 | FAR | MAR | Edges |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 0.8817 | 0.8999 | +0.0182 | 0.8702 | 7.26 | 12.58 | 4 |
| 43 | 0.8028 | 0.8203 | +0.0175 | 0.7629 | 11.16 | 25.44 | 3 |
| 44 | 0.8185 | 0.8394 | +0.0209 | 0.7971 | 14.51 | 15.78 | 1 |

Aggregate:

```text
Baseline Macro-F1: 0.8343 +/- 0.0341
Learned Macro-F1:  0.8532 +/- 0.0339
Delta Macro-F1:    0.0189 +/- 0.0015
```

Interpretation: the reliability estimator yields consistent positive gains across splits, supporting the core hypothesis. However, absolute performance varies across run splits, so this is not yet sufficient for a stable SOTA claim.

## Hydraulic Evidence

Hydraulic four-target three-seed results:

| Target | Main | UGMC | Learned | SafeLearned | ERE |
|---|---:|---:|---:|---:|---:|
| cooler | 1.0000 +/- 0.0000 | 1.0000 +/- 0.0000 | 1.0000 +/- 0.0000 | 1.0000 +/- 0.0000 | 1.0000 +/- 0.0000 |
| valve | 0.9280 +/- 0.0272 | 0.9230 +/- 0.0207 | 0.9290 +/- 0.0202 | 0.9315 +/- 0.0237 | 0.9256 +/- 0.0240 |
| pump | 0.9960 +/- 0.0030 | 0.9960 +/- 0.0030 | 0.9951 +/- 0.0041 | 0.9960 +/- 0.0030 | 0.9960 +/- 0.0030 |
| accumulator | 0.9850 +/- 0.0028 | 0.9837 +/- 0.0047 | 0.9860 +/- 0.0037 | 0.9860 +/- 0.0037 | 0.9850 +/- 0.0028 |

Interpretation: Hydraulic validates the industrial state-diagnosis side. Cooler and pump are near-ceiling; valve is the most informative target and shows that safe learned routing can improve over the main model.

## Current AAAI-Readiness Assessment

Positive:

- The model now has a clear research question: how to safely use noisy mechanism knowledge in industrial time-series diagnosis.
- SKAB demonstrates that all LLM edges can hurt while reliability-calibrated edges help.
- Hydraulic provides a second industrial benchmark with strong multi-target results.
- The implementation records selected edges and edge-level diagnostics, improving reproducibility.

Still missing:

- Strong external baselines such as GDN, MTAD-GAT, TranAD, Anomaly Transformer, and USAD.
- A third dataset such as TEP, C-MAPSS, or SMD.
- Counterfactual perturbation experiments for admitted edges.
- Stability improvement for difficult SKAB splits.

## Next Experiments

1. Add counterfactual edge tests: shuffle lag, reverse direction, mask source, and random target replacement.
2. Run C-MAPSS and/or TEP as the next industrial dataset.
3. Add at least two strong anomaly-detection baselines.
4. Generate a formal ablation table: all edges, no reliability, learned reliability, without FAR penalty, without mechanism-role prior, without MSFG gate.
