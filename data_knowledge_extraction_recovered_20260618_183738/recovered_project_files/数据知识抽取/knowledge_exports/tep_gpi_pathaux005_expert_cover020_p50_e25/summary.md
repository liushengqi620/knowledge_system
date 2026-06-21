# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert@0.00 | group_pair_inclusive+dedup-hard+prior-cover@0.20+path-aux@0.05 | 1 | 0.5981 +/- 0.0000 | 0.6116 +/- 0.0000 | n/a | n/a | 0.1877 | 0.0000 | 0.6870 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 755.7 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_21 -> xmv_10 | xmeas_21 -> xmv_10 | 0.3438 | 0.6431 | 0.3933 | 0.0000 | 0.0000 | 1.0 |
| xmeas_33 -> xmv_11 | xmeas_33 -> xmv_11 | 0.3387 | 0.6043 | 0.2868 | 0.0000 | 0.0000 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.2276 | 0.5632 | 0.4260 | 0.0000 | 0.0000 | 1.0 |
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.2097 | 0.4247 | 0.3710 | 0.0000 | 0.0000 | 1.0 |
| xmeas_02 -> xmv_11 | xmeas_02 -> xmv_11 | 0.2074 | 0.4972 | 0.2988 | 0.0000 | 0.0000 | 1.0 |

