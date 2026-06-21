# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Prior mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | none | 3 | 0.7088 +/- 0.0747 | 0.7259 +/- 0.0700 | 0.0000 | 0.0000 | 277.9 | 161225 |

## Top Evidence Paths

### hydraulic / valve / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| PS2_mean -> EPS1_last_minus_first | 0.2069 | 0.5791 | 0.8393 | 0.0000 |
| PS2_std -> FS2_std | 0.1919 | 0.7036 | 0.5817 | 0.0000 |
| VS1_mean -> PS6_min | 0.1841 | 0.5493 | 0.5568 | 0.0000 |
| PS2_std -> PS2_mean | 0.1798 | 0.5307 | 0.9735 | 0.0000 |
| PS2_std -> CE_min | 0.1588 | 0.5945 | 0.8783 | 0.0000 |

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

