# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | prior-cover@0.25+alg-prior-multiview-k16-lag3@0.05+class-evidence@8 | 3 | 0.6158 +/- 0.0077 | 0.6351 +/- 0.0062 | 0.0351 | 0.0351 | 0.2819 | 0.2803 | 0.7580 | 1.0000 | 0.3310 | 0.00 | 0.00 | 0.00 | 0.0000 | on | 18052.7 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3314 | 0.8529 | 0.6021 | 0.8489 | 0.5795 | 1.0 |
| xmeas_18 -> xmv_09 | xmeas_18 -> xmv_09 | 0.2753 | 0.6712 | 0.1991 | 0.8207 | 0.5210 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2551 | 0.6612 | 0.2023 | 0.8740 | 0.5860 | 1.0 |
| xmeas_12 -> xmeas_15 | xmeas_12 -> xmeas_15 | 0.2223 | 0.4134 | 0.5458 | 0.3607 | 0.0061 | 1.0 |
| xmeas_37 -> xmv_11 | xmeas_37 -> xmv_11 | 0.2205 | 0.6300 | 0.5618 | 0.0000 | 0.2916 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2797 | 0.8506 | 0.3239 | 0.8581 | 0.5239 | 1.0 |
| xmeas_24 -> xmeas_01 | xmeas_24 -> xmeas_01 | 0.2777 | 0.7247 | 0.4423 | 0.4535 | 0.0107 | 1.0 |
| xmv_11 -> xmeas_22 | xmv_11 -> xmeas_22 | 0.2600 | 0.7394 | 0.5193 | 0.6958 | 0.6739 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.2587 | 0.7344 | 0.2841 | 0.7678 | 0.6759 | 1.0 |
| xmeas_26 -> xmeas_01 | xmeas_26 -> xmeas_01 | 0.2490 | 0.7699 | 0.5363 | 0.4157 | 0.0095 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.4673 | 0.7898 | 0.3503 | 0.7119 | 0.8532 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.3707 | 0.8674 | 0.2348 | 0.7292 | 0.9418 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2936 | 0.8461 | 0.3184 | 0.8581 | 0.2322 | 1.0 |
| xmv_10 -> xmeas_23 | xmv_10 -> xmeas_23 | 0.2674 | 0.8621 | 0.2103 | 0.7527 | 0.9327 | 1.0 |
| xmv_08 -> xmv_10 | xmv_08 -> xmv_10 | 0.2657 | 0.7305 | 0.4463 | 0.0000 | 0.9757 | 1.0 |

