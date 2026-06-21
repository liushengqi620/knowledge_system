# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert_llm@0.00 | group_pair_inclusive+dedup-hard+prior-cover@0.05+prior-cal@0.10+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6216 +/- 0.0000 | 0.6282 +/- 0.0000 | n/a | n/a | 0.0273 | 0.3077 | 0.7440 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 790.6 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert_llm@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_18 | xmv_10 -> xmeas_18 | 0.2984 | 0.8127 | 0.3062 | 0.0000 | 0.6018 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.2852 | 0.8604 | 0.2812 | 0.0000 | 0.3160 | 1.0 |
| xmeas_18 -> xmeas_13 | xmeas_18 -> xmeas_13 | 0.2323 | 0.4907 | 0.2796 | 0.0000 | 0.6812 | 1.0 |
| xmv_11 -> xmeas_11 | xmv_11 -> xmeas_11 | 0.2162 | 0.8100 | 0.3440 | 0.5654 | 0.5129 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.2138 | 0.6316 | 0.2672 | 0.0000 | 0.9608 | 1.0 |

