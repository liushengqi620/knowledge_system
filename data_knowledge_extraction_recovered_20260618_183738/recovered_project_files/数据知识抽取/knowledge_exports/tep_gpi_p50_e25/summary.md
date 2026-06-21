# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard | 1 | 0.6140 +/- 0.0000 | 0.6250 +/- 0.0000 | n/a | n/a | 0.0000 | 0.0000 | 0.7214 | 0.0000 | 0.00 | 0.00 | 0.0000 | on | 585.5 | 53138 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_04 -> xmv_09 | xmeas_04 -> xmv_09 | 0.2875 | 0.4763 | 0.3376 | 0.0000 | 0.0000 | 1.0 |
| xmv_05 -> xmv_11 | xmv_05 -> xmv_11 | 0.2066 | 0.6759 | 0.2414 | 0.0000 | 0.0000 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.1866 | 0.7650 | 0.3406 | 0.0000 | 0.0000 | 1.0 |
| xmeas_26 -> xmv_09 | xmeas_26 -> xmv_09 | 0.1806 | 0.4759 | 0.2637 | 0.0000 | 0.0000 | 1.0 |
| xmv_03 -> xmv_09 | xmv_03 -> xmv_09 | 0.1765 | 0.4208 | 0.2351 | 0.0000 | 0.0000 | 1.0 |

