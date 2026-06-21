# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-k8-edge4+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6340 +/- 0.0073 | 0.6452 +/- 0.0076 | 0.0370 | 0.0370 | 0.0833 | 0.3413 | 0.7846 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11778.2 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_28 -> xmeas_10 | xmeas_28 -> xmeas_10 | 0.3333 | 0.3761 | 0.4300 | 0.3238 | 0.5158 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3245 | 0.8213 | 0.2704 | 0.6365 | 0.7382 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2318 | 0.5885 | 0.2831 | 0.2921 | 0.9053 | 1.0 |
| xmeas_32 -> xmv_02 | xmeas_32 -> xmv_02 | 0.2031 | 0.7902 | 0.3770 | 0.0000 | 0.2237 | 1.0 |
| xmeas_35 -> xmeas_13 | xmeas_35 -> xmeas_13 | 0.1952 | 0.7220 | 0.0461 | 0.5116 | 0.6589 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.5294 | 0.7294 | 0.2422 | 0.4845 | 0.6104 | 1.0 |
| xmeas_13 -> xmeas_18 | xmeas_13 -> xmeas_18 | 0.3037 | 0.6703 | 0.5068 | 0.0000 | 0.2388 | 1.0 |
| xmeas_36 -> xmeas_25 | xmeas_36 -> xmeas_25 | 0.2863 | 0.6183 | 0.0792 | 0.6201 | 0.7639 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2549 | 0.8154 | 0.4304 | 0.6314 | 0.7980 | 1.0 |
| xmeas_26 -> xmeas_38 | xmeas_26 -> xmeas_38 | 0.2400 | 0.6524 | 0.4312 | 0.0000 | 0.3814 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3541 | 0.7084 | 0.1309 | 0.5719 | 0.8214 | 1.0 |
| xmeas_09 -> xmv_02 | xmeas_09 -> xmv_02 | 0.2737 | 0.7017 | 0.5934 | 0.0000 | 0.5608 | 1.0 |
| xmeas_06 -> xmeas_31 | xmeas_06 -> xmeas_31 | 0.2384 | 0.6014 | 0.3830 | 0.0000 | 0.3696 | 1.0 |
| xmeas_38 -> xmv_07 | xmeas_38 -> xmv_07 | 0.2326 | 0.4605 | 0.4449 | 0.0000 | 0.5953 | 1.0 |
| xmeas_38 -> xmeas_20 | xmeas_38 -> xmeas_20 | 0.1707 | 0.5371 | 0.1375 | 0.4484 | 0.5255 | 1.0 |

