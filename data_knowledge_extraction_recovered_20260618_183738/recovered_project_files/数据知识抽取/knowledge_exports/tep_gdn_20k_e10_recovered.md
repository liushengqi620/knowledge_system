# TEP Sequence Graph Ablation Summary

| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_graph | 3 | 0.3922 +/- 0.0510 | 0.3820 +/- 0.0432 | 0.4603 +/- 0.0224 | 0.0000 +/- 0.0000 | n/a | n/a | n/a |
| all_lagged | 3 | 0.4051 +/- 0.0518 | 0.3954 +/- 0.0456 | 0.4603 +/- 0.0809 | 0.0000 +/- 0.0000 | 79.0000 | 79.0000 | 0.0000 |
| reliable_lagged | 3 | 0.4149 +/- 0.0502 | 0.4037 +/- 0.0434 | 0.4921 +/- 0.0224 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |
| residual_gated_lagged | 3 | 0.5179 +/- 0.0372 | 0.4993 +/- 0.0328 | 0.5238 +/- 0.0389 | 0.0000 +/- 0.0000 | 79.0000 | 40.0000 | 39.0000 |

## Interpretation

This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; competitive claims require longer training and multiple seeds.

## Runs

- no_graph/seed=42: target-F1=0.4340, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=42: target-F1=0.4636, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=42: target-F1=0.4728, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=42: target-F1=0.5539, matched_edges=40, pruned_edges=39
- no_graph/seed=43: target-F1=0.4223, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=43: target-F1=0.4141, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=43: target-F1=0.4214, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=43: target-F1=0.5332, matched_edges=40, pruned_edges=39
- no_graph/seed=44: target-F1=0.3204, matched_edges=n/a, pruned_edges=n/a
- all_lagged/seed=44: target-F1=0.3377, matched_edges=79, pruned_edges=0
- reliable_lagged/seed=44: target-F1=0.3504, matched_edges=40, pruned_edges=39
- residual_gated_lagged/seed=44: target-F1=0.4667, matched_edges=40, pruned_edges=39
