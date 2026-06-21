# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full_admitted | none | 3 | 0.7564 +/- 0.0446 | 0.7601 +/- 0.0499 | 0.0175 | 0.0417 | 0.0000 | 0.5381 | 0.3304 | 290.1 | 161353 |

## Top Evidence Paths

### hydraulic / valve / full_admitted / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| EPS1_max -> PS1_max | EPS1 -> PS1 | 0.2746 | 0.8542 | 0.5193 | 0.0000 | 0.6991 |
| FS1_max -> FS1_last_minus_first | FS1 -> FS1 | 0.2565 | 0.7797 | 0.5706 | 0.0000 | 1.0000 |
| PS3_std -> TS4_max | PS3 -> TS4 | 0.2257 | 0.7846 | 0.5017 | 0.0000 | 0.6714 |
| PS1_mean -> PS2_mean | PS1 -> PS2 | 0.2096 | 0.5008 | 0.5901 | 0.0000 | 0.7611 |
| TS4_max -> FS2_last_minus_first | TS4 -> FS2 | 0.2035 | 0.5135 | 0.6270 | 0.0000 | 0.2454 |

### hydraulic / valve / full_admitted / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| CE_mean -> FS1_min | CE -> FS1 | 0.3037 | 0.6145 | 0.4899 | 0.0000 | 1.0000 |
| FS1_max -> TS1_max | FS1 -> TS1 | 0.1971 | 0.6579 | 0.9255 | 0.0000 | 1.0000 |
| FS1_max -> PS1_mean | FS1 -> PS1 | 0.1718 | 0.4658 | 0.7613 | 0.0000 | 1.0000 |
| FS1_max -> PS2_mean | FS1 -> PS2 | 0.1703 | 0.6800 | 0.8806 | 0.0000 | 1.0000 |
| FS1_max -> SE_max | FS1 -> SE | 0.1460 | 0.4910 | 1.0113 | 0.0000 | 1.0000 |

### hydraulic / valve / full_admitted / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_max -> PS6_min | FS1 -> PS6 | 0.4720 | 0.5366 | 0.6702 | 0.0000 | 0.0000 |
| PS6_mean -> FS1_max | PS6 -> FS1 | 0.4300 | 0.6311 | 0.7056 | 0.0000 | 0.0000 |
| FS1_max -> PS6_max | FS1 -> PS6 | 0.3192 | 0.5338 | 0.8622 | 0.0000 | 0.0000 |
| TS2_std -> PS2_mean | TS2 -> PS2 | 0.2733 | 0.6165 | 0.5963 | 0.0000 | 0.0000 |
| PS1_std -> FS1_max | PS1 -> FS1 | 0.2634 | 0.5705 | 0.6826 | 0.0000 | 0.0000 |

