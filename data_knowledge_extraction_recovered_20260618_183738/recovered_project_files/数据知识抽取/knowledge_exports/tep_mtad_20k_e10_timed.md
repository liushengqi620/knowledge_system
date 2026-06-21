# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 3 | 0.6339 +/- 0.0118 | 0.6080 +/- 0.0112 | 0.7619 +/- 0.0389 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |
| residual_gated_lagged | 3 | 0.6385 +/- 0.0120 | 0.6121 +/- 0.0110 | 0.7778 +/- 0.0449 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.6272, matched_edges=n/a, pruned_edges=n/a
- residual_gated_lagged/seed=42: target-F1=0.6331, matched_edges=40, pruned_edges=39
- no_graph/seed=43: target-F1=0.6505, matched_edges=n/a, pruned_edges=n/a
- residual_gated_lagged/seed=43: target-F1=0.6551, matched_edges=40, pruned_edges=39
- no_graph/seed=44: target-F1=0.6240, matched_edges=n/a, pruned_edges=n/a
- residual_gated_lagged/seed=44: target-F1=0.6272, matched_edges=40, pruned_edges=39
