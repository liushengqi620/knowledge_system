# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6095 +/- 0.0105 | 0.6185 +/- 0.0108 | 0.0000 | 0.0000 | 0.0000 | 0.2975 | 0.7480 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7280.4 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3745 | 0.8940 | 0.2984 | 0.0000 | 0.7427 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.3553 | 0.7231 | 0.2690 | 0.0000 | 0.9444 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.3314 | 0.7461 | 0.2995 | 0.0000 | 0.5448 | 1.0 |
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.3076 | 0.7185 | 0.3259 | 0.0000 | 0.3019 | 1.0 |
| xmeas_08 -> xmv_09 | xmeas_08 -> xmv_09 | 0.2484 | 0.3767 | 0.3062 | 0.0000 | 0.0088 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_26 -> xmv_04 | xmeas_26 -> xmv_04 | 0.6252 | 0.8061 | 0.2365 | 0.0000 | 0.6708 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.4468 | 0.7952 | 0.2603 | 0.0000 | 0.6159 | 1.0 |
| xmeas_31 -> xmv_04 | xmeas_31 -> xmv_04 | 0.4086 | 0.7727 | 0.3099 | 0.0000 | 0.5082 | 1.0 |
| xmeas_39 -> xmv_04 | xmeas_39 -> xmv_04 | 0.3892 | 0.7188 | 0.3149 | 0.0000 | 0.5056 | 1.0 |
| xmv_09 -> xmv_11 | xmv_09 -> xmv_11 | 0.3716 | 0.8845 | 0.2502 | 0.0000 | 0.7495 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.6003 | 0.7876 | 0.3867 | 0.0000 | 0.3591 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.3657 | 0.8772 | 0.2806 | 0.0000 | 0.2691 | 1.0 |
| xmeas_07 -> xmv_10 | xmeas_07 -> xmv_10 | 0.3401 | 0.6794 | 0.3066 | 0.0000 | 0.3492 | 1.0 |
| xmv_03 -> xmv_11 | xmv_03 -> xmv_11 | 0.2699 | 0.7223 | 0.3378 | 0.0000 | 0.4832 | 1.0 |
| xmeas_26 -> xmv_09 | xmeas_26 -> xmv_09 | 0.2468 | 0.8837 | 0.2424 | 0.0000 | 0.8474 | 1.0 |

