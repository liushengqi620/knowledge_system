# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | default | 1 | 0.6054 +/- 0.0000 | 0.6211 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.6947 | 0.4178 | 0.00 | 0.00 | 0.00 | 0.0000 | on | 902.7 | 55412 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_08 -> xmv_10 | xmv_08 -> xmv_10 | 0.3132 | 0.6781 | 0.2975 | 0.0000 | 0.0000 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.2726 | 0.7308 | 0.3825 | 0.0000 | 0.0000 | 1.0 |
| xmeas_24 -> xmv_10 | xmeas_24 -> xmv_10 | 0.2696 | 0.7500 | 0.4132 | 0.0000 | 0.0000 | 1.0 |
| xmeas_41 -> xmv_10 | xmeas_41 -> xmv_10 | 0.2191 | 0.6117 | 0.4322 | 0.0000 | 0.0000 | 1.0 |
| xmeas_20 -> xmeas_34 | xmeas_20 -> xmeas_34 | 0.2071 | 0.4070 | 0.3558 | 0.0000 | 0.0000 | 1.0 |

