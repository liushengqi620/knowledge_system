# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-aux@0.05 | 1 | 0.6214 +/- 0.0000 | 0.6291 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.7714 | 0.0000 | 0.05 | 0.00 | 0.0000 | on | 583.8 | 53138 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_04 -> xmv_09 | xmeas_04 -> xmv_09 | 0.2875 | 0.6624 | 0.4629 | 0.0000 | 0.0000 | 1.0 |
| xmeas_33 -> xmv_09 | xmeas_33 -> xmv_09 | 0.2859 | 0.6489 | 0.2078 | 0.0000 | 0.0000 | 1.0 |
| xmeas_26 -> xmv_09 | xmeas_26 -> xmv_09 | 0.1851 | 0.6374 | 0.3569 | 0.0000 | 0.0000 | 1.0 |
| xmeas_11 -> xmv_10 | xmeas_11 -> xmv_10 | 0.1746 | 0.7535 | 0.2817 | 0.0000 | 0.0000 | 1.0 |
| xmeas_12 -> xmv_10 | xmeas_12 -> xmv_10 | 0.1730 | 0.6558 | 0.2465 | 0.0000 | 0.0000 | 1.0 |

