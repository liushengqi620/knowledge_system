# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+multihop@0.25+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6005 +/- 0.0205 | 0.6049 +/- 0.0255 | 0.0000 | 0.0000 | 0.0000 | 0.3468 | 0.8349 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 8288.2 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_09 -> xmeas_16 -> xmv_10 | xmv_09 -> xmeas_16 -> xmv_10 | 0.3366 | 0.7945 | 0.4022 | 0.0000 | 0.5508 | 2.0 |
| xmv_10 -> xmv_01 -> xmeas_35 | xmv_10 -> xmv_01 -> xmeas_35 | 0.3224 | 0.7839 | 0.3971 | 0.0000 | 0.4574 | 2.0 |
| xmeas_28 -> xmeas_09 | xmeas_28 -> xmeas_09 | 0.3163 | 0.7350 | 0.3394 | 0.0000 | 0.5576 | 1.0 |
| xmeas_05 -> xmeas_23 -> xmeas_09 | xmeas_05 -> xmeas_23 -> xmeas_09 | 0.3153 | 0.8282 | 0.4356 | 0.0000 | 0.3819 | 2.0 |
| xmv_10 -> xmeas_41 -> xmeas_25 | xmv_10 -> xmeas_41 -> xmeas_25 | 0.2964 | 0.8366 | 0.4581 | 0.0000 | 0.1624 | 2.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_13 -> xmeas_19 | xmeas_13 -> xmeas_19 | 0.6099 | 0.7470 | 0.2629 | 0.0000 | 0.1265 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.4252 | 0.7296 | 0.3342 | 0.0000 | 0.4479 | 1.0 |
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.3900 | 0.7224 | 0.2340 | 0.0000 | 0.8007 | 1.0 |
| xmv_10 -> xmv_01 | xmv_10 -> xmv_01 | 0.3638 | 0.3623 | 0.3490 | 0.0000 | 0.2737 | 1.0 |
| xmv_10 -> xmv_07 | xmv_10 -> xmv_07 | 0.3309 | 0.7023 | 0.2765 | 0.0000 | 0.5821 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.4580 | 0.7710 | 0.3071 | 0.0000 | 0.3021 | 1.0 |
| xmeas_25 -> xmeas_14 -> xmv_10 | xmeas_25 -> xmeas_14 -> xmv_10 | 0.4441 | 0.7515 | 0.4692 | 0.0000 | 0.2600 | 2.0 |
| xmeas_14 -> xmv_10 | xmeas_14 -> xmv_10 | 0.3882 | 0.6203 | 0.3207 | 0.0000 | 0.3228 | 1.0 |
| xmv_02 -> xmv_09 | xmv_02 -> xmv_09 | 0.3227 | 0.6800 | 0.3798 | 0.0000 | 0.0338 | 1.0 |
| xmeas_28 -> xmv_09 | xmeas_28 -> xmv_09 | 0.2600 | 0.4047 | 0.3263 | 0.0000 | 0.0773 | 1.0 |

