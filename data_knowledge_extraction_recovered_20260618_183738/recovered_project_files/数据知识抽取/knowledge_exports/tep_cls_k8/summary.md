# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6167 +/- 0.0000 | 0.6282 +/- 0.0000 | n/a | n/a | 0.0000 | 0.3037 | 0.7680 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 762.9 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_11 -> xmeas_21 | xmv_11 -> xmeas_21 | 0.4789 | 0.8704 | 0.4104 | 0.0000 | 0.3863 | 1.0 |
| xmv_10 -> xmeas_38 | xmv_10 -> xmeas_38 | 0.4067 | 0.8445 | 0.2893 | 0.0000 | 0.6042 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.3625 | 0.7004 | 0.2842 | 0.0000 | 0.9576 | 1.0 |
| xmv_10 -> xmeas_21 | xmv_10 -> xmeas_21 | 0.3145 | 0.8206 | 0.2610 | 0.0000 | 0.2816 | 1.0 |
| xmv_11 -> xmeas_11 | xmv_11 -> xmeas_11 | 0.2695 | 0.8208 | 0.2722 | 0.0000 | 0.5592 | 1.0 |

