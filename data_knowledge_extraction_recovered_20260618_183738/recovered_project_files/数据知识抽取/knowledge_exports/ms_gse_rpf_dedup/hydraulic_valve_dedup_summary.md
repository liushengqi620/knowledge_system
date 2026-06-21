# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | none | 3 | 0.6569 +/- 0.0458 | 0.6701 +/- 0.0471 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 292.4 | 161225 |

## Top Evidence Paths

### hydraulic / valve / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS5_max -> PS2_std | PS5 -> PS2 | 0.3562 | 0.5962 | 0.4561 | 0.0000 | 0.0000 |
| CP_last_minus_first -> PS2_std | CP -> PS2 | 0.3119 | 0.8232 | 0.3877 | 0.0000 | 0.0000 |
| PS5_std -> FS1_max | PS5 -> FS1 | 0.3041 | 0.6862 | 0.4403 | 0.0000 | 0.0000 |
| TS4_std -> PS3_mean | TS4 -> PS3 | 0.2750 | 0.6765 | 0.3315 | 0.0000 | 0.0000 |
| TS1_max -> EPS1_std | TS1 -> EPS1 | 0.2538 | 0.6513 | 0.3635 | 0.0000 | 0.0000 |

### hydraulic / valve / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS2_mean -> TS1_std | PS2 -> TS1 | 0.5796 | 0.6316 | 0.6515 | 0.0000 | 0.0000 |
| PS6_max -> FS1_max | PS6 -> FS1 | 0.4510 | 0.7447 | 0.5247 | 0.0000 | 0.0000 |
| PS4_std -> VS1_last_minus_first | PS4 -> VS1 | 0.4377 | 0.6234 | 0.4628 | 0.0000 | 0.0000 |
| TS4_min -> TS2_mean | TS4 -> TS2 | 0.4339 | 0.7122 | 0.5070 | 0.0000 | 0.0000 |
| TS1_mean -> PS4_min | TS1 -> PS4 | 0.3619 | 0.5088 | 0.5060 | 0.0000 | 0.0000 |

### hydraulic / valve / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS6_min -> SE_mean | PS6 -> SE | 0.6917 | 0.8025 | 0.8176 | 0.0000 | 0.0000 |
| PS1_std -> SE_mean | PS1 -> SE | 0.4423 | 0.5031 | 0.3718 | 0.0000 | 0.0000 |
| TS1_std -> SE_mean | TS1 -> SE | 0.4140 | 0.7303 | 0.3833 | 0.0000 | 0.0000 |
| PS3_max -> FS1_max | PS3 -> FS1 | 0.3756 | 0.6279 | 0.5455 | 0.0000 | 0.0000 |
| FS2_min -> SE_mean | FS2 -> SE | 0.3310 | 0.7075 | 0.3700 | 0.0000 | 0.0000 |

