# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-prior-cons-s0.25-thr0.35-t0.05-agreement+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05 | 3 | 0.6327 +/- 0.0020 | 0.6434 +/- 0.0055 | 0.0000 | 0.0000 | 0.1533 | 0.2302 | 0.7803 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11729.9 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4531 | 0.7297 | 0.5354 | 0.6601 | 0.5133 | 1.0 |
| xmeas_30 -> xmv_09 | xmeas_30 -> xmv_09 | 0.3513 | 0.6678 | 0.3974 | 0.0000 | 0.2117 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2834 | 0.8811 | 0.4752 | 0.2968 | 0.1184 | 1.0 |
| xmeas_01 -> xmv_10 | xmeas_01 -> xmv_10 | 0.2766 | 0.8395 | 0.7776 | 0.0000 | 0.3534 | 1.0 |
| xmeas_03 -> xmeas_13 | xmeas_03 -> xmeas_13 | 0.2619 | 0.8977 | 0.4129 | 0.0000 | 0.1840 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.6595 | 0.6796 | 0.6267 | 0.5904 | 0.4815 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3901 | 0.7282 | 0.6380 | 0.6303 | 0.4396 | 1.0 |
| xmv_07 -> xmv_05 | xmv_07 -> xmv_05 | 0.3338 | 0.6388 | 0.3391 | 0.0000 | 0.3067 | 1.0 |
| xmeas_39 -> xmv_05 | xmeas_39 -> xmv_05 | 0.2901 | 0.6661 | 0.4356 | 0.0000 | 0.4845 | 1.0 |
| xmeas_40 -> xmv_03 | xmeas_40 -> xmv_03 | 0.2583 | 0.7452 | 0.5325 | 0.0000 | 0.1148 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.5004 | 0.8506 | 0.8689 | 0.5264 | 0.6037 | 1.0 |
| xmv_10 -> xmeas_13 | xmv_10 -> xmeas_13 | 0.3442 | 0.7762 | 0.6996 | 0.0000 | 0.3033 | 1.0 |
| xmeas_03 -> xmeas_11 | xmeas_03 -> xmeas_11 | 0.2953 | 0.4725 | 0.4444 | 0.0000 | 0.1153 | 1.0 |
| xmv_10 -> xmeas_30 | xmv_10 -> xmeas_30 | 0.2308 | 0.7116 | 0.5297 | 0.0000 | 0.2158 | 1.0 |
| xmeas_01 -> xmv_11 | xmeas_01 -> xmv_11 | 0.2059 | 0.7900 | 0.5173 | 0.0000 | 0.5909 | 1.0 |

