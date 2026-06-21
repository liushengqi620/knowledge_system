# TEP Reliable Lagged Graph Sequence Smoke Summary

## Purpose

This smoke experiment verifies the reliability-gated lagged graph path for tree-free TEP sequence heads. It is not a competitive result because it uses only 2k rows and 1 supervised epoch.

## Configuration

```text
model: TCN
rows: 2000
window_size: 16
epochs: 1
normal_pretrain_epochs: 1
normal_residual_features: enabled
graph_strength: 0.15
graph_mode: reliability-gated lagged edge messages
reliability_threshold: 0.70
max_edges: 40
prior: tep_expert_llm_graph_prior.json
```

## Edge Reliability Evidence

```text
candidate_edges: 79
matched_edges: 40
pruned_edges: 39
lag_counts: lag=1 -> 2, lag=2 -> 38
max_lag: 2
lagged_graph_messages: true
```

## Smoke Metrics

```text
macro_f1: 0.1005
target_defect_macro_f1: 0.1053
event_macro_recall: 0.1429
```

## Interpretation

The important result is not the absolute score. The implementation now supports the full experimental chain required by the theory: noisy expert/LLM mechanism edges are first scored and pruned, then admitted edges deliver delayed source-variable messages from `u(t-lag)` to `v(t)`, and the sequence head records the selected graph in reproducible diagnostics. This turns the tree-free sequence route into a testable mechanism-learning model rather than a generic temporal classifier.
