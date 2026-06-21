# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-prior-cons-s0.25-thr0.35-t0.05+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05 | 3 | 0.6368 +/- 0.0034 | 0.6469 +/- 0.0027 | 0.0000 | 0.0000 | 0.1494 | 0.2207 | 0.7934 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11037.8 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3531 | 0.8458 | 0.4824 | 0.5634 | 0.2758 | 1.0 |
| xmv_05 -> xmeas_30 | xmv_05 -> xmeas_30 | 0.3527 | 0.7860 | 0.3440 | 0.0000 | 0.4035 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2400 | 0.7088 | 0.2014 | 0.7664 | 0.5174 | 1.0 |
| xmeas_25 -> xmeas_13 | xmeas_25 -> xmeas_13 | 0.2176 | 0.6898 | 0.4062 | 0.0000 | 0.3685 | 1.0 |
| xmv_10 -> xmeas_02 | xmv_10 -> xmeas_02 | 0.1961 | 0.7356 | 0.4803 | 0.0000 | 0.3723 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmv_10 | xmeas_30 -> xmv_10 | 0.3048 | 0.6237 | 0.3919 | 0.0000 | 0.4083 | 1.0 |
| xmeas_21 -> xmeas_36 | xmeas_21 -> xmeas_36 | 0.2116 | 0.7150 | 0.7548 | 0.0000 | 0.1565 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.2088 | 0.5982 | 0.1689 | 0.6593 | 0.5973 | 1.0 |
| xmeas_21 -> xmeas_11 | xmeas_21 -> xmeas_11 | 0.1963 | 0.5972 | 0.7889 | 0.0000 | 0.3725 | 1.0 |
| xmeas_10 -> xmeas_26 | xmeas_10 -> xmeas_26 | 0.1956 | 0.5784 | 0.4028 | 0.0000 | 0.0810 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.5395 | 0.7747 | 0.4118 | 0.6282 | 0.1334 | 1.0 |
| xmeas_01 -> xmv_11 | xmeas_01 -> xmv_11 | 0.3593 | 0.6933 | 0.3816 | 0.0000 | 0.1498 | 1.0 |
| xmeas_08 -> xmv_10 | xmeas_08 -> xmv_10 | 0.3588 | 0.6968 | 0.3541 | 0.0000 | 0.3058 | 1.0 |
| xmeas_23 -> xmv_10 | xmeas_23 -> xmv_10 | 0.3499 | 0.7481 | 0.1271 | 0.6898 | 0.3949 | 1.0 |
| xmv_10 -> xmeas_17 | xmv_10 -> xmeas_17 | 0.2947 | 0.7601 | 0.3747 | 0.0000 | 0.3778 | 1.0 |

