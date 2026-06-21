# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 3 | 0.2693 +/- 0.0071 | 0.2593 +/- 0.0076 | 0.3651 +/- 0.0594 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |
| all_lagged | 3 | 0.2713 +/- 0.0093 | 0.2611 +/- 0.0075 | 0.3651 +/- 0.0449 | 0.0000 +/- 0.0000 | 79.0000 | 79.0000 | 0.0000 |
| reliable_lagged | 3 | 0.2679 +/- 0.0079 | 0.2583 +/- 0.0061 | 0.3175 +/- 0.0449 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |
| residual_gated_lagged | 3 | 0.2780 +/- 0.0088 | 0.2677 +/- 0.0113 | 0.3651 +/- 0.0594 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.2776, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=42: target-F1=0.2845, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=42: target-F1=0.2791, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=42: target-F1=0.2782, matched_edges=40, pruned_edges=39
- no_graph/seed=43: target-F1=0.2699, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=43: target-F1=0.2636, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=43: target-F1=0.2617, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=43: target-F1=0.2887, matched_edges=40, pruned_edges=39
- no_graph/seed=44: target-F1=0.2604, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=44: target-F1=0.2659, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=44: target-F1=0.2629, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=44: target-F1=0.2672, matched_edges=40, pruned_edges=39
