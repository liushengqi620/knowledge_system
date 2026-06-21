# TEP Low-Tail Lag Probe 10k/e10 Findings

## Protocol

```text
model: TCN
rows: 10000
seed: 42
window_size: 32
hidden_dim: 64
epochs: 10
normal_pretrain_epochs: 5
normal_residual_features: enabled
weak_class_rerank: enabled
graph_strength: 0.15
probe_lags: 1,2
probe_min_delta: -0.001
probe_low_tail_quantile: 0.5
probe_low_tail_min_delta: -0.002
```

## Result

```text
no_graph target-F1: 0.5311
all_lagged target-F1: 0.5281
reliable_lagged target-F1: 0.5168
probe_lag1 target-F1: 0.5218
probe_lag2 target-F1: 0.5225
validation_probe_lagged target-F1: 0.5225
```

## Validation Selection

```text
baseline validation Target-F1: 0.7363
lag=1 validation Target-F1: 0.7186, delta -0.0177, low-tail delta -0.0177
lag=2 validation Target-F1: 0.7398, delta +0.0035, low-tail delta +0.0035
selected_lags: [2]
```

## Conclusion

The stronger 10k/e10 TCN route improves absolute performance substantially over 5k/e5, but direct lagged graph fusion still does not improve the main sequence head. The validation selector correctly rejects lag=1 and admits lag=2, yet the selected lag=2 graph remains below the no-graph model on the test split. This is an important negative result: graph evidence should not directly overwrite or smooth sequence features. The next model upgrade should use lagged graph messages as a residual evidence channel with a learnable or validation-calibrated gate, so the main temporal representation can ignore graph evidence when it is not useful.
