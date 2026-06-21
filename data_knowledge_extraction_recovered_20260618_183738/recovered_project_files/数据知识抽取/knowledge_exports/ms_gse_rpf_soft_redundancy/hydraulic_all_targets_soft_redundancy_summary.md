# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | cooler | full | none | 3 | 0.9994 +/- 0.0009 | 0.9994 +/- 0.0009 | 0.0000 | 0.0526 | 0.0000 | 0.0000 | 0.3257 | 259.8 | 161160 |
| hydraulic | hydraulic_accumulator | full | none | 3 | 0.9327 +/- 0.0078 | 0.9339 +/- 0.0052 | 0.0000 | 0.0185 | 0.0000 | 0.0000 | 0.3832 | 225.3 | 161225 |
| hydraulic | internal_pump_leakage | full | none | 3 | 0.9790 +/- 0.0118 | 0.9792 +/- 0.0116 | 0.0000 | 0.0175 | 0.0000 | 0.0000 | 0.3771 | 299.8 | 161160 |
| hydraulic | valve | full | none | 3 | 0.7098 +/- 0.0196 | 0.7102 +/- 0.0179 | 0.0000 | 0.0577 | 0.0000 | 0.0000 | 0.3671 | 284.6 | 161225 |

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

### hydraulic / hydraulic_accumulator / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| TS1_last_minus_first -> TS4_mean | TS1 -> TS4 | 0.3417 | 0.6418 | 0.4490 | 0.0000 | 0.0000 |
| TS4_last_minus_first -> EPS1_std | TS4 -> EPS1 | 0.2225 | 0.4136 | 0.5122 | 0.0000 | 0.0000 |
| FS1_last_minus_first -> PS2_max | FS1 -> PS2 | 0.1956 | 0.6116 | 0.6090 | 0.0000 | 0.0000 |
| FS1_max -> TS1_min | FS1 -> TS1 | 0.1915 | 0.6452 | 0.5788 | 0.0000 | 0.0000 |
| TS3_max -> PS2_mean | TS3 -> PS2 | 0.1882 | 0.5463 | 0.4463 | 0.0000 | 0.0000 |

### hydraulic / hydraulic_accumulator / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS4_mean -> PS2_last_minus_first | PS4 -> PS2 | 0.3524 | 0.5123 | 0.9340 | 0.0000 | 0.0000 |
| PS4_min -> TS2_std | PS4 -> TS2 | 0.1900 | 0.5219 | 0.6539 | 0.0000 | 0.0000 |
| VS1_min -> CP_mean | VS1 -> CP | 0.1753 | 0.5820 | 0.5876 | 0.0000 | 0.0000 |
| TS3_last_minus_first -> PS2_last_minus_first | TS3 -> PS2 | 0.1717 | 0.5127 | 0.7961 | 0.0000 | 0.0000 |
| FS1_last_minus_first -> PS3_std | FS1 -> PS3 | 0.1616 | 0.5400 | 0.8389 | 0.0000 | 0.0000 |

### hydraulic / hydraulic_accumulator / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| EPS1_max -> TS3_std | EPS1 -> TS3 | 0.2119 | 0.5005 | 0.9277 | 0.0000 | 0.0000 |
| PS2_std -> EPS1_max | PS2 -> EPS1 | 0.1889 | 0.4786 | 0.4740 | 0.0000 | 0.0000 |
| TS1_mean -> FS2_max | TS1 -> FS2 | 0.1759 | 0.4672 | 0.4773 | 0.0000 | 0.0000 |
| FS1_max -> VS1_max | FS1 -> VS1 | 0.1746 | 0.6596 | 0.6253 | 0.0000 | 0.0000 |
| TS1_std -> CP_last_minus_first | TS1 -> CP | 0.1640 | 0.7370 | 0.5446 | 0.0000 | 0.0000 |

### hydraulic / internal_pump_leakage / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_last_minus_first -> SE_max | FS1 -> SE | 0.2696 | 0.5592 | 0.4478 | 0.0000 | 0.0000 |
| PS6_last_minus_first -> SE_max | PS6 -> SE | 0.2350 | 0.5146 | 0.4014 | 0.0000 | 0.0000 |
| TS4_max -> VS1_max | TS4 -> VS1 | 0.2215 | 0.5304 | 0.6315 | 0.0000 | 0.0000 |
| VS1_min -> SE_max | VS1 -> SE | 0.2215 | 0.6172 | 0.5206 | 0.0000 | 0.0000 |
| PS2_max -> FS1_std | PS2 -> FS1 | 0.2099 | 0.5067 | 0.3893 | 0.0000 | 0.0000 |

### hydraulic / internal_pump_leakage / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| TS1_max -> EPS1_mean | TS1 -> EPS1 | 0.2793 | 0.4876 | 0.3845 | 0.0000 | 0.0000 |
| PS1_max -> PS2_max | PS1 -> PS2 | 0.1636 | 0.5470 | 0.5533 | 0.0000 | 0.0000 |
| SE_max -> TS4_min | SE -> TS4 | 0.1472 | 0.6031 | 0.6477 | 0.0000 | 0.0000 |
| SE_std -> TS4_min | SE -> TS4 | 0.1453 | 0.5610 | 0.3996 | 0.0000 | 0.0000 |
| VS1_std -> TS1_std | VS1 -> TS1 | 0.1446 | 0.5209 | 0.3857 | 0.0000 | 0.0000 |

### hydraulic / internal_pump_leakage / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_mean -> TS1_max | FS1 -> TS1 | 0.3061 | 0.5689 | 0.4209 | 0.0000 | 0.0000 |
| PS1_std -> TS3_mean | PS1 -> TS3 | 0.2808 | 0.5371 | 0.4327 | 0.0000 | 0.0000 |
| VS1_min -> FS1_mean | VS1 -> FS1 | 0.2675 | 0.5863 | 0.4027 | 0.0000 | 0.0000 |
| FS1_last_minus_first -> SE_mean | FS1 -> SE | 0.2654 | 0.6218 | 0.4452 | 0.0000 | 0.0000 |
| TS3_max -> SE_max | TS3 -> SE | 0.2449 | 0.5538 | 0.3861 | 0.0000 | 0.0000 |

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

