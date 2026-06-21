# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Prior mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | none | 3 | 0.6834 +/- 0.0413 | 0.7029 +/- 0.0388 | 0.0000 | 0.0000 | 284.5 | 161225 |

## Top Evidence Paths

### hydraulic / valve / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| PS2_std -> FS2_max | 0.2164 | 0.5171 | 0.7470 | 0.0000 |
| FS1_std -> PS4_mean | 0.1972 | 0.6343 | 0.5736 | 0.0000 |
| PS3_std -> TS2_std | 0.1806 | 0.5721 | 0.3848 | 0.0000 |
| EPS1_mean -> TS1_last_minus_first | 0.1783 | 0.5825 | 0.4156 | 0.0000 |
| VS1_std -> TS1_max | 0.1557 | 0.6626 | 0.3933 | 0.0000 |

### hydraulic / valve / full / prior=none / seed=43

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| SE_mean -> FS1_max | 0.3398 | 0.6646 | 0.5965 | 0.0000 |
| TS1_mean -> PS4_min | 0.2470 | 0.3930 | 0.6698 | 0.0000 |
| SE_mean -> FS1_last_minus_first | 0.2053 | 0.5364 | 0.5254 | 0.0000 |
| SE_mean -> TS4_mean | 0.1780 | 0.6598 | 0.4745 | 0.0000 |
| PS2_std -> FS1_max | 0.1749 | 0.5385 | 0.4952 | 0.0000 |

### hydraulic / valve / full / prior=none / seed=44

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| VS1_last_minus_first -> PS6_max | 0.2353 | 0.4595 | 0.5992 | 0.0000 |
| FS1_max -> PS6_min | 0.2267 | 0.6813 | 0.4953 | 0.0000 |
| PS2_mean -> TS3_max | 0.2138 | 0.4804 | 0.6649 | 0.0000 |
| FS1_max -> SE_mean | 0.2078 | 0.5710 | 0.7745 | 0.0000 |
| SE_mean -> PS4_mean | 0.1770 | 0.5851 | 0.7733 | 0.0000 |

