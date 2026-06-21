# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-aux@0.05+coarse@0.10 | 1 | 0.6049 +/- 0.0000 | 0.6222 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.7783 | 0.0000 | 0.05 | 0.10 | 0.00 | 0.0000 | on | 812.9 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.2782 | 0.6860 | 0.3532 | 0.0000 | 0.0000 | 1.0 |
| xmeas_15 -> xmv_10 | xmeas_15 -> xmv_10 | 0.2628 | 0.7089 | 0.3460 | 0.0000 | 0.0000 | 1.0 |
| xmv_08 -> xmv_10 | xmv_08 -> xmv_10 | 0.2605 | 0.7429 | 0.3591 | 0.0000 | 0.0000 | 1.0 |
| xmeas_24 -> xmv_10 | xmeas_24 -> xmv_10 | 0.2571 | 0.7041 | 0.3824 | 0.0000 | 0.0000 | 1.0 |
| xmv_07 -> xmv_10 | xmv_07 -> xmv_10 | 0.2319 | 0.7100 | 0.3097 | 0.0000 | 0.0000 | 1.0 |

