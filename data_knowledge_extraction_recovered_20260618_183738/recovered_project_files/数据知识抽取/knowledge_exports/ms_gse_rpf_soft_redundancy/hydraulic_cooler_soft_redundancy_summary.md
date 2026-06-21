# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | cooler | full | none | 3 | 0.9994 +/- 0.0009 | 0.9994 +/- 0.0009 | 0.0000 | 0.0526 | 0.0000 | 0.0000 | 0.3257 | 259.8 | 161160 |

## Top Evidence Paths

### hydraulic / cooler / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| EPS1_max -> FS2_min | EPS1 -> FS2 | 0.1537 | 0.6647 | 0.3869 | 0.0000 | 0.0000 |
| CP_max -> TS4_std | CP -> TS4 | 0.1333 | 0.5502 | 0.5199 | 0.0000 | 0.0000 |
| EPS1_max -> PS3_max | EPS1 -> PS3 | 0.1322 | 0.7161 | 0.4371 | 0.0000 | 0.0000 |
| CP_max -> PS5_max | CP -> PS5 | 0.1248 | 0.5782 | 0.5335 | 0.0000 | 0.0000 |
| CP_max -> PS6_last_minus_first | CP -> PS6 | 0.1187 | 0.6163 | 0.4357 | 0.0000 | 0.0000 |

### hydraulic / cooler / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| CP_min -> PS5_min | CP -> PS5 | 0.2862 | 0.6327 | 0.3437 | 0.0000 | 0.0000 |
| CP_min -> EPS1_min | CP -> EPS1 | 0.2601 | 0.6291 | 0.3431 | 0.0000 | 0.0000 |
| CP_max -> FS1_mean | CP -> FS1 | 0.1784 | 0.6649 | 0.3638 | 0.0000 | 0.0000 |
| PS4_mean -> FS1_max | PS4 -> FS1 | 0.1717 | 0.6229 | 0.3798 | 0.0000 | 0.0000 |
| PS4_mean -> CP_max | PS4 -> CP | 0.1403 | 0.5693 | 0.4084 | 0.0000 | 0.0000 |

### hydraulic / cooler / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| CE_max -> TS1_std | CE -> TS1 | 0.2667 | 0.6846 | 0.4797 | 0.0000 | 0.0000 |
| CE_min -> PS2_last_minus_first | CE -> PS2 | 0.2433 | 0.5752 | 0.5094 | 0.0000 | 0.0000 |
| CP_max -> PS4_min | CP -> PS4 | 0.2400 | 0.6878 | 0.3644 | 0.0000 | 0.0000 |
| TS2_std -> TS3_std | TS2 -> TS3 | 0.2364 | 0.5078 | 0.3505 | 0.0000 | 0.0000 |
| CE_min -> TS3_std | CE -> TS3 | 0.2277 | 0.4709 | 0.3717 | 0.0000 | 0.0000 |

