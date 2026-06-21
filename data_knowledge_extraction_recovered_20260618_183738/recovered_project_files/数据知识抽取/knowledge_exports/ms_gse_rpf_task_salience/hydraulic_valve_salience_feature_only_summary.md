# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | none | 1 | 0.7956 +/- 0.0000 | 0.7943 +/- 0.0000 | n/a | n/a | 0.0000 | 0.7798 | 284.2 | 161353 |

## Top Evidence Paths

### hydraulic / valve / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| EPS1_max -> PS1_max | EPS1 -> PS1 | 0.3343 | 0.8271 | 0.5160 | 0.0000 | 0.6991 |
| EPS1_max -> VS1_last_minus_first | EPS1 -> VS1 | 0.2960 | 0.7914 | 0.4827 | 0.0000 | 0.6991 |
| FS1_max -> FS1_last_minus_first | FS1 -> FS1 | 0.2819 | 0.6574 | 0.4802 | 0.0000 | 1.0000 |
| FS1_max -> TS3_max | FS1 -> TS3 | 0.2319 | 0.6008 | 0.4652 | 0.0000 | 1.0000 |
| EPS1_mean -> PS5_max | EPS1 -> PS5 | 0.1886 | 0.5853 | 0.5419 | 0.0000 | 0.6991 |

