# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| cmapss | degradation_stage_id | full | none | group_pair_inclusive+dedup-hard+regime6+no-order-path | 3 | 0.8086 +/- 0.0041 | 0.8073 +/- 0.0041 | 0.0175 | 0.0175 | 0.0000 | 0.0000 | 0.4768 | 0.0000 | 0.00 | 0.00 | 0.0000 | on | 1203.5 | 34604 |

## Top Evidence Paths

### cmapss / degradation_stage_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| sensor_12 -> sensor_06 | sensor_12 -> sensor_06 | 0.1261 | 0.6003 | 0.3179 | 0.0000 | 0.0000 | 1.0 |
| sensor_02 -> sensor_11 | sensor_02 -> sensor_11 | 0.0846 | 0.5893 | 0.2624 | 0.0000 | 0.0000 | 1.0 |
| sensor_11 -> op_setting_1 | sensor_11 -> op_setting_1 | 0.0724 | 0.5887 | 0.1966 | 0.0000 | 0.0000 | 1.0 |
| sensor_12 -> op_setting_1 | sensor_12 -> op_setting_1 | 0.0699 | 0.5799 | 0.1945 | 0.0000 | 0.0000 | 1.0 |
| sensor_09 -> sensor_06 | sensor_09 -> sensor_06 | 0.0591 | 0.5960 | 0.2652 | 0.0000 | 0.0000 | 1.0 |

### cmapss / degradation_stage_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| sensor_05 -> sensor_14 | sensor_05 -> sensor_14 | 0.1580 | 0.5755 | 0.1633 | 0.0000 | 0.0000 | 1.0 |
| sensor_06 -> sensor_11 | sensor_06 -> sensor_11 | 0.1380 | 0.5944 | 0.1508 | 0.0000 | 0.0000 | 1.0 |
| sensor_18 -> sensor_11 | sensor_18 -> sensor_11 | 0.1193 | 0.5683 | 0.2307 | 0.0000 | 0.0000 | 1.0 |
| sensor_06 -> sensor_13 | sensor_06 -> sensor_13 | 0.1129 | 0.5971 | 0.1290 | 0.0000 | 0.0000 | 1.0 |
| sensor_18 -> sensor_04 | sensor_18 -> sensor_04 | 0.1033 | 0.6558 | 0.1799 | 0.0000 | 0.0000 | 1.0 |

### cmapss / degradation_stage_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| sensor_14 -> sensor_12 | sensor_14 -> sensor_12 | 0.0847 | 0.5190 | 0.1701 | 0.0000 | 0.0000 | 1.0 |
| sensor_09 -> sensor_18 | sensor_09 -> sensor_18 | 0.0842 | 0.6026 | 0.1439 | 0.0000 | 0.0000 | 1.0 |
| sensor_01 -> sensor_07 | sensor_01 -> sensor_07 | 0.0817 | 0.5948 | 0.0902 | 0.0000 | 0.0000 | 1.0 |
| sensor_01 -> sensor_21 | sensor_01 -> sensor_21 | 0.0640 | 0.5328 | 0.0852 | 0.0000 | 0.0000 | 1.0 |
| sensor_07 -> sensor_06 | sensor_07 -> sensor_06 | 0.0633 | 0.4726 | 0.2681 | 0.0000 | 0.0000 | 1.0 |

