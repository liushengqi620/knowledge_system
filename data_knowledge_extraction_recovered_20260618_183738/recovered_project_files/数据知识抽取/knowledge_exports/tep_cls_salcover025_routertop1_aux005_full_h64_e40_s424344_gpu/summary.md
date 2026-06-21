# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | salience-cover@0.25+class-evidence-router1-temp0.50@8+router@0.05 | 3 | 0.6146 +/- 0.0030 | 0.6359 +/- 0.0009 | 0.0000 | 0.0000 | 0.0000 | 0.4690 | 0.7026 | 1.0000 | 0.3307 | 0.00 | 0.00 | 0.00 | 0.0000 | on | 19271.6 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_06 -> xmeas_22 | xmv_06 -> xmeas_22 | 0.5736 | 0.8323 | 0.2062 | 0.0000 | 0.9263 | 1.0 |
| xmv_06 -> xmv_05 | xmv_06 -> xmv_05 | 0.3400 | 0.8192 | 0.1165 | 0.0000 | 1.0000 | 1.0 |
| xmeas_34 -> xmeas_22 | xmeas_34 -> xmeas_22 | 0.3039 | 0.8792 | 0.2044 | 0.0000 | 0.9263 | 1.0 |
| xmeas_14 -> xmv_11 | xmeas_14 -> xmv_11 | 0.2994 | 0.6445 | 0.2545 | 0.0000 | 1.0000 | 1.0 |
| xmv_02 -> xmeas_10 | xmv_02 -> xmeas_10 | 0.2964 | 0.6119 | 0.3009 | 0.0000 | 1.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_41 -> xmv_05 | xmeas_41 -> xmv_05 | 0.3917 | 0.7512 | 0.1364 | 0.0000 | 1.0000 | 1.0 |
| xmeas_07 -> xmeas_01 | xmeas_07 -> xmeas_01 | 0.3643 | 0.6974 | 0.1546 | 0.0000 | 1.0000 | 1.0 |
| xmeas_40 -> xmv_05 | xmeas_40 -> xmv_05 | 0.3532 | 0.8142 | 0.2416 | 0.0000 | 1.0000 | 1.0 |
| xmeas_39 -> xmeas_18 | xmeas_39 -> xmeas_18 | 0.3431 | 0.4149 | 0.3349 | 0.0000 | 0.9368 | 1.0 |
| xmeas_20 -> xmeas_01 | xmeas_20 -> xmeas_01 | 0.3085 | 0.8033 | 0.1166 | 0.0000 | 1.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_06 -> xmeas_09 | xmv_06 -> xmeas_09 | 0.3315 | 0.4887 | 0.2131 | 0.0000 | 0.7530 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2967 | 0.8559 | 0.3214 | 0.0000 | 0.8774 | 1.0 |
| xmeas_03 -> xmeas_09 | xmeas_03 -> xmeas_09 | 0.2826 | 0.5311 | 0.3227 | 0.0000 | 0.8040 | 1.0 |
| xmeas_35 -> xmeas_09 | xmeas_35 -> xmeas_09 | 0.2557 | 0.6680 | 0.2340 | 0.0000 | 0.7530 | 1.0 |
| xmeas_35 -> xmeas_14 | xmeas_35 -> xmeas_14 | 0.2495 | 0.7908 | 0.5556 | 0.0000 | 0.7200 | 1.0 |

