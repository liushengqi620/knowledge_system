# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 3 | 0.3293 +/- 0.0205 | 0.3143 +/- 0.0195 | 0.3175 +/- 0.0224 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |
| residual_gated_lagged | 3 | 0.4077 +/- 0.0240 | 0.3892 +/- 0.0229 | 0.3968 +/- 0.0449 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.3438, matched_edges=n/a, pruned_edges=n/a
- residual_gated_lagged/seed=42: target-F1=0.4137, matched_edges=40, pruned_edges=39
- no_graph/seed=43: target-F1=0.3437, matched_edges=n/a, pruned_edges=n/a
- residual_gated_lagged/seed=43: target-F1=0.4337, matched_edges=40, pruned_edges=39
- no_graph/seed=44: target-F1=0.3004, matched_edges=n/a, pruned_edges=n/a
- residual_gated_lagged/seed=44: target-F1=0.3758, matched_edges=40, pruned_edges=39
