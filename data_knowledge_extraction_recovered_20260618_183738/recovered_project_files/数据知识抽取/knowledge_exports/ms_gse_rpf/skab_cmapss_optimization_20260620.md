# SKAB / C-MAPSS Optimization Record - 2026-06-20

## Current Main Results

| Dataset | Current main setting | Seeds | Macro-F1 mean/std | Balanced Acc mean/std | Run dir |
|---|---|---:|---:|---:|---|
| SKAB | full + expert prior + prototype posterior fusion | 42,43,44 | 0.8419 / 0.0183 | 0.8377 / 0.0205 | `C:\kg_runs\skab_full_expert_proto_probe` |
| C-MAPSS | full + group_pair_inclusive hard coverage + prototype posterior fusion | 42,43,44 | 0.7104 / 0.0058 | 0.7049 / 0.0049 | `C:\kg_runs\cmapss_gpi50_proto_probe` |
| C-MAPSS | full + group_pair_inclusive hard coverage + ordinal boundary BCE + prototype posterior fusion | 42,43,44 | 0.7112 / 0.0039 | 0.7062 / 0.0043 | `C:\kg_runs\cmapss_ordinal_boundary_w0005_probe` |

## Implemented Edge-Initialization Upgrade

The experiment script now supports a source-aware three-family edge initialization path:

- Expert and LLM knowledge graph edges are separated during `load_knowledge_graph_prior`.
- `tri_source_calibrated` combines data edges and external edges with train-only data support.
- `algorithmic-edge-prior-candidate-only` keeps data-derived edges as path candidates instead of forcing them into the main graph prior.
- Edge-family routing can now receive data/expert/LLM family matrices after data calibration.

This keeps the method aligned with the paper story: data edges, expert evidence, and LLM evidence are separate candidate sources, then admitted by data support and downstream path reliability.

## Edge Probes

| Dataset | Probe | Seed(s) | Macro-F1 | Conclusion |
|---|---|---:|---:|---|
| SKAB | tri-source + edge-family router | 42 | 0.6865 | Too strong; noisy algorithmic edges dominate RPF. Do not use as main. |
| SKAB | algorithmic candidate-only + candidate admission | 42 | 0.8497 | Much safer than strong router, but still below expert+prototype seed42 0.8667. Use as ablation. |
| C-MAPSS | data edge-family router | 42 | 0.7145 | Slightly below current seed42 0.7158. |
| C-MAPSS | algorithmic candidate-only + candidate admission | 42 | 0.7150 | Close to current seed42, but no clear gain. |

## Additional Probes

| Dataset | Probe | Seeds | Macro-F1 mean/std | Conclusion |
|---|---|---:|---:|---|
| SKAB | no forecast auxiliary loss | 42,43,44 | 0.8142 / 0.0284 | Worse; keep `forecast_weight=0.05`. |
| C-MAPSS | health auxiliary + temporal mixer | 42,43,44 | 0.7094 / 0.0134 | Seed42 improves to 0.7282 but unstable across seeds. Not main. |
| C-MAPSS | health auxiliary only | 42,43,44 | 0.7087 / 0.0035 | Stable but below current main. |
| C-MAPSS | window size 96 | 42,43,44 | 0.7067 / 0.0078 | Longer window is not robust under current model. |
| SKAB | one-class normality posterior after prototype fusion | 42,43,44 | 0.8354 / 0.0196 | Does not stabilize seed44; below current main. Keep as anomaly-specific ablation. |
| C-MAPSS | ordinal expected-stage threshold posterior | 42,43,44 | 0.7078 / 0.0077 | Validation admits seed44 but hurts test; indicates boundary calibration overfit. Not main. |
| C-MAPSS | training-time ordinal boundary BCE, weight 0.030 | 42,43,44 | 0.7057 / 0.0173 | Strong seed42 gain but unstable. |
| C-MAPSS | training-time ordinal boundary BCE, weight 0.010 | 42,43,44 | 0.7123 / 0.0120 | Best mean, but high variance; keep as aggressive variant. |
| C-MAPSS | training-time ordinal boundary BCE, weight 0.005 | 42,43,44 | 0.7112 / 0.0039 | Small but stable improvement over current main; candidate main setting. |

## Decision

For the next main table, keep:

- SKAB: `C:\kg_runs\skab_full_expert_proto_probe`
- C-MAPSS conservative: `C:\kg_runs\cmapss_ordinal_boundary_w0005_probe`
- C-MAPSS aggressive: `C:\kg_runs\cmapss_ordinal_boundary_w001_probe`

Do not claim external SOTA yet. These are the best strict-protocol internal results after the current round. The new three-source edge initialization should enter the paper as an auditable candidate-edge mechanism and ablation, not as the default setting for SKAB/C-MAPSS unless later validation shows stable gains.

## Next Work

1. Build benchmark-matched external comparison tables for SKAB and C-MAPSS.
2. For SKAB, focus on stabilizing seed43/44 rather than adding more edges.
3. For C-MAPSS, use the conservative training-time ordinal boundary BCE setting for the next main table, and report the aggressive setting separately if variance is acceptable.
4. Keep LLM/expert edges weak and data-certified; never directly inject raw external edges as high-strength graph priors.
