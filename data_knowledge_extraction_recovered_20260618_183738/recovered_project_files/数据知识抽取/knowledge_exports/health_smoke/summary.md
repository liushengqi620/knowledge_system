# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| cmapss | degradation_stage_id | full | none | 1 | 0.3603 +/- 0.0000 | 0.3683 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.2335 | 0.1303 | 0.00 | 0.10 | 0.3283 | on | 2911.8 | 13212 |

## Top Evidence Paths

### cmapss / degradation_stage_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| sensor_06 -> sensor_16 | sensor_06 -> sensor_16 | 0.1826 | 0.4526 | 0.2801 | 0.0000 | 0.0000 | 1.0 |
| sensor_20 -> sensor_07 | sensor_20 -> sensor_07 | 0.1783 | 0.4456 | 0.2906 | 0.0000 | 0.0000 | 1.0 |
| sensor_06 -> sensor_02 | sensor_06 -> sensor_02 | 0.1711 | 0.5142 | 0.2780 | 0.0000 | 0.0000 | 1.0 |
| sensor_18 -> op_setting_3 | sensor_18 -> op_setting_3 | 0.1707 | 0.4494 | 0.2913 | 0.0000 | 0.0000 | 1.0 |
| sensor_20 -> sensor_06 | sensor_20 -> sensor_06 | 0.1668 | 0.4605 | 0.2850 | 0.0000 | 0.0000 | 1.0 |

