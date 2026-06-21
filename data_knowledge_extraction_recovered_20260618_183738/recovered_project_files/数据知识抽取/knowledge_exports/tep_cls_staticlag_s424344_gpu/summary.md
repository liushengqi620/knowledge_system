# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-evidence-static_lag-lag3@0.50@8+path-aux@0.05+router@0.05 | 3 | 0.6071 +/- 0.0085 | 0.6162 +/- 0.0121 | 0.0000 | 0.0000 | 0.0000 | 0.1456 | 0.7404 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7348.2 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_38 | xmv_10 -> xmeas_38 | 0.4488 | 0.7974 | 0.2638 | 0.0000 | 0.3047 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.4076 | 0.8346 | 0.3109 | 0.0000 | 0.4737 | 1.0 |
| xmeas_18 -> xmeas_13 | xmeas_18 -> xmeas_13 | 0.3814 | 0.6679 | 0.2429 | 0.0000 | 0.4515 | 1.0 |
| xmv_10 -> xmeas_35 | xmv_10 -> xmeas_35 | 0.3426 | 0.8117 | 0.2608 | 0.0000 | 0.1370 | 1.0 |
| xmv_10 -> xmeas_32 | xmv_10 -> xmeas_32 | 0.3191 | 0.6237 | 0.2450 | 0.0000 | 0.1152 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmv_04 | xmeas_14 -> xmv_04 | 0.6455 | 0.8585 | 0.2596 | 0.0000 | 0.2594 | 1.0 |
| xmv_02 -> xmv_04 | xmv_02 -> xmv_04 | 0.6026 | 0.7793 | 0.3574 | 0.0000 | 0.1658 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.5936 | 0.8416 | 0.2701 | 0.0000 | 0.3173 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.5889 | 0.8091 | 0.2955 | 0.0000 | 0.3086 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.5342 | 0.7151 | 0.2973 | 0.0000 | 0.1598 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_02 -> xmv_10 | xmv_02 -> xmv_10 | 0.3885 | 0.6213 | 0.3768 | 0.0000 | 0.1457 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.3686 | 0.6424 | 0.2898 | 0.0000 | 0.1989 | 1.0 |
| xmeas_07 -> xmeas_18 | xmeas_07 -> xmeas_18 | 0.2054 | 0.6085 | 0.2719 | 0.0000 | 0.1976 | 1.0 |
| xmeas_22 -> xmeas_18 | xmeas_22 -> xmeas_18 | 0.1988 | 0.2846 | 0.3787 | 0.0000 | 0.1437 | 1.0 |
| xmeas_33 -> xmv_10 | xmeas_33 -> xmv_10 | 0.1822 | 0.4580 | 0.3315 | 0.0000 | 0.1486 | 1.0 |

