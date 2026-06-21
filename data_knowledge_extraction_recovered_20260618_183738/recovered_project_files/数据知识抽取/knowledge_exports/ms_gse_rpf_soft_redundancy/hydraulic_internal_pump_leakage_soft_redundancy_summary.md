# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | internal_pump_leakage | full | none | 3 | 0.9790 +/- 0.0118 | 0.9792 +/- 0.0116 | 0.0000 | 0.0175 | 0.0000 | 0.0000 | 0.3771 | 299.8 | 161160 |

## Top Evidence Paths

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

