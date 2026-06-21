# TEP Residual-Gated Lagged Graph Findings

## Implemented Upgrade

The tree-free TEP sequence route now supports a residual-gated lagged graph evidence head. Direct lagged graph fusion uses:

```text
X'_t = (1 - alpha * B_t) * X_t + alpha * B_t * M_G(X)_t
```

where `M_G(X)_t` is the incoming lagged graph message. The new residual-gated route instead keeps the main temporal input unchanged and builds a separate standardized graph evidence stream:

```text
E_G(t) = zscore_train(alpha * B_t * (M_G(X)_t - X_t))
logits = f_theta(X) + sigmoid(gamma) * h_phi(E_G)
```

The gate is initialized at `gamma=-3.0`, so graph evidence starts as a small correction and can be learned upward only when useful. This makes the graph an auditable residual verifier rather than a forced feature smoother.

## Code Paths

```text
Scripts/tep_sequence_heads.py
  append_lagged_graph_residual_channel
  _standardized_lagged_graph_residuals
  _ResidualGatedSequenceModule
  train_sequence_model(..., lagged_graph_fusion_mode="residual_channel")

Scripts/run_tep_sequence_graph_ablation.py
  --include-residual-gated
  residual_gated_lagged
  validation_probe_residual_lagged
```

## Evidence

### 5k/e5 seed42 weak rerank

```text
File: knowledge_exports/tep_sequence_graph_ablation_residual_gatehead_seed42_e5_5k_weakrerank.json
no_graph target-F1: 0.3709
all_lagged target-F1: 0.3650
reliable_lagged target-F1: 0.3584
residual_gated_lagged target-F1: 0.3808
validation_probe_residual_lagged target-F1: 0.3739
selected_lags: [1]
```

### 10k/e10 seed42 weak rerank

```text
File: knowledge_exports/tep_sequence_graph_ablation_residual_gatehead_seed42_e10_10k_weakrerank.json
no_graph target-F1: 0.5311
all_lagged target-F1: 0.5281
reliable_lagged target-F1: 0.5168
residual_gated_lagged target-F1: 0.5621
validation_probe_residual_lagged target-F1: 0.5620
event macro-recall: no_graph 0.6667 -> residual_gated_lagged 0.7143
selected_lags: [2]
learned graph gate: about 0.054
```

## Conclusion

The new result resolves the earlier negative finding. Direct graph smoothing can hurt a strong TCN sequence head, but a residual-gated graph evidence branch improves the same 10k/e10 setting by `+0.0310` target-F1 over no graph and by `+0.0453` over direct reliability-gated graph fusion. This is the current best evidence that the proposed mechanism graph should be connected inside the main decision framework as a learned residual verifier, not used as a post-hoc correction or a direct feature replacement.
