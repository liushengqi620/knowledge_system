# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-k8-edge4+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6384 +/- 0.0000 | 0.6513 +/- 0.0000 | n/a | n/a | 0.0849 | 0.3214 | 0.7322 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9959.0 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3912 | 0.9017 | 0.2509 | 0.6440 | 0.7476 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3253 | 0.8888 | 0.0319 | 0.5609 | 0.8966 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2821 | 0.8757 | 0.3959 | 0.0000 | 0.1813 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2510 | 0.5688 | 0.2329 | 0.3726 | 0.3520 | 1.0 |
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.2451 | 0.8629 | 0.5426 | 0.0000 | 0.1696 | 1.0 |

