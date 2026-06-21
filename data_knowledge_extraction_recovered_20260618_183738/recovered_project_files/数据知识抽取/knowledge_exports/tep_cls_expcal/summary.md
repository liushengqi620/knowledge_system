# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert@0.00 | group_pair_inclusive+dedup-hard+prior-cover@0.05+prior-cal@0.10+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6136 +/- 0.0000 | 0.6266 +/- 0.0000 | n/a | n/a | 0.0287 | 0.3108 | 0.7471 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 647.5 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.3858 | 0.7693 | 0.2657 | 0.0000 | 0.9710 | 1.0 |
| xmv_10 -> xmeas_18 | xmv_10 -> xmeas_18 | 0.3838 | 0.8186 | 0.2725 | 0.0000 | 0.6400 | 1.0 |
| xmv_10 -> xmeas_19 | xmv_10 -> xmeas_19 | 0.3091 | 0.7898 | 0.2526 | 0.0000 | 0.5991 | 1.0 |
| xmv_11 -> xmeas_11 | xmv_11 -> xmeas_11 | 0.2951 | 0.8638 | 0.3439 | 0.5654 | 0.5205 | 1.0 |
| xmeas_38 -> xmv_10 | xmeas_38 -> xmv_10 | 0.2749 | 0.7253 | 0.3177 | 0.0000 | 0.6788 | 1.0 |

