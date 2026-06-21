# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+salience-class@0.00 | 1 | 0.6124 +/- 0.0000 | 0.6181 +/- 0.0000 | n/a | n/a | 0.0000 | 0.8044 | 0.6583 | 0.0000 | 0.00 | 0.00 | 0.0000 | on | 579.7 | 53202 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.7214 | 0.8210 | 0.2256 | 0.0000 | 0.8015 | 1.0 |
| xmeas_18 -> xmv_11 | xmeas_18 -> xmv_11 | 0.4913 | 0.7390 | 0.2733 | 0.0000 | 0.8015 | 1.0 |
| xmv_10 -> xmeas_38 | xmv_10 -> xmeas_38 | 0.4323 | 0.8307 | 0.2519 | 0.0000 | 0.8117 | 1.0 |
| xmv_10 -> xmeas_35 | xmv_10 -> xmeas_35 | 0.3611 | 0.8570 | 0.2108 | 0.0000 | 0.8117 | 1.0 |
| xmv_10 -> xmeas_39 | xmv_10 -> xmeas_39 | 0.3509 | 0.7303 | 0.2829 | 0.0000 | 0.8117 | 1.0 |

