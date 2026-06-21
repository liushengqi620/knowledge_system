# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | none | 3 | 0.7098 +/- 0.0196 | 0.7102 +/- 0.0179 | 0.0000 | 0.0577 | 0.0000 | 0.0000 | 0.3671 | 284.6 | 161225 |

## Top Evidence Paths

### hydraulic / valve / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_mean -> PS3_mean | FS1 -> PS3 | 0.2786 | 0.6644 | 0.3954 | 0.0000 | 0.0000 |
| PS2_last_minus_first -> SE_std | PS2 -> SE | 0.2361 | 0.6375 | 0.4163 | 0.0000 | 0.0000 |
| FS1_mean -> CE_max | FS1 -> CE | 0.2292 | 0.6047 | 0.4712 | 0.0000 | 0.0000 |
| PS5_max -> PS4_mean | PS5 -> PS4 | 0.2198 | 0.7083 | 0.5564 | 0.0000 | 0.0000 |
| SE_mean -> PS6_std | SE -> PS6 | 0.2039 | 0.6454 | 0.5970 | 0.0000 | 0.0000 |

### hydraulic / valve / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS2_mean -> PS4_mean | FS2 -> PS4 | 0.3232 | 0.5104 | 0.5798 | 0.0000 | 0.0000 |
| TS1_mean -> PS4_min | TS1 -> PS4 | 0.3070 | 0.5262 | 0.6333 | 0.0000 | 0.0000 |
| PS2_mean -> TS1_std | PS2 -> TS1 | 0.2662 | 0.4975 | 0.7237 | 0.0000 | 0.0000 |
| PS2_mean -> PS4_max | PS2 -> PS4 | 0.2592 | 0.5003 | 0.5178 | 0.0000 | 0.0000 |
| CE_min -> FS1_std | CE -> FS1 | 0.2159 | 0.4808 | 0.4315 | 0.0000 | 0.0000 |

### hydraulic / valve / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_max -> PS6_min | FS1 -> PS6 | 0.4720 | 0.5366 | 0.6702 | 0.0000 | 0.0000 |
| PS6_mean -> FS1_max | PS6 -> FS1 | 0.4300 | 0.6311 | 0.7056 | 0.0000 | 0.0000 |
| FS1_max -> PS6_max | FS1 -> PS6 | 0.3192 | 0.5338 | 0.8622 | 0.0000 | 0.0000 |
| TS2_std -> PS2_mean | TS2 -> PS2 | 0.2733 | 0.6165 | 0.5963 | 0.0000 | 0.0000 |
| PS1_std -> FS1_max | PS1 -> FS1 | 0.2634 | 0.5705 | 0.6826 | 0.0000 | 0.0000 |

