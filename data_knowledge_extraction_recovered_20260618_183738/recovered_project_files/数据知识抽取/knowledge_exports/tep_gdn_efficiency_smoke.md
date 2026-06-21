# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 1 | 0.0145 +/- 0.0000 | 0.0138 +/- 0.0000 | 0.0952 +/- 0.0000 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |
| all_lagged | 1 | 0.0152 +/- 0.0000 | 0.0145 +/- 0.0000 | 0.0952 +/- 0.0000 | 0.0000 +/- 0.0000 | 79.0000 | 79.0000 | 0.0000 |
| reliable_lagged | 1 | 0.0142 +/- 0.0000 | 0.0135 +/- 0.0000 | 0.0952 +/- 0.0000 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |
| residual_gated_lagged | 1 | 0.0141 +/- 0.0000 | 0.0135 +/- 0.0000 | 0.0952 +/- 0.0000 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.0145, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=42: target-F1=0.0152, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=42: target-F1=0.0142, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=42: target-F1=0.0141, matched_edges=40, pruned_edges=39
