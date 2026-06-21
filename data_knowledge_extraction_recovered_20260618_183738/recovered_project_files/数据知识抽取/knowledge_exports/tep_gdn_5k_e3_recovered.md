# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 3 | 0.0941 +/- 0.0215 | 0.0898 +/- 0.0205 | 0.1905 +/- 0.0389 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |
| all_lagged | 3 | 0.0926 +/- 0.0192 | 0.0884 +/- 0.0184 | 0.2222 +/- 0.0449 | 0.0000 +/- 0.0000 | 79.0000 | 79.0000 | 0.0000 |
| reliable_lagged | 3 | 0.0965 +/- 0.0182 | 0.0922 +/- 0.0174 | 0.2063 +/- 0.0594 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |
| residual_gated_lagged | 3 | 0.1002 +/- 0.0202 | 0.0957 +/- 0.0193 | 0.2063 +/- 0.0594 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.0650, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=42: target-F1=0.0674, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=42: target-F1=0.0729, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=42: target-F1=0.0723, matched_edges=40, pruned_edges=39
- no_graph/seed=43: target-F1=0.1007, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=43: target-F1=0.0963, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=43: target-F1=0.0995, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=43: target-F1=0.1089, matched_edges=40, pruned_edges=39
- no_graph/seed=44: target-F1=0.1165, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=44: target-F1=0.1141, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=44: target-F1=0.1173, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=44: target-F1=0.1194, matched_edges=40, pruned_edges=39
