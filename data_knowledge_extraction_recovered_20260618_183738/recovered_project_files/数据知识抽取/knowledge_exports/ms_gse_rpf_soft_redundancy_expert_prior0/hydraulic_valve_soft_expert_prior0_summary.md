# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | expert@0.00 | 3 | 0.6701 +/- 0.0423 | 0.6935 +/- 0.0363 | 0.0000 | 0.0185 | 0.0000 | 0.0000 | 0.3605 | 297.1 | 161225 |

## Top Evidence Paths

### hydraulic / valve / full / prior=expert@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS5_max -> PS4_mean | PS5 -> PS4 | 0.3936 | 0.7990 | 0.5892 | 0.0000 | 0.0000 |
| TS3_std -> PS4_mean | TS3 -> PS4 | 0.3847 | 0.7673 | 0.4472 | 0.0000 | 0.0000 |
| FS1_mean -> PS6_std | FS1 -> PS6 | 0.3530 | 0.5360 | 0.4073 | 0.0000 | 0.0000 |
| PS5_max -> PS2_std | PS5 -> PS2 | 0.3250 | 0.6040 | 0.4022 | 0.0000 | 0.0000 |
| SE_mean -> PS6_std | SE -> PS6 | 0.2898 | 0.7179 | 0.5133 | 0.0000 | 0.0000 |

### hydraulic / valve / full / prior=expert@0.00 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS2_mean -> PS4_mean | FS2 -> PS4 | 0.4728 | 0.5598 | 0.5833 | 0.0000 | 0.0000 |
| CP_max -> TS1_std | CP -> TS1 | 0.3901 | 0.5249 | 0.5332 | 0.0000 | 0.0000 |
| PS2_mean -> TS1_std | PS2 -> TS1 | 0.3315 | 0.5380 | 0.6679 | 0.0000 | 0.0000 |
| VS1_std -> SE_std | VS1 -> SE | 0.3227 | 0.6689 | 0.3837 | 0.0000 | 0.0000 |
| VS1_mean -> PS1_last_minus_first | VS1 -> PS1 | 0.2794 | 0.5892 | 0.4106 | 0.0000 | 0.0000 |

### hydraulic / valve / full / prior=expert@0.00 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS6_min -> SE_mean | PS6 -> SE | 0.2626 | 0.7531 | 0.8634 | 0.0000 | 0.0000 |
| PS1_std -> FS1_max | PS1 -> FS1 | 0.2527 | 0.4047 | 0.6200 | 0.0000 | 0.0000 |
| SE_std -> FS1_max | SE -> FS1 | 0.2312 | 0.4836 | 0.8416 | 0.0000 | 0.0000 |
| PS1_mean -> PS5_max | PS1 -> PS5 | 0.2260 | 0.4692 | 0.4700 | 0.0000 | 0.0000 |
| FS1_max -> TS4_max | FS1 -> TS4 | 0.2043 | 0.5359 | 0.4601 | 0.0000 | 0.0000 |

