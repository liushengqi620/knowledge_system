# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert@0.00 | group_pair_inclusive+dedup-hard+prior-cover@0.05+path-aux@0.05 | 1 | 0.6038 +/- 0.0000 | 0.6190 +/- 0.0000 | n/a | n/a | 0.0454 | 0.0000 | 0.7619 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 746.3 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_13 -> xmeas_16 | xmeas_13 -> xmeas_16 | 0.3415 | 0.3256 | 0.2512 | 0.0000 | 0.0000 | 1.0 |
| xmeas_15 -> xmv_10 | xmeas_15 -> xmv_10 | 0.3370 | 0.6274 | 0.3130 | 0.0000 | 0.0000 | 1.0 |
| xmeas_40 -> xmv_07 | xmeas_40 -> xmv_07 | 0.3263 | 0.4914 | 0.3233 | 0.0000 | 0.0000 | 1.0 |
| xmeas_41 -> xmv_10 | xmeas_41 -> xmv_10 | 0.2931 | 0.6239 | 0.4021 | 0.0000 | 0.0000 | 1.0 |
| xmeas_25 -> xmv_11 | xmeas_25 -> xmv_11 | 0.2924 | 0.6578 | 0.2621 | 0.0000 | 0.0000 | 1.0 |

