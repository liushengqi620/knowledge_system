# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert@0.05 | group_pair_inclusive+dedup-hard+path-aux@0.05 | 1 | 0.6065 +/- 0.0000 | 0.6211 +/- 0.0000 | n/a | n/a | 0.0108 | 0.0000 | 0.7814 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 652.7 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert@0.05 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.3421 | 0.6969 | 0.3411 | 0.0000 | 0.0000 | 1.0 |
| xmv_08 -> xmv_10 | xmv_08 -> xmv_10 | 0.3362 | 0.7200 | 0.3033 | 0.0000 | 0.0000 | 1.0 |
| xmeas_15 -> xmv_10 | xmeas_15 -> xmv_10 | 0.3348 | 0.6137 | 0.2915 | 0.0000 | 0.0000 | 1.0 |
| xmeas_41 -> xmv_10 | xmeas_41 -> xmv_10 | 0.2959 | 0.6243 | 0.4053 | 0.0000 | 0.0000 | 1.0 |
| xmv_07 -> xmv_10 | xmv_07 -> xmv_10 | 0.2921 | 0.6494 | 0.2868 | 0.0000 | 0.0000 | 1.0 |

