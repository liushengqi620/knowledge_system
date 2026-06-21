# Condition Monitoring of Hydraulic Systems knowledge model

- task: four component-state diagnosis targets
- split protocol: stratified cycle split per component target
- temporal unit: one cycle summarized from sensor time series
- knowledge nodes: 91
- mechanism edges: 24
- numeric features: 85
- anchor model: strong_tabular_component_state_anchor

## Model stack

1. Anchor classifier: protocol-selected strong discriminator. ExtraTrees is kept only as the unified smoke-test fallback.
2. Residual evidence: train-only normal residual and missingness head.
3. Mechanism evidence: admitted graph edges converted into edge-difference features.
4. Router: validation-selected UGMC selective logit correction with anchor fallback.
