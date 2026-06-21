# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | none | 3 | 0.7439 +/- 0.0610 | 0.7520 +/- 0.0605 | 0.0000 | 0.0196 | 0.0000 | 0.7873 | 0.3175 | 265.1 | 161353 |

## Top Evidence Paths

### hydraulic / valve / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| EPS1_max -> PS1_max | EPS1 -> PS1 | 0.2746 | 0.8542 | 0.5193 | 0.0000 | 0.6991 |
| FS1_max -> FS1_last_minus_first | FS1 -> FS1 | 0.2565 | 0.7797 | 0.5706 | 0.0000 | 1.0000 |
| PS3_std -> TS4_max | PS3 -> TS4 | 0.2257 | 0.7846 | 0.5017 | 0.0000 | 0.6714 |
| PS1_mean -> PS2_mean | PS1 -> PS2 | 0.2096 | 0.5008 | 0.5901 | 0.0000 | 0.7611 |
| TS4_max -> FS2_last_minus_first | TS4 -> FS2 | 0.2035 | 0.5135 | 0.6270 | 0.0000 | 0.2454 |

### hydraulic / valve / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| CE_mean -> FS1_min | CE -> FS1 | 0.3037 | 0.6145 | 0.4899 | 0.0000 | 1.0000 |
| FS1_max -> TS1_max | FS1 -> TS1 | 0.1971 | 0.6579 | 0.9255 | 0.0000 | 1.0000 |
| FS1_max -> PS1_mean | FS1 -> PS1 | 0.1718 | 0.4658 | 0.7613 | 0.0000 | 1.0000 |
| FS1_max -> PS2_mean | FS1 -> PS2 | 0.1703 | 0.6800 | 0.8806 | 0.0000 | 1.0000 |
| FS1_max -> SE_max | FS1 -> SE | 0.1460 | 0.4910 | 1.0113 | 0.0000 | 1.0000 |

### hydraulic / valve / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_last_minus_first -> FS1_max | FS1 -> FS1 | 0.4028 | 0.6764 | 0.6902 | 0.0000 | 1.0000 |
| FS1_last_minus_first -> FS1_std | FS1 -> FS1 | 0.3710 | 0.5611 | 0.5328 | 0.0000 | 1.0000 |
| EPS1_std -> FS1_max | EPS1 -> FS1 | 0.3286 | 0.5794 | 0.5548 | 0.0000 | 1.0000 |
| TS3_std -> FS1_max | TS3 -> FS1 | 0.2816 | 0.6175 | 0.8170 | 0.0000 | 1.0000 |
| PS3_std -> FS1_max | PS3 -> FS1 | 0.2792 | 0.5996 | 0.6481 | 0.0000 | 1.0000 |

