# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cmapss | degradation_stage_id | full | none | 3 | 0.7001 +/- 0.0066 | 0.6944 +/- 0.0077 | 0.1111 | 0.1111 | 0.0000 | 0.3144 | 0.0000 | 1540.7 | 31112 |

## Top Evidence Paths

### cmapss / degradation_stage_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| sensor_07 -> cycle | sensor_07 -> cycle | 0.2177 | 0.8191 | 0.1502 | 0.0000 | 1.0000 |
| sensor_21 -> cycle | sensor_21 -> cycle | 0.2115 | 0.7387 | 0.1996 | 0.0000 | 1.0000 |
| sensor_10 -> cycle | sensor_10 -> cycle | 0.1598 | 0.6507 | 0.1500 | 0.0000 | 1.0000 |
| sensor_11 -> op_setting_2 | sensor_11 -> op_setting_2 | 0.1549 | 0.6661 | 0.9399 | 0.0000 | 0.2780 |
| sensor_11 -> cycle | sensor_11 -> cycle | 0.1523 | 0.6123 | 0.1655 | 0.0000 | 1.0000 |

### cmapss / degradation_stage_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| cycle -> sensor_16 | cycle -> sensor_16 | 0.2781 | 0.8272 | 0.0234 | 0.0000 | 1.0000 |
| cycle -> sensor_08 | cycle -> sensor_08 | 0.2623 | 0.8408 | 0.1560 | 0.0000 | 1.0000 |
| cycle -> sensor_10 | cycle -> sensor_10 | 0.2331 | 0.8173 | 0.1763 | 0.0000 | 1.0000 |
| cycle -> sensor_02 | cycle -> sensor_02 | 0.2320 | 0.8140 | 0.2245 | 0.0000 | 1.0000 |
| cycle -> sensor_15 | cycle -> sensor_15 | 0.2308 | 0.8067 | 0.1429 | 0.0000 | 1.0000 |

### cmapss / degradation_stage_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| sensor_14 -> cycle | sensor_14 -> cycle | 0.2602 | 0.8402 | 0.0426 | 0.0000 | 1.0000 |
| sensor_20 -> cycle | sensor_20 -> cycle | 0.1579 | 0.8649 | 0.1131 | 0.0000 | 1.0000 |
| sensor_11 -> cycle | sensor_11 -> cycle | 0.1455 | 0.6813 | 0.8189 | 0.0000 | 1.0000 |
| sensor_12 -> cycle | sensor_12 -> cycle | 0.1430 | 0.9131 | 0.1473 | 0.0000 | 1.0000 |
| sensor_13 -> cycle | sensor_13 -> cycle | 0.1393 | 0.8425 | 0.0852 | 0.0000 | 1.0000 |

