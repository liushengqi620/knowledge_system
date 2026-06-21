# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | hydraulic_accumulator | full | none | 3 | 0.8978 +/- 0.0103 | 0.8994 +/- 0.0047 | 0.0000 | 0.0361 | 0.0000 | 0.8702 | 0.3472 | 255.3 | 161353 |

## Top Evidence Paths

### hydraulic / hydraulic_accumulator / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| PS3_std -> TS1_min | PS3 -> TS1 | 0.2325 | 0.6250 | 0.9498 | 0.0000 | 0.8894 |
| TS1_mean -> PS2_mean | TS1 -> PS2 | 0.2301 | 0.6057 | 0.7211 | 0.0000 | 0.8124 |
| FS2_std -> PS5_std | FS2 -> PS5 | 0.2177 | 0.5376 | 0.6543 | 0.0000 | 0.6853 |
| PS5_mean -> TS2_last_minus_first | PS5 -> TS2 | 0.2169 | 0.4775 | 0.5736 | 0.0000 | 0.6853 |
| FS2_std -> FS2_max | FS2 -> FS2 | 0.2032 | 0.5801 | 0.5728 | 0.0000 | 0.5419 |

### hydraulic / hydraulic_accumulator / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| TS1_min -> FS1_max | TS1 -> FS1 | 0.4163 | 0.5639 | 0.4058 | 0.0000 | 1.0000 |
| TS3_last_minus_first -> EPS1_mean | TS3 -> EPS1 | 0.2603 | 0.5976 | 0.3968 | 0.0000 | 0.8830 |
| CE_mean -> TS1_last_minus_first | CE -> TS1 | 0.2292 | 0.6692 | 0.5021 | 0.0000 | 0.8626 |
| PS5_min -> FS1_std | PS5 -> FS1 | 0.2152 | 0.5424 | 0.4211 | 0.0000 | 1.0000 |
| PS4_std -> FS1_std | PS4 -> FS1 | 0.1911 | 0.6240 | 0.6513 | 0.0000 | 1.0000 |

### hydraulic / hydraulic_accumulator / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| TS1_max -> PS3_std | TS1 -> PS3 | 0.3492 | 0.6425 | 0.5521 | 0.0000 | 0.9137 |
| TS1_last_minus_first -> TS3_min | TS1 -> TS3 | 0.3336 | 0.4849 | 0.5598 | 0.0000 | 0.8120 |
| PS3_std -> TS1_max | PS3 -> TS1 | 0.3245 | 0.4616 | 0.4717 | 0.0000 | 0.9137 |
| SE_std -> VS1_mean | SE -> VS1 | 0.2669 | 0.6322 | 0.4986 | 0.0000 | 0.7837 |
| EPS1_mean -> FS1_max | EPS1 -> FS1 | 0.2643 | 0.5676 | 0.6823 | 0.0000 | 1.0000 |

