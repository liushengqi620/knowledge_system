# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full_admitted | none | 3 | 0.7570 +/- 0.0614 | 0.7686 +/- 0.0626 | 0.0351 | 0.1201 | 0.0000 | 0.5384 | 294.8 | 161353 |

## Top Evidence Paths

### hydraulic / valve / full_admitted / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS2_std -> SE_std | PS2 -> SE | 0.2064 | 0.5314 | 0.9582 | 0.0000 | 0.8262 |
| PS2_std -> PS6_min | PS2 -> PS6 | 0.1436 | 0.6092 | 1.0298 | 0.0000 | 0.7611 |
| PS2_std -> PS6_max | PS2 -> PS6 | 0.1417 | 0.5876 | 1.0209 | 0.0000 | 0.7611 |
| TS1_mean -> TS4_max | TS1 -> TS4 | 0.1367 | 0.6009 | 0.5554 | 0.0000 | 0.4616 |
| TS4_max -> VS1_last_minus_first | TS4 -> VS1 | 0.1337 | 0.6549 | 0.4912 | 0.0000 | 0.4901 |

### hydraulic / valve / full_admitted / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| FS1_max -> PS6_last_minus_first | FS1 -> PS6 | 0.1737 | 0.4149 | 0.8305 | 0.0000 | 1.0000 |
| FS1_max -> PS1_last_minus_first | FS1 -> PS1 | 0.1451 | 0.4775 | 0.8165 | 0.0000 | 1.0000 |
| PS2_std -> CP_mean | PS2 -> CP | 0.1334 | 0.4221 | 1.0381 | 0.0000 | 0.8063 |
| VS1_mean -> TS2_std | VS1 -> TS2 | 0.1292 | 0.5055 | 0.5119 | 0.0000 | 0.5910 |
| TS4_max -> VS1_mean | TS4 -> VS1 | 0.1292 | 0.4144 | 0.6861 | 0.0000 | 0.5910 |

### hydraulic / valve / full_admitted / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| VS1_last_minus_first -> PS6_max | VS1 -> PS6 | 0.2353 | 0.4595 | 0.5992 | 0.0000 | 0.0000 |
| FS1_max -> PS6_min | FS1 -> PS6 | 0.2267 | 0.6813 | 0.4953 | 0.0000 | 0.0000 |
| PS2_mean -> TS3_max | PS2 -> TS3 | 0.2138 | 0.4804 | 0.6649 | 0.0000 | 0.0000 |
| FS1_max -> SE_mean | FS1 -> SE | 0.2078 | 0.5710 | 0.7745 | 0.0000 | 0.0000 |
| SE_mean -> PS4_mean | SE -> PS4 | 0.1770 | 0.5851 | 0.7733 | 0.0000 | 0.0000 |

