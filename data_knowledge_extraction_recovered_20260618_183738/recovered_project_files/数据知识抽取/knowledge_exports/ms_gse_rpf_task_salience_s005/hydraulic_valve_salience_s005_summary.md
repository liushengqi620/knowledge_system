# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | none | 3 | 0.7360 +/- 0.0880 | 0.7433 +/- 0.0941 | 0.0000 | 0.0809 | 0.0000 | 0.7658 | 295.7 | 161353 |

## Top Evidence Paths

### hydraulic / valve / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS2_std -> SE_std | PS2 -> SE | 0.2064 | 0.5314 | 0.9582 | 0.0000 | 0.8262 |
| PS2_std -> PS6_min | PS2 -> PS6 | 0.1436 | 0.6092 | 1.0298 | 0.0000 | 0.7611 |
| PS2_std -> PS6_max | PS2 -> PS6 | 0.1417 | 0.5876 | 1.0209 | 0.0000 | 0.7611 |
| TS1_mean -> TS4_max | TS1 -> TS4 | 0.1367 | 0.6009 | 0.5554 | 0.0000 | 0.4616 |
| TS4_max -> VS1_last_minus_first | TS4 -> VS1 | 0.1337 | 0.6549 | 0.4912 | 0.0000 | 0.4901 |

### hydraulic / valve / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_max -> PS6_last_minus_first | FS1 -> PS6 | 0.1737 | 0.4149 | 0.8305 | 0.0000 | 1.0000 |
| FS1_max -> PS1_last_minus_first | FS1 -> PS1 | 0.1451 | 0.4775 | 0.8165 | 0.0000 | 1.0000 |
| PS2_std -> CP_mean | PS2 -> CP | 0.1334 | 0.4221 | 1.0381 | 0.0000 | 0.8063 |
| VS1_mean -> TS2_std | VS1 -> TS2 | 0.1292 | 0.5055 | 0.5119 | 0.0000 | 0.5910 |
| TS4_max -> VS1_mean | TS4 -> VS1 | 0.1292 | 0.4144 | 0.6861 | 0.0000 | 0.5910 |

### hydraulic / valve / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_max -> TS2_last_minus_first | FS1 -> TS2 | 0.4017 | 0.7712 | 0.5602 | 0.0000 | 1.0000 |
| PS3_std -> FS1_max | PS3 -> FS1 | 0.3301 | 0.7001 | 0.6947 | 0.0000 | 1.0000 |
| FS1_max -> VS1_mean | FS1 -> VS1 | 0.3159 | 0.7927 | 0.6103 | 0.0000 | 1.0000 |
| FS1_last_minus_first -> FS1_max | FS1 -> FS1 | 0.3058 | 0.7388 | 0.6400 | 0.0000 | 1.0000 |
| FS1_mean -> FS1_max | FS1 -> FS1 | 0.3008 | 0.7621 | 0.5098 | 0.0000 | 1.0000 |

