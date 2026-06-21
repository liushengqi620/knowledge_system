# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard | 1 | 0.0125 +/- 0.0000 | 0.0575 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.1525 | 0.0000 | 0.00 | 0.00 | 0.0000 | on | 923.0 | 22498 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmeas_07 | xmeas_09 -> xmeas_07 | 0.0602 | 0.4936 | 0.1514 | 0.0000 | 0.0000 | 1.0 |
| xmeas_22 -> xmeas_07 | xmeas_22 -> xmeas_07 | 0.0575 | 0.5145 | 0.1638 | 0.0000 | 0.0000 | 1.0 |
| xmeas_18 -> xmeas_01 | xmeas_18 -> xmeas_01 | 0.0566 | 0.4862 | 0.1486 | 0.0000 | 0.0000 | 1.0 |
| xmv_07 -> xmeas_36 | xmv_07 -> xmeas_36 | 0.0553 | 0.5258 | 0.1490 | 0.0000 | 0.0000 | 1.0 |
| xmeas_18 -> xmeas_37 | xmeas_18 -> xmeas_37 | 0.0548 | 0.4970 | 0.1550 | 0.0000 | 0.0000 | 1.0 |

