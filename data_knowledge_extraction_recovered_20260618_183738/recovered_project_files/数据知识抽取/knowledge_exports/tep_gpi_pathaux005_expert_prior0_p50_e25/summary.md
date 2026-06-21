# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert@0.00 | group_pair_inclusive+dedup-hard+path-aux@0.05 | 1 | 0.6108 +/- 0.0000 | 0.6278 +/- 0.0000 | n/a | n/a | 0.0109 | 0.0000 | 0.8085 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 734.8 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_07 -> xmv_11 | xmv_07 -> xmv_11 | 0.4032 | 0.7068 | 0.2769 | 0.0000 | 0.0000 | 1.0 |
| xmeas_02 -> xmv_10 | xmeas_02 -> xmv_10 | 0.3884 | 0.6933 | 0.2429 | 0.0000 | 0.0000 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.3088 | 0.7191 | 0.3557 | 0.0000 | 0.0000 | 1.0 |
| xmeas_41 -> xmv_10 | xmeas_41 -> xmv_10 | 0.3059 | 0.6891 | 0.3932 | 0.0000 | 0.0000 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.2607 | 0.6542 | 0.2925 | 0.0000 | 0.0000 | 1.0 |

