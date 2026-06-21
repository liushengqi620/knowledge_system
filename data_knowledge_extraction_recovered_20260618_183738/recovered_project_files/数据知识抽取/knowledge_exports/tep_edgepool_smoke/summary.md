# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_pool-k12-g3-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.0273 +/- 0.0000 | 0.0569 +/- 0.0000 | n/a | n/a | 0.2094 | 0.1784 | 0.2101 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12539.4 | 24513 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_16 -> xmv_05 | xmeas_16 -> xmv_05 | 0.1856 | 0.5862 | 0.1611 | 0.0000 | 0.3394 | 1.0 |
| xmv_03 -> xmeas_18 | xmv_03 -> xmeas_18 | 0.1634 | 0.5504 | 0.1609 | 0.0000 | 0.2454 | 1.0 |
| xmeas_07 -> xmv_05 | xmeas_07 -> xmv_05 | 0.1543 | 0.5660 | 0.1599 | 0.0000 | 0.3229 | 1.0 |
| xmeas_40 -> xmv_04 | xmeas_40 -> xmv_04 | 0.1496 | 0.5427 | 0.1664 | 0.0000 | 0.1661 | 1.0 |
| xmeas_16 -> xmeas_28 | xmeas_16 -> xmeas_28 | 0.1374 | 0.5892 | 0.1604 | 0.0000 | 0.2702 | 1.0 |

