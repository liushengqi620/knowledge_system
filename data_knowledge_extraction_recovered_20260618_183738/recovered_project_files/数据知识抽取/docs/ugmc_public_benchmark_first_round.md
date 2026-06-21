# UGMC Public Benchmark First Round

## Research Question

The current method should be framed as **selective mechanism correction over a strong main classifier** rather than a stack of post-processing modules. The core hypothesis is:

```text
z_final(t, c) = z0(t, c) + g(t, c) * Delta(t, c)
```

where `z0` is the strong main classifier logit and `Delta` contains mechanism, residual, and verifier evidence. The gate `g(t,c)` should prevent negative transfer by allowing correction only where the main classifier is uncertain or where the evidence agrees with the main candidate set.

## Downloaded Public Datasets

- `knowledge_exports/public_datasets/secom/secom.zip`
  - UCI SECOM semiconductor manufacturing process data.
  - Role: high-dimensional industrial process quality classification and minority-class correction.
- `knowledge_exports/public_datasets/cmapss/cmapss.zip`
  - NASA C-MAPSS turbofan degradation simulation data.
  - Role: sequence degradation and normal-dynamics residual verification.

SWaT/WADI remain high-priority but require iTrust data access approval. LiU-ICE is theoretically suitable, but a stable direct data download URL still needs to be located or requested from the authors.

## Implemented Public Benchmark Entry

Added:

```text
Scripts/public_benchmark_experiment.py
Scripts/test_public_benchmark_experiment.py
```

The benchmark supports:

- SECOM binary pass/fail classification.
- C-MAPSS FD001 health-stage classification: healthy, degraded, critical.
- Strong main classifier `f0`: ExtraTrees or LightGBM.
- Residual evidence head.
- Plain residual logit fusion.
- UGMC selective correction:

```text
z_final = z0 + g_unc * w * log p_residual
```

For SECOM, validation-tuned binary decision thresholds are used because default argmax collapses to the majority class.

## First-Round Results

### SECOM

```text
ExtraTrees:
main macro F1  = 0.544378
plain macro F1 = 0.563430
UGMC macro F1  = 0.563430

LightGBM:
main macro F1  = 0.523930
plain macro F1 = 0.524459
UGMC macro F1  = 0.524459
```

Interpretation:

- SECOM is extremely imbalanced, so threshold calibration is mandatory.
- Residual/missingness evidence can help in some splits, but the current evidence head is not consistently stronger than plain fusion.
- SECOM is useful as a minority-class robustness benchmark, but it is not the best primary dataset for the time-residual theory.

### C-MAPSS FD001

```text
ExtraTrees:
main macro F1  = 0.756306
plain macro F1 = 0.755048
UGMC macro F1  = 0.754772

LightGBM:
main macro F1  = 0.737437
plain macro F1 = 0.739719
UGMC macro F1  = 0.739954
```

Interpretation:

- C-MAPSS is a better fit for the normal-dynamics residual theory.
- With ExtraTrees, the first residual evidence head is too weak and can slightly hurt.
- With LightGBM, UGMC improves consistently across seeds, but the gain is small.
- This supports the theoretical claim that evidence must be gated, but also shows the residual evidence itself must be strengthened before claiming SOTA.

## Theory Update From Evidence

The first external experiments refine the theory:

1. The core contribution should not be "adding residual evidence"; it should be **learning when residual evidence is allowed to modify a strong main classifier**.
2. A weak residual head can still cause negative transfer, even with a strong main classifier.
3. UGMC's next theoretical layer should include an evidence-quality term:

```text
g(t,c) = sigma(a * uncertainty + b * candidate_agreement + d * evidence_quality - tau)
```

4. For sequence datasets, residual evidence should move from global residual classification to **stage-aware residual propagation**:

```text
r_t = |x_t - A_theta(x_{t-L:t-1})|
E_R(t,c) = Pool_c(GraphPropagate(r_t))
```

5. For imbalanced static datasets, the selective correction objective must include threshold/decision-boundary calibration:

```text
L = L_cls + alpha L_anchor + beta ||Delta||_1 + gamma L_threshold
```

## Next Optimization Steps

1. C-MAPSS:
   - Replace one-step Ridge residuals with a sequence GRU/TCN normal forecaster.
   - Evaluate FD001-FD004 and cross-subset transfer.
   - Add early-warning metrics by RUL bins.

2. SECOM:
   - Add calibrated LightGBM/XGBoost baselines and feature selection.
   - Treat SECOM as minority-class correction evidence, not as the main time-series proof.

3. SWaT/WADI:
   - Apply for access and use them as the main proof for control-logic graph constraints.

4. Theory:
   - Formalize UGMC as a constrained optimization problem:

```text
min CE(y, softmax(z0 + Delta))
  + alpha KL(p0 || p_final) on high-confidence samples
  + beta ||Delta||_1
  + gamma L_counterfactual_graph
```

This will make the method read as a single algorithm instead of a collection of modules.
