# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-static_lag-lag3@0.25@8+path-aux@0.05 | 3 | 0.6306 +/- 0.0061 | 0.6453 +/- 0.0064 | 0.0175 | 0.0175 | 0.0864 | 0.2002 | 0.7788 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10742.6 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3929 | 0.3790 | 0.1950 | 0.5248 | 0.2164 | 1.0 |
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.3559 | 0.8785 | 0.5746 | 0.0000 | 0.3306 | 1.0 |
| xmeas_26 -> xmeas_18 | xmeas_26 -> xmeas_18 | 0.2844 | 0.6981 | 0.3446 | 0.0000 | 0.4744 | 1.0 |
| xmv_05 -> xmeas_10 | xmv_05 -> xmeas_10 | 0.2836 | 0.7403 | 0.3365 | 0.0000 | 0.2412 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2715 | 0.9024 | 0.1741 | 0.3970 | 0.5739 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_09 | xmv_03 -> xmeas_09 | 0.3199 | 0.6841 | 0.3593 | 0.0000 | 0.4246 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3080 | 0.6534 | 0.1481 | 0.5399 | 0.4548 | 1.0 |
| xmv_11 -> xmeas_28 | xmv_11 -> xmeas_28 | 0.2850 | 0.6865 | 0.8862 | 0.0000 | 0.1530 | 1.0 |
| xmeas_23 -> xmv_10 | xmeas_23 -> xmv_10 | 0.2234 | 0.6239 | 0.1108 | 0.4825 | 0.2734 | 1.0 |
| xmeas_23 -> xmeas_25 | xmeas_23 -> xmeas_25 | 0.1953 | 0.5945 | 0.3566 | 0.0000 | 0.1689 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_06 -> xmeas_34 | xmv_06 -> xmeas_34 | 0.2961 | 0.7752 | 0.1519 | 0.2665 | 0.3095 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2516 | 0.8367 | 0.5727 | 0.0000 | 0.0346 | 1.0 |
| xmv_11 -> xmeas_35 | xmv_11 -> xmeas_35 | 0.2393 | 0.8076 | 0.4283 | 0.0000 | 0.0134 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2252 | 0.6335 | 0.0961 | 0.3928 | 0.4884 | 1.0 |
| xmeas_35 -> xmeas_39 | xmeas_35 -> xmeas_39 | 0.2249 | 0.6827 | 0.3651 | 0.0000 | 0.0700 | 1.0 |

