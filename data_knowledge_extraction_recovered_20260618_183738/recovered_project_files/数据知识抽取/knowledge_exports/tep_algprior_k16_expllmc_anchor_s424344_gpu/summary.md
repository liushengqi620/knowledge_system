# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert_llm@0.05 | group_pair_inclusive+dedup-hard+prior-cover@0.25+prior-cal@0.10+alg-prior-hybrid-k16-lag3@0.05+anchor-e0.25-b0.20-n0.35+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6121 +/- 0.0070 | 0.6214 +/- 0.0097 | 0.0351 | 0.0351 | 0.3116 | 0.3251 | 0.7458 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 8058.5 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert_llm@0.05 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.4933 | 0.7740 | 0.3027 | 0.0000 | 0.4344 | 1.0 |
| xmeas_39 -> xmv_05 | xmeas_39 -> xmv_05 | 0.3205 | 0.7812 | 0.2491 | 0.0000 | 0.9454 | 1.0 |
| xmeas_18 -> xmv_11 | xmeas_18 -> xmv_11 | 0.3188 | 0.6955 | 0.2892 | 0.0000 | 0.4099 | 1.0 |
| xmeas_07 -> xmv_11 | xmeas_07 -> xmv_11 | 0.3087 | 0.7662 | 0.1571 | 0.7519 | 0.6715 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.3071 | 0.7291 | 0.2186 | 0.7579 | 0.3673 | 1.0 |

### tep / event_quality_class_id / full / prior=expert_llm@0.05 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.4847 | 0.8474 | 0.1722 | 0.7514 | 0.6570 | 1.0 |
| xmeas_36 -> xmv_04 | xmeas_36 -> xmv_04 | 0.4514 | 0.8631 | 0.2493 | 0.6419 | 0.6034 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.3784 | 0.8084 | 0.2690 | 0.6175 | 0.5697 | 1.0 |
| xmeas_13 -> xmv_04 | xmeas_13 -> xmv_04 | 0.3552 | 0.8148 | 0.1926 | 0.7388 | 0.7155 | 1.0 |
| xmeas_40 -> xmv_04 | xmeas_40 -> xmv_04 | 0.3546 | 0.7089 | 0.2953 | 0.0000 | 0.4582 | 1.0 |

### tep / event_quality_class_id / full / prior=expert_llm@0.05 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_39 -> xmv_10 | xmeas_39 -> xmv_10 | 0.4599 | 0.5481 | 0.3427 | 0.0000 | 0.1606 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.4241 | 0.6952 | 0.3404 | 0.0000 | 0.2537 | 1.0 |
| xmeas_07 -> xmv_11 | xmeas_07 -> xmv_11 | 0.4234 | 0.7429 | 0.1650 | 0.7523 | 0.5098 | 1.0 |
| xmeas_19 -> xmv_11 | xmeas_19 -> xmv_11 | 0.3928 | 0.7747 | 0.1401 | 0.6566 | 0.7522 | 1.0 |
| xmeas_07 -> xmv_10 | xmeas_07 -> xmv_10 | 0.3372 | 0.6448 | 0.1475 | 0.7578 | 0.3958 | 1.0 |

