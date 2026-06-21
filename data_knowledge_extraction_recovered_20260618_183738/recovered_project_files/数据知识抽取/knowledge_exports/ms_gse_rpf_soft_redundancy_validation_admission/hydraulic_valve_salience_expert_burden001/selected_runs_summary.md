# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full_admitted | expert@0.00 | 1 | 0.7228 +/- 0.0000 | 0.7372 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.3732 | 301.1 | 161225 |
| hydraulic | valve | full_admitted | none | 2 | 0.7848 +/- 0.0237 | 0.7921 +/- 0.0260 | 0.0000 | 0.0000 | 0.0000 | 0.8072 | 0.2973 | 292.9 | 161353 |

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

### hydraulic / valve / full_admitted / prior=expert@0.00 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS6_min -> SE_mean | PS6 -> SE | 0.2626 | 0.7531 | 0.8634 | 0.0000 | 0.0000 |
| PS1_std -> FS1_max | PS1 -> FS1 | 0.2527 | 0.4047 | 0.6200 | 0.0000 | 0.0000 |
| SE_std -> FS1_max | SE -> FS1 | 0.2312 | 0.4836 | 0.8416 | 0.0000 | 0.0000 |
| PS1_mean -> PS5_max | PS1 -> PS5 | 0.2260 | 0.4692 | 0.4700 | 0.0000 | 0.0000 |
| FS1_max -> TS4_max | FS1 -> TS4 | 0.2043 | 0.5359 | 0.4601 | 0.0000 | 0.0000 |

