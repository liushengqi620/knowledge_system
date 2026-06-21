# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| cmapss | degradation_stage_id | full | none | group_pair_inclusive+dedup-hard+regime6 | 3 | 0.8105 +/- 0.0021 | 0.8097 +/- 0.0017 | 0.0175 | 0.0175 | 0.0000 | 0.0000 | 0.4410 | 0.0000 | 0.00 | 0.00 | 0.0000 | on | 1210.0 | 34604 |

## Top Evidence Paths

### cmapss / degradation_stage_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| cycle -> op_setting_3 | cycle -> op_setting_3 | 0.2003 | 0.6600 | 0.1644 | 0.0000 | 0.0000 | 1.0 |
| cycle -> sensor_18 | cycle -> sensor_18 | 0.1666 | 0.6265 | 0.3377 | 0.0000 | 0.0000 | 1.0 |
| cycle -> sensor_06 | cycle -> sensor_06 | 0.1630 | 0.7432 | 0.2142 | 0.0000 | 0.0000 | 1.0 |
| cycle -> sensor_04 | cycle -> sensor_04 | 0.1334 | 0.6100 | 0.1723 | 0.0000 | 0.0000 | 1.0 |
| sensor_11 -> cycle | sensor_11 -> cycle | 0.1061 | 0.4609 | 0.2093 | 0.0000 | 0.0000 | 1.0 |

### cmapss / degradation_stage_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| sensor_18 -> sensor_04 | sensor_18 -> sensor_04 | 0.1742 | 0.6586 | 0.1462 | 0.0000 | 0.0000 | 1.0 |
| sensor_06 -> sensor_11 | sensor_06 -> sensor_11 | 0.1290 | 0.6602 | 0.1783 | 0.0000 | 0.0000 | 1.0 |
| sensor_05 -> sensor_11 | sensor_05 -> sensor_11 | 0.1189 | 0.6762 | 0.1644 | 0.0000 | 0.0000 | 1.0 |
| sensor_05 -> sensor_14 | sensor_05 -> sensor_14 | 0.1152 | 0.6648 | 0.1704 | 0.0000 | 0.0000 | 1.0 |
| sensor_15 -> sensor_04 | sensor_15 -> sensor_04 | 0.1139 | 0.5816 | 0.2654 | 0.0000 | 0.0000 | 1.0 |

### cmapss / degradation_stage_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| sensor_15 -> cycle | sensor_15 -> cycle | 0.3687 | 0.6862 | 0.2185 | 0.0000 | 0.0000 | 1.0 |
| sensor_06 -> cycle | sensor_06 -> cycle | 0.3287 | 0.6398 | 0.1727 | 0.0000 | 0.0000 | 1.0 |
| sensor_08 -> cycle | sensor_08 -> cycle | 0.3085 | 0.6689 | 0.1712 | 0.0000 | 0.0000 | 1.0 |
| op_setting_3 -> cycle | op_setting_3 -> cycle | 0.2564 | 0.6635 | 0.1657 | 0.0000 | 0.0000 | 1.0 |
| sensor_17 -> cycle | sensor_17 -> cycle | 0.2353 | 0.6877 | 0.2032 | 0.0000 | 0.0000 | 1.0 |

