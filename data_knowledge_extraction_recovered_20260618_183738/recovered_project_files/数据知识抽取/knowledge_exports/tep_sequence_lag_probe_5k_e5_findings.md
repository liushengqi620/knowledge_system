# TEP Sequence Lag-Group Probe 5k/e5 Findings

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
probe_lags: 1,2
```

## Strict Positive-Delta Probe

```text
baseline validation Target-F1: 0.4131
lag=1 validation Target-F1: 0.4129, delta -0.0002
lag=2 validation Target-F1: 0.4109, delta -0.0022
selected_lags: []
```

Test-side Target-F1 under the same run:

```text
no_graph: 0.3499
all_lagged: 0.3510
reliable_lagged_t070_k40: 0.3450
probe_lag1: 0.3520
probe_lag2: 0.3456
```

## Tolerance-Band Probe

Using `probe_min_delta=-0.001` admits lag groups that are validation-neutral within a small tolerance:

```text
selected_lags: [1]
validation_probe_lagged Target-F1: 0.3520
matched_edges: 33/79
pruned_edges: 46
```

## Conclusion

The lag-group probe is more informative than metadata-only reliability pruning. The current best tree-free TCN graph variant is lag-1 only with a small validation tolerance, improving over no-graph and all-lagged at this 5k/e5 seed42 setting. However, the absolute score is still far below the strict ExtraTrees plus mechanism model, so this should be treated as a diagnostic step toward a stronger tree-free architecture, not as a replacement result.
