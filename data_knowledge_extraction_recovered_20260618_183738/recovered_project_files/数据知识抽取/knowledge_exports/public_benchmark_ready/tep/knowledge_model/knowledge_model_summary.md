# Tennessee Eastman Process knowledge model

- task: 22-class process fault diagnosis
- split protocol: official train/test files with train-only validation split
- temporal unit: source_file/run sample_index
- knowledge nodes: 63
- mechanism edges: 79
- numeric features: 52
- anchor model: strict_mechanism_kiep_gl_tree_anchor

## Model stack

1. Anchor classifier: protocol-selected strong discriminator. ExtraTrees is kept only as the unified smoke-test fallback.
2. Residual evidence: train-only normal residual and missingness head.
3. Mechanism evidence: admitted graph edges converted into edge-difference features.
4. Router: validation-selected UGMC selective logit correction with anchor fallback.
