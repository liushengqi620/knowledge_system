# TEP Low-Tail Lag Probe Smoke Findings

## Protocol

```text
model: TCN
rows: 2000
seeds: 42,43
window_size: 16
hidden_dim: 32
epochs: 1
normal_pretrain_epochs: 1
graph_strength: 0.15
probe_lags: 1,2
probe_min_delta: -0.001
probe_low_tail_quantile: 0.5
probe_low_tail_min_delta: -0.002
```

## Result

```text
no_graph target-F1: 0.0748 +/- 0.0300
all_lagged target-F1: 0.0786 +/- 0.0248
reliable_lagged target-F1: 0.0750 +/- 0.0303
probe_lag1 target-F1: 0.0789 +/- 0.0212
probe_lag2 target-F1: 0.0744 +/- 0.0297
validation_probe_lagged target-F1: 0.0786 +/- 0.0248
```

## Low-Tail Selection

```text
baseline validation Target-F1: 0.0768
lag=1 validation Target-F1: 0.0919, mean delta 0.0151, low-tail delta 0.0000
lag=2 validation Target-F1: 0.0821, mean delta 0.0052, low-tail delta 0.0000
selected_lags: [1, 2]
```

## Interpretation

The low-tail selector is now operational across seeds. At this tiny training budget it selects both lag groups because neither group violates the configured low-tail tolerance. The resulting `validation_probe_lagged` equals the all-lagged model, which is expected when all lags are admitted. The useful contribution is methodological: the runner now records both mean validation benefit and low-tail validation benefit, allowing later 10k-20k/three-seed experiments to reject lag groups that have good average gain but unstable seed-level behavior.
