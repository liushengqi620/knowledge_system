# TEP Matched Baseline Evidence

## Reference

- StrictMechanism: Target-F1 0.9549 +/- 0.0023; source `manual-record`.

## Matched TEP Protocol Baselines

| Method | Target-F1 | Delta vs Strict | Delta vs Family NoGraph | Sample Macro-F1 | Event Macro-Recall | Path Hit | Source |
|---|---:|---:|---:|---:|---:|---:|---|
| TCN20k-NoGraph | 0.5754 +/- 0.0141 | -0.3795 | +0.0000 | 0.5564 +/- 0.0149 | 0.6667 +/- 0.0000 | 0.0000 +/- 0.0000 | `manual-record` |
| TCN20k-ResidualGatedLagged | 0.6034 +/- 0.0096 | -0.3515 | +0.0280 | 0.5846 +/- 0.0104 | 0.6667 +/- 0.0389 | 0.0000 +/- 0.0000 | `manual-record` |
| GRU20k-NoGraph | 0.6150 +/- 0.0030 | -0.3399 | +0.0000 | n/a | n/a | n/a | `manual-record` |
| GRU20k-ResidualGatedLagged | 0.6217 +/- 0.0073 | -0.3332 | +0.0067 | n/a | n/a | n/a | `manual-record` |
| FT20k-NoGraph | 0.4644 +/- 0.0110 | -0.4905 | +0.0000 | n/a | n/a | n/a | `manual-record` |
| FT20k-ResidualGatedLagged | 0.5136 +/- 0.0218 | -0.4413 | +0.0492 | n/a | n/a | n/a | `manual-record` |
| GDN20k-NoGraph | 0.3922 +/- 0.0510 | -0.5627 | +0.0000 | 0.3820 +/- 0.0432 | 0.4603 +/- 0.0224 | 0.0000 +/- 0.0000 | `tep_gdn_20k_e10_recovered.json::no_graph` |
| GDN20k-ResidualGatedLagged | 0.5179 +/- 0.0372 | -0.4370 | +0.1257 | 0.4993 +/- 0.0328 | 0.5238 +/- 0.0389 | 0.0000 +/- 0.0000 | `tep_gdn_20k_e10_recovered.json::residual_gated_lagged` |
| MTADGAT20k-NoGraph | 0.6369 +/- 0.0050 | -0.3180 | +0.0000 | 0.6119 +/- 0.0035 | 0.8413 +/- 0.0224 | 0.0000 +/- 0.0000 | `tep_mtad_20k_e10_recovered.json::no_graph` |
| MTADGAT20k-ResidualGatedLagged | 0.6447 +/- 0.0038 | -0.3102 | +0.0078 | 0.6201 +/- 0.0025 | 0.8254 +/- 0.0224 | 0.0000 +/- 0.0000 | `tep_mtad_20k_e10_recovered.json::residual_gated_lagged` |

## Interpretation

This report separates matched TEP protocol evidence into two questions. First, the strict mechanism model remains the main high-performing classifier. Second, within the tree-free sequence family, lagged residual-gated graph evidence should improve over the no-graph temporal baseline before it is treated as a meaningful replacement direction. The current table is therefore a baseline and mechanism-ablation audit, not a claim that tree-free sequence heads already beat KIEP-GL.
