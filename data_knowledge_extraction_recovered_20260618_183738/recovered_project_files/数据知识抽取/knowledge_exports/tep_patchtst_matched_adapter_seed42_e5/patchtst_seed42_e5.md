# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 1 | 0.0461 +/- 0.0000 | 0.0440 +/- 0.0000 | 0.0952 +/- 0.0000 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |
| residual_gated_lagged | 1 | 0.0442 +/- 0.0000 | 0.0422 +/- 0.0000 | 0.0476 +/- 0.0000 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.0461, matched_edges=n/a, pruned_edges=n/a
- residual_gated_lagged/seed=42: target-F1=0.0442, matched_edges=40, pruned_edges=39
