# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-aux@0.05 | 1 | 0.6051 +/- 0.0000 | 0.6208 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.8270 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 808.7 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_07 -> xmv_10 | xmv_07 -> xmv_10 | 0.3953 | 0.7906 | 0.2970 | 0.0000 | 0.0000 | 1.0 |
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.3904 | 0.5964 | 0.2825 | 0.0000 | 0.0000 | 1.0 |
| xmeas_25 -> xmv_11 | xmeas_25 -> xmv_11 | 0.3276 | 0.6550 | 0.2391 | 0.0000 | 0.0000 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.3223 | 0.7702 | 0.3389 | 0.0000 | 0.0000 | 1.0 |
| xmv_08 -> xmv_10 | xmv_08 -> xmv_10 | 0.3068 | 0.7725 | 0.3168 | 0.0000 | 0.0000 | 1.0 |

