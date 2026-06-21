# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hydraulic | valve | full | none | 1 | 0.1562 +/- 0.0000 | 0.2200 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.0000 | 2373.0 | 14337 |

## Top Evidence Paths

### hydraulic / valve / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| TS2_mean -> TS4_last_minus_first | TS2 -> TS4 | 0.3648 | 0.4096 | 0.5418 | 0.0000 | 0.0000 |
| FS2_std -> TS3_std | FS2 -> TS3 | 0.2888 | 0.4536 | 0.5272 | 0.0000 | 0.0000 |
| TS2_mean -> PS4_mean | TS2 -> PS4 | 0.2837 | 0.3818 | 0.5353 | 0.0000 | 0.0000 |
| FS2_std -> CP_mean | FS2 -> CP | 0.2545 | 0.4011 | 0.5302 | 0.0000 | 0.0000 |
| PS1_min -> PS3_std | PS1 -> PS3 | 0.2462 | 0.4358 | 0.5488 | 0.0000 | 0.0000 |

