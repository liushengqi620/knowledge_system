# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-evidence-static_lag-lag1@0.25@8+path-aux@0.05+router@0.05 | 3 | 0.6051 +/- 0.0111 | 0.6118 +/- 0.0140 | 0.0000 | 0.0000 | 0.0000 | 0.2175 | 0.7753 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7220.4 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.3129 | 0.8736 | 0.3100 | 0.0000 | 0.1814 | 1.0 |
| xmv_10 -> xmeas_41 | xmv_10 -> xmeas_41 | 0.2992 | 0.8074 | 0.3218 | 0.0000 | 0.1777 | 1.0 |
| xmeas_40 -> xmv_05 | xmeas_40 -> xmv_05 | 0.2924 | 0.8378 | 0.2413 | 0.0000 | 0.7204 | 1.0 |
| xmv_11 -> xmeas_03 | xmv_11 -> xmeas_03 | 0.2817 | 0.8964 | 0.2446 | 0.0000 | 0.5581 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.2524 | 0.6771 | 0.2727 | 0.0000 | 0.6725 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.7700 | 0.8467 | 0.2364 | 0.0000 | 0.4807 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.6636 | 0.8242 | 0.3581 | 0.0000 | 0.3695 | 1.0 |
| xmv_02 -> xmv_04 | xmv_02 -> xmv_04 | 0.5697 | 0.7882 | 0.3503 | 0.0000 | 0.3300 | 1.0 |
| xmeas_03 -> xmv_04 | xmeas_03 -> xmv_04 | 0.5326 | 0.8102 | 0.2779 | 0.0000 | 0.3544 | 1.0 |
| xmeas_14 -> xmv_04 | xmeas_14 -> xmv_04 | 0.5302 | 0.8632 | 0.2597 | 0.0000 | 0.3899 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_33 -> xmv_11 | xmeas_33 -> xmv_11 | 0.7052 | 0.6462 | 0.2695 | 0.0000 | 0.2242 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.4199 | 0.7693 | 0.2963 | 0.0000 | 0.3571 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.3577 | 0.7906 | 0.2606 | 0.0000 | 0.1614 | 1.0 |
| xmv_02 -> xmv_10 | xmv_02 -> xmv_10 | 0.3543 | 0.6094 | 0.3774 | 0.0000 | 0.2305 | 1.0 |
| xmv_09 -> xmv_11 | xmv_09 -> xmv_11 | 0.3249 | 0.8582 | 0.2560 | 0.0000 | 0.1975 | 1.0 |

