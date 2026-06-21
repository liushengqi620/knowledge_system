# Skoltech Anomaly Benchmark knowledge model

- task: binary point/run anomaly detection
- split protocol: run-held-out split, validation runs selected from training runs
- temporal unit: run_id sample_index
- knowledge nodes: 17
- mechanism edges: 6
- numeric features: 9
- anchor model: run_level_anomaly_anchor_with_dynamic_graph_challengers

## Model stack

1. Anchor classifier: protocol-selected strong discriminator. ExtraTrees is kept only as the unified smoke-test fallback.
2. Residual evidence: train-only normal residual and missingness head.
3. Mechanism evidence: admitted graph edges converted into edge-difference features.
4. Router: validation-selected UGMC selective logit correction with anchor fallback.
