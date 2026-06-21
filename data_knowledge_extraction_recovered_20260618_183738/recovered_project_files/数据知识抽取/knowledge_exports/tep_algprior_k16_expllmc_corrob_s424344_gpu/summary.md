# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert_llm@0.05 | group_pair_inclusive+dedup-hard+prior-cover@0.25+prior-cal@0.10+alg-prior-hybrid-k16-lag3@0.05+corrob-e0.25-b0.20+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6106 +/- 0.0053 | 0.6226 +/- 0.0055 | 0.0175 | 0.0175 | 0.3324 | 0.3252 | 0.7433 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 8700.0 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert_llm@0.05 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmv_11 | xmeas_18 -> xmv_11 | 0.4565 | 0.7522 | 0.3717 | 0.0000 | 0.6381 | 1.0 |
| xmeas_16 -> xmv_11 | xmeas_16 -> xmv_11 | 0.4303 | 0.8061 | 0.1819 | 0.8002 | 0.5674 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.2826 | 0.7879 | 0.2962 | 0.7579 | 0.3521 | 1.0 |
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.2596 | 0.7358 | 0.3364 | 0.0000 | 0.4731 | 1.0 |
| xmeas_07 -> xmv_11 | xmeas_07 -> xmv_11 | 0.2543 | 0.7540 | 0.1666 | 0.7519 | 0.6849 | 1.0 |

### tep / event_quality_class_id / full / prior=expert_llm@0.05 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.5754 | 0.8334 | 0.3219 | 0.6175 | 0.5405 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.4715 | 0.8862 | 0.1492 | 0.7514 | 0.7684 | 1.0 |
| xmv_11 -> xmv_05 | xmv_11 -> xmv_05 | 0.4478 | 0.8630 | 0.1392 | 0.7921 | 0.8398 | 1.0 |
| xmeas_18 -> xmv_04 | xmeas_18 -> xmv_04 | 0.4403 | 0.8622 | 0.2817 | 0.0000 | 0.5552 | 1.0 |
| xmeas_36 -> xmv_04 | xmeas_36 -> xmv_04 | 0.3663 | 0.8787 | 0.1809 | 0.6419 | 0.7632 | 1.0 |

### tep / event_quality_class_id / full / prior=expert_llm@0.05 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_12 -> xmv_05 | xmeas_12 -> xmv_05 | 0.3440 | 0.7840 | 0.2513 | 0.0000 | 0.9121 | 1.0 |
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.3419 | 0.6043 | 0.1885 | 0.7678 | 0.4034 | 1.0 |
| xmeas_29 -> xmv_11 | xmeas_29 -> xmv_11 | 0.3199 | 0.8033 | 0.1587 | 0.7713 | 0.6286 | 1.0 |
| xmv_11 -> xmeas_35 | xmv_11 -> xmeas_35 | 0.3071 | 0.6475 | 0.2300 | 0.7525 | 0.4195 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.2967 | 0.6831 | 0.2939 | 0.0000 | 0.2736 | 1.0 |

