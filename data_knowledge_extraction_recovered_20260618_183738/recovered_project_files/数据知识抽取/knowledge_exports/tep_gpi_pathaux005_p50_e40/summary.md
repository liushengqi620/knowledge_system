# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-aux@0.05 | 1 | 0.6199 +/- 0.0000 | 0.6322 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.8727 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 765.4 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_07 -> xmv_10 | xmv_07 -> xmv_10 | 0.2630 | 0.7569 | 0.2561 | 0.0000 | 0.0000 | 1.0 |
| xmv_08 -> xmv_10 | xmv_08 -> xmv_10 | 0.2605 | 0.8580 | 0.3307 | 0.0000 | 0.0000 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.2304 | 0.7976 | 0.3958 | 0.0000 | 0.0000 | 1.0 |
| xmeas_40 -> xmv_11 | xmeas_40 -> xmv_11 | 0.2273 | 0.6348 | 0.2488 | 0.0000 | 0.0000 | 1.0 |
| xmv_05 -> xmeas_16 | xmv_05 -> xmeas_16 | 0.2022 | 0.4913 | 0.4691 | 0.0000 | 0.0000 | 1.0 |

