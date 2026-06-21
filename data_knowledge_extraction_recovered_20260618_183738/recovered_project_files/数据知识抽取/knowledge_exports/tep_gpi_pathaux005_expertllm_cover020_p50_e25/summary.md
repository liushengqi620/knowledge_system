# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert_llm@0.00 | group_pair_inclusive+dedup-hard+prior-cover@0.20+path-aux@0.05 | 1 | 0.5976 +/- 0.0000 | 0.6101 +/- 0.0000 | n/a | n/a | 0.1879 | 0.0000 | 0.6845 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 812.0 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert_llm@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_21 -> xmv_10 | xmeas_21 -> xmv_10 | 0.3801 | 0.6174 | 0.3835 | 0.0000 | 0.0000 | 1.0 |
| xmeas_33 -> xmv_11 | xmeas_33 -> xmv_11 | 0.3662 | 0.5812 | 0.2884 | 0.0000 | 0.0000 | 1.0 |
| xmeas_02 -> xmv_11 | xmeas_02 -> xmv_11 | 0.2520 | 0.4853 | 0.3128 | 0.0000 | 0.0000 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.2213 | 0.5728 | 0.4169 | 0.0000 | 0.0000 | 1.0 |
| xmv_08 -> xmv_10 | xmv_08 -> xmv_10 | 0.1907 | 0.4625 | 0.3200 | 0.0000 | 0.0000 | 1.0 |

