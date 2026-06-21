# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w1.00-lag3@0.50-k8-edge4-class-filter0.25+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6319 +/- 0.0000 | 0.6476 +/- 0.0000 | n/a | n/a | 0.0777 | 0.3827 | 0.7724 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10234.2 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmeas_28 | xmeas_18 -> xmeas_28 | 0.4019 | 0.8297 | 0.3400 | 0.0000 | 0.8989 | 1.0 |
| xmeas_38 -> xmv_09 | xmeas_38 -> xmv_09 | 0.3651 | 0.7653 | 0.3426 | 0.0000 | 0.8392 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3402 | 0.8998 | 0.1378 | 0.5401 | 1.0000 | 1.0 |
| xmeas_30 -> xmeas_19 | xmeas_30 -> xmeas_19 | 0.3183 | 0.5744 | 0.3715 | 0.0000 | 0.1710 | 1.0 |
| xmeas_19 -> xmeas_13 | xmeas_19 -> xmeas_13 | 0.2375 | 0.7206 | 0.3108 | 0.0000 | 0.1535 | 1.0 |

