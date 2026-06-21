# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+edge-cal-f0.20-b4.0-reg1.00+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6111 +/- 0.0061 | 0.6302 +/- 0.0067 | 0.0000 | 0.0000 | 0.3010 | 0.3401 | 0.7273 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 17942.3 | 153678 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_17 -> xmeas_19 | xmeas_17 -> xmeas_19 | 0.3594 | 0.3652 | 0.4177 | 0.0000 | 0.8123 | 1.0 |
| xmeas_17 -> xmv_11 | xmeas_17 -> xmv_11 | 0.2730 | 0.7585 | 0.4587 | 0.8543 | 0.5209 | 1.0 |
| xmeas_29 -> xmeas_25 | xmeas_29 -> xmeas_25 | 0.2333 | 0.8214 | 0.5348 | 0.7964 | 0.7427 | 1.0 |
| xmv_02 -> xmeas_09 | xmv_02 -> xmeas_09 | 0.2024 | 0.6334 | 0.4827 | 0.0000 | 0.4245 | 1.0 |
| xmeas_17 -> xmeas_38 | xmeas_17 -> xmeas_38 | 0.1942 | 0.6971 | 0.4795 | 0.0000 | 0.1707 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_12 -> xmv_11 | xmeas_12 -> xmv_11 | 0.6939 | 0.4776 | 0.3693 | 0.0000 | 0.1101 | 1.0 |
| xmeas_25 -> xmv_11 | xmeas_25 -> xmv_11 | 0.4913 | 0.6923 | 0.1820 | 0.8068 | 0.6337 | 1.0 |
| xmeas_06 -> xmv_11 | xmeas_06 -> xmv_11 | 0.4466 | 0.6409 | 0.3845 | 0.0000 | 0.4530 | 1.0 |
| xmeas_29 -> xmv_11 | xmeas_29 -> xmv_11 | 0.4094 | 0.6787 | 0.1440 | 0.7676 | 0.7250 | 1.0 |
| xmeas_22 -> xmv_06 | xmeas_22 -> xmv_06 | 0.3249 | 0.7299 | 0.3401 | 0.6560 | 0.7663 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_02 | xmv_10 -> xmv_02 | 0.2636 | 0.8424 | 0.4688 | 0.0000 | 0.5157 | 1.0 |
| xmeas_22 -> xmeas_37 | xmeas_22 -> xmeas_37 | 0.2248 | 0.9094 | 0.4229 | 0.0000 | 0.8707 | 1.0 |
| xmeas_10 -> xmeas_22 | xmeas_10 -> xmeas_22 | 0.2226 | 0.8554 | 0.2448 | 0.6348 | 0.9103 | 1.0 |
| xmv_06 -> xmv_02 | xmv_06 -> xmv_02 | 0.2209 | 0.8667 | 0.6602 | 0.0000 | 0.6523 | 1.0 |
| xmeas_10 -> xmeas_01 | xmeas_10 -> xmeas_01 | 0.2166 | 0.8273 | 0.2626 | 0.3408 | 0.9903 | 1.0 |

