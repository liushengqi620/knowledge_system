# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 3 | 0.0592 +/- 0.0145 | 0.0565 +/- 0.0138 | 0.1111 +/- 0.0224 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.0623, matched_edges=n/a, pruned_edges=n/a
- no_graph/seed=43: target-F1=0.0401, matched_edges=n/a, pruned_edges=n/a
- no_graph/seed=44: target-F1=0.0751, matched_edges=n/a, pruned_edges=n/a
