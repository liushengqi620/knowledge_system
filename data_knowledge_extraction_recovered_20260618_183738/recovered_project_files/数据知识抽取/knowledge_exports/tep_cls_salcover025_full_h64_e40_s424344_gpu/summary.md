# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | salience-cover@0.25+class-evidence@8 | 3 | 0.6155 +/- 0.0033 | 0.6335 +/- 0.0021 | 0.0175 | 0.0175 | 0.0000 | 0.3498 | 0.6659 | 1.0000 | 0.3214 | 0.00 | 0.00 | 0.00 | 0.0000 | on | 16787.5 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_41 -> xmeas_31 | xmeas_41 -> xmeas_31 | 0.2276 | 0.6327 | 0.5220 | 0.0000 | 0.2019 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2092 | 0.6770 | 0.4401 | 0.0000 | 0.7766 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2088 | 0.7466 | 0.9422 | 0.0000 | 0.3523 | 1.0 |
| xmv_05 -> xmeas_19 | xmv_05 -> xmeas_19 | 0.1908 | 0.6530 | 0.4628 | 0.0000 | 0.5344 | 1.0 |
| xmv_06 -> xmeas_16 | xmv_06 -> xmeas_16 | 0.1795 | 0.7158 | 0.4819 | 0.0000 | 0.2629 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_13 -> xmv_03 | xmeas_13 -> xmv_03 | 0.3687 | 0.7899 | 0.2845 | 0.0000 | 0.5304 | 1.0 |
| xmeas_13 -> xmv_10 | xmeas_13 -> xmv_10 | 0.3508 | 0.7617 | 0.1503 | 0.0000 | 0.8515 | 1.0 |
| xmv_06 -> xmv_10 | xmv_06 -> xmv_10 | 0.3402 | 0.7017 | 0.2807 | 0.0000 | 0.7956 | 1.0 |
| xmv_07 -> xmv_10 | xmv_07 -> xmv_10 | 0.3238 | 0.7499 | 0.1917 | 0.0000 | 0.8458 | 1.0 |
| xmeas_15 -> xmv_10 | xmeas_15 -> xmv_10 | 0.2883 | 0.7375 | 0.2241 | 0.0000 | 0.8125 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2731 | 0.7467 | 0.3802 | 0.0000 | 0.2352 | 1.0 |
| xmeas_17 -> xmv_05 | xmeas_17 -> xmv_05 | 0.2729 | 0.4003 | 0.3153 | 0.0000 | 0.0052 | 1.0 |
| xmeas_11 -> xmeas_09 | xmeas_11 -> xmeas_09 | 0.2218 | 0.8422 | 0.1730 | 0.0000 | 0.8578 | 1.0 |
| xmeas_20 -> xmeas_19 | xmeas_20 -> xmeas_19 | 0.2216 | 0.4202 | 0.3248 | 0.0000 | 0.1608 | 1.0 |
| xmeas_08 -> xmeas_28 | xmeas_08 -> xmeas_28 | 0.2095 | 0.7236 | 0.4568 | 0.0000 | 0.0037 | 1.0 |

