# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 3 | 0.6369 +/- 0.0050 | 0.6119 +/- 0.0035 | 0.8413 +/- 0.0224 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |
| all_lagged | 3 | 0.6337 +/- 0.0031 | 0.6080 +/- 0.0024 | 0.8254 +/- 0.0224 | 0.0000 +/- 0.0000 | 79.0000 | 79.0000 | 0.0000 |
| reliable_lagged | 3 | 0.6321 +/- 0.0021 | 0.6066 +/- 0.0006 | 0.8413 +/- 0.0224 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |
| residual_gated_lagged | 3 | 0.6447 +/- 0.0038 | 0.6201 +/- 0.0025 | 0.8254 +/- 0.0224 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.6300, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=42: target-F1=0.6327, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=42: target-F1=0.6302, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=42: target-F1=0.6421, matched_edges=40, pruned_edges=39
- no_graph/seed=43: target-F1=0.6419, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=43: target-F1=0.6380, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=43: target-F1=0.6350, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=43: target-F1=0.6502, matched_edges=40, pruned_edges=39
- no_graph/seed=44: target-F1=0.6388, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=44: target-F1=0.6306, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=44: target-F1=0.6311, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=44: target-F1=0.6419, matched_edges=40, pruned_edges=39
