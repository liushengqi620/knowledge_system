# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | hydraulic_accumulator | full | none | 3 | 0.9327 +/- 0.0078 | 0.9339 +/- 0.0052 | 0.0000 | 0.0185 | 0.0000 | 0.0000 | 0.3832 | 225.3 | 161225 |

## Top Evidence Paths

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

