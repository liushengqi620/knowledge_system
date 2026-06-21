# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | expert@0.00 | 3 | 0.6375 +/- 0.0495 | 0.6550 +/- 0.0358 | 0.0000 | 0.0370 | 0.0093 | 0.0000 | 0.3769 | 302.6 | 161225 |

## Top Evidence Paths

### hydraulic / valve / full / prior=expert@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS5_max -> PS4_mean | PS5 -> PS4 | 0.3261 | 0.8033 | 0.6674 | 0.0000 | 0.0000 |
| FS2_max -> TS4_min | FS2 -> TS4 | 0.2412 | 0.7384 | 0.3895 | 0.0000 | 0.0000 |
| PS1_std -> FS2_max | PS1 -> FS2 | 0.2271 | 0.6580 | 0.7131 | 0.0000 | 0.0000 |
| FS1_last_minus_first -> TS3_mean | FS1 -> TS3 | 0.2255 | 0.6101 | 0.3466 | 0.0000 | 0.0000 |
| FS1_mean -> CE_std | FS1 -> CE | 0.2012 | 0.6240 | 0.4038 | 0.0000 | 0.0000 |

### hydraulic / valve / full / prior=expert@0.00 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS2_mean -> VS1_last_minus_first | PS2 -> VS1 | 0.4247 | 0.6446 | 0.5845 | 0.2100 | 0.0000 |
| PS2_mean -> TS1_std | PS2 -> TS1 | 0.3560 | 0.5827 | 0.6718 | 0.0000 | 0.0000 |
| FS2_mean -> PS4_mean | FS2 -> PS4 | 0.3152 | 0.5944 | 0.4996 | 0.0000 | 0.0000 |
| TS1_mean -> PS4_min | TS1 -> PS4 | 0.2891 | 0.4863 | 0.5727 | 0.0000 | 0.0000 |
| EPS1_std -> PS1_max | EPS1 -> PS1 | 0.2623 | 0.5192 | 0.4064 | 0.0000 | 0.0000 |

### hydraulic / valve / full / prior=expert@0.00 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| TS2_std -> PS2_mean | TS2 -> PS2 | 0.3135 | 0.5299 | 0.6414 | 0.0000 | 0.0000 |
| SE_std -> FS1_max | SE -> FS1 | 0.2734 | 0.5153 | 0.8617 | 0.0000 | 0.0000 |
| FS1_max -> PS6_min | FS1 -> PS6 | 0.2557 | 0.5638 | 0.7476 | 0.0000 | 0.0000 |
| FS1_max -> PS4_mean | FS1 -> PS4 | 0.2412 | 0.6567 | 0.8476 | 0.0000 | 0.0000 |
| PS1_std -> FS1_max | PS1 -> FS1 | 0.2339 | 0.5222 | 0.6906 | 0.0000 | 0.0000 |

