# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-evid-cons-s0.10-thr0.50-t0.05-relative+prior-cover@0.20+alg-prior-edge_pool-k8-g3-lag3-vote2-sv0.55-vb0.15-pool2.0-rank0.35@0.05+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6277 +/- 0.0039 | 0.6418 +/- 0.0067 | 0.0175 | 0.0175 | 0.0356 | 0.0479 | 0.7845 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11146.8 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_33 -> xmeas_07 | xmeas_33 -> xmeas_07 | 0.2851 | 0.5626 | 0.4714 | 0.0000 | 0.0337 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2357 | 0.6577 | 0.0987 | 0.1379 | 0.0598 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2245 | 0.1592 | 0.1466 | 0.2405 | 0.0817 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2144 | 0.7681 | 0.4959 | 0.0000 | 0.1094 | 1.0 |
| xmv_05 -> xmeas_18 | xmv_05 -> xmeas_18 | 0.2131 | 0.7464 | 0.4534 | 0.0000 | 0.0634 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_04 -> xmv_05 | xmeas_04 -> xmv_05 | 0.3916 | 0.5170 | 0.4596 | 0.0000 | 0.0596 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3721 | 0.6831 | 0.3322 | 0.1662 | 0.0861 | 1.0 |
| xmeas_18 -> xmeas_28 | xmeas_18 -> xmeas_28 | 0.3084 | 0.4756 | 0.4102 | 0.0000 | 0.0634 | 1.0 |
| xmv_01 -> xmv_10 | xmv_01 -> xmv_10 | 0.2930 | 0.7288 | 0.4278 | 0.0000 | 0.0078 | 1.0 |
| xmeas_40 -> xmv_03 | xmeas_40 -> xmv_03 | 0.2913 | 0.7573 | 0.4496 | 0.0000 | 0.0402 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3421 | 0.6898 | 0.3273 | 0.1477 | 0.0698 | 1.0 |
| xmeas_01 -> xmv_10 | xmeas_01 -> xmv_10 | 0.3071 | 0.6631 | 0.5939 | 0.0000 | 0.0226 | 1.0 |
| xmeas_18 -> xmv_10 | xmeas_18 -> xmv_10 | 0.2794 | 0.5737 | 0.2980 | 0.0000 | 0.0713 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2365 | 0.5625 | 0.1162 | 0.2636 | 0.1516 | 1.0 |
| xmeas_24 -> xmv_10 | xmeas_24 -> xmv_10 | 0.2106 | 0.3329 | 0.5208 | 0.0000 | 0.0471 | 1.0 |

