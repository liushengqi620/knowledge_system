# TEP Sequence Graph Ablation 5k/e5 Findings

## Protocol

```text
model: TCN
rows: 5000
seed: 42
window_size: 24
hidden_dim: 48
epochs: 5
normal_pretrain_epochs: 3
normal_residual_features: enabled
graph_strength: 0.15
```

## Without Weak-Class Rerank

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Edges |
|---|---:|---:|---:|---:|
| no_graph | 0.3499 | 0.3363 | 0.3810 | n/a |
| all_lagged | 0.3510 | 0.3369 | 0.3810 | 79/79 |
| reliable_lagged_t070_k40 | 0.3450 | 0.3311 | 0.3810 | 40/79 |
| reliable_lagged_t050_k60 | 0.3484 | 0.3340 | 0.3810 | 60/79 |
| reliable_lagged_t060_k60 | 0.3484 | 0.3340 | 0.3810 | 60/79 |

## With Weak-Class Rerank

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Edges |
|---|---:|---:|---:|---:|
| no_graph | 0.3574 | 0.3435 | 0.3810 | n/a |
| all_lagged | 0.3607 | 0.3461 | 0.4286 | 79/79 |
| reliable_lagged_t070_k40 | 0.3593 | 0.3448 | 0.4286 | 40/79 |
| reliable_lagged_t050_k60 | 0.3593 | 0.3430 | 0.3810 | 60/79 |
| reliable_lagged_t060_k60 | 0.3593 | 0.3430 | 0.3810 | 60/79 |

## Conclusion

Longer training improves the tree-free TCN route from the earlier 2k/e1 smoke level, and weak-class rerank consistently improves Target-F1. However, the current metadata-only reliability score does not yet beat all-lagged edge injection at this budget. This is a useful negative result: the next reliability estimator should be validation-benefit driven, probing edge groups or lag classes on validation data, rather than relying only on prior edge metadata.
