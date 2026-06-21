# C-MAPSS turbofan degradation knowledge model

- task: degradation-stage classification from RUL thresholds
- split protocol: NASA train/test units with train-only validation split
- temporal unit: subset/unit/cycle
- knowledge nodes: 34
- mechanism edges: 31
- numeric features: 27
- anchor model: lightgbm_lifecycle_anchor

## Model stack

1. Anchor classifier: protocol-selected strong discriminator. ExtraTrees is kept only as the unified smoke-test fallback.
2. Residual evidence: train-only normal residual and missingness head.
3. Mechanism evidence: admitted graph edges converted into edge-difference features.
4. Router: validation-selected UGMC selective logit correction with anchor fallback.
