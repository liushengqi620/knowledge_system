# Paper Experiment Result Visualizations

This directory visualizes the consolidated paper-level experiment results under the current matched-protocol setting. The figures support the method-evidence narrative and the TEP SOTA candidate claim under matched protocol; they are not official universal SOTA evidence.

## Figure Index

| Figure | Meaning |
|---|---|
| `main_multi_benchmark_results.png` | Anchor/Main vs reliable route on TEP, SKAB, Hydraulic, and C-MAPSS; C-MAPSS uses the pseudo-terminal validation-safe RMSE rerun because lower is better. |
| `main_multi_benchmark_delta.png` | Absolute gain of the reliable route over the anchor. |
| `reliability_ablation_summary.png` | Reliability admission, prior-only, all-edge, counterfactual, pruning, and low-tail contrasts. |
| `tep_mechanism_ablation.png` | TEP mechanism ablation proving expert/LLM/reliability/residual modules are not decorative. |
| `tep_matched_baselines.png` | TEP matched strong baselines and the strict mechanism result. |
| `skab_external_baselines.png` | SKAB matched external-style reconstruction baselines versus the learned reliability route. |
| `hydraulic_four_target_results.png` | Hydraulic four-target main vs SafeLearned comparison. |
| `cmapss_rul_matched_results.png` | C-MAPSS original terminal RUL RMSE with cap/window repair, pseudo-terminal validation-safe rerun, PHM score trade-off, and non-admitted AnchorPath challenger. |

## Claim Boundary

Use these plots as manuscript visual evidence for matched-protocol experiments. TEP is the current strongest SOTA candidate, while SKAB, Hydraulic, and C-MAPSS support reliability filtering, non-degradation, and RMSE-oriented original-task RUL transfer with the C-MAPSS PHM score trade-off disclosed. Do not describe the plots as official universal SOTA until external split, preprocessing, metric, threshold, delay, and budget alignment is completed.

## Source Data

The flattened plotting table is saved as `experiment_visualization_source_data.csv`.
