# TEP Lagged Graph Sequence Smoke Summary

## Purpose

This smoke experiment verifies that the tree-free TEP sequence-head path can consume lagged mechanism graph evidence. It is not a main performance result because it uses only 2k rows and 1 supervised epoch.

## Configuration

```text
model: TCN
rows: 2000
window_size: 16
epochs: 1
normal_pretrain_epochs: 1
normal_residual_features: enabled
graph_strength: 0.15
graph_mode: lagged edge messages
prior: tep_expert_llm_graph_prior.json
```

## Evidence

```text
matched_edges: 79
lag_counts: lag=1 -> 33, lag=2 -> 46
max_lag: 2
lagged_graph_messages: true
normal_residual_features: true
augmented_features: 52 -> 104
```

## Smoke Metrics

```text
macro_f1: 0.0987
target_defect_macro_f1: 0.1034
event_macro_recall: 0.1429
```

## Interpretation

The result should be read as a mechanism-path verification, not as a competitive model. The important advance is that the graph prior is no longer limited to same-step neighbor smoothing: each edge can now deliver a source-variable message from `t - lag` to the target variable at `t`. This is the required implementation base for the next mechanism-aligned tree-free experiments with longer training, validation-based reliability gating, and weak-class correction.
