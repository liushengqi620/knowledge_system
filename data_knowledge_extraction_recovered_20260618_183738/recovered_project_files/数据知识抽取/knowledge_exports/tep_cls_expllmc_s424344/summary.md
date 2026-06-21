# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert_llm@0.00 | group_pair_inclusive+dedup-hard+prior-cover@0.05+prior-cal@0.10+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6129 +/- 0.0111 | 0.6182 +/- 0.0137 | 0.0351 | 0.0351 | 0.0295 | 0.3028 | 0.7407 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 768.5 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert_llm@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_18 | xmv_10 -> xmeas_18 | 0.2984 | 0.8127 | 0.3062 | 0.0000 | 0.6018 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.2852 | 0.8604 | 0.2812 | 0.0000 | 0.3160 | 1.0 |
| xmeas_18 -> xmeas_13 | xmeas_18 -> xmeas_13 | 0.2323 | 0.4907 | 0.2796 | 0.0000 | 0.6812 | 1.0 |
| xmv_11 -> xmeas_11 | xmv_11 -> xmeas_11 | 0.2162 | 0.8100 | 0.3440 | 0.5654 | 0.5129 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.2138 | 0.6316 | 0.2672 | 0.0000 | 0.9608 | 1.0 |

### tep / event_quality_class_id / full / prior=expert_llm@0.00 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_13 -> xmv_11 | xmeas_13 -> xmv_11 | 0.3718 | 0.8191 | 0.3112 | 0.0000 | 0.5962 | 1.0 |
| xmeas_19 -> xmv_11 | xmeas_19 -> xmv_11 | 0.2792 | 0.4044 | 0.2485 | 0.0000 | 0.5974 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2509 | 0.6508 | 0.5401 | 0.0000 | 0.5921 | 1.0 |
| xmeas_35 -> xmv_05 | xmeas_35 -> xmv_05 | 0.2051 | 0.5814 | 0.2425 | 0.0000 | 0.7737 | 1.0 |
| xmeas_41 -> xmv_05 | xmeas_41 -> xmv_05 | 0.1741 | 0.4766 | 0.3636 | 0.0000 | 0.6345 | 1.0 |

### tep / event_quality_class_id / full / prior=expert_llm@0.00 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.6933 | 0.9142 | 0.2554 | 0.0000 | 0.8950 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.6055 | 0.8337 | 0.4002 | 0.0000 | 0.3755 | 1.0 |
| xmv_11 -> xmeas_16 | xmv_11 -> xmeas_16 | 0.4643 | 0.8445 | 0.2918 | 0.0000 | 0.1924 | 1.0 |
| xmeas_05 -> xmv_11 | xmeas_05 -> xmv_11 | 0.4639 | 0.8750 | 0.3382 | 0.0000 | 0.5844 | 1.0 |
| xmeas_13 -> xmv_11 | xmeas_13 -> xmv_11 | 0.4496 | 0.9138 | 0.2435 | 0.0000 | 0.9043 | 1.0 |

