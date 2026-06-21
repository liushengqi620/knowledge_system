# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+learned-path-admit-s0.20-reg0.020+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-k8-edge4+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6117 +/- 0.0000 | 0.6300 +/- 0.0000 | n/a | n/a | 0.0925 | 0.3864 | 0.8176 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11811.4 | 175320 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.3228 | 0.7050 | 0.0949 | 0.2384 | 0.9656 | 1.0 |
| xmv_01 -> xmeas_13 | xmv_01 -> xmeas_13 | 0.2753 | 0.6981 | 0.5250 | 0.0000 | 0.6696 | 1.0 |
| xmeas_22 -> xmv_05 | xmeas_22 -> xmv_05 | 0.2692 | 0.6932 | 0.4034 | 0.0000 | 0.9973 | 1.0 |
| xmeas_31 -> xmv_05 | xmeas_31 -> xmv_05 | 0.2146 | 0.6967 | 0.4188 | 0.0000 | 0.8346 | 1.0 |
| xmeas_10 -> xmeas_18 | xmeas_10 -> xmeas_18 | 0.2098 | 0.7074 | 0.8629 | 0.0000 | 0.9513 | 1.0 |

