# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.50-w0.50-lag3@0.50-path-off-edge4+stable-class-edge-overlay-max-s0.25-k8-g2-fw1.25-nw0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@1.00@8+path-aux@0.05+router@0.05 | 3 | 0.6344 +/- 0.0032 | 0.6436 +/- 0.0056 | 0.0175 | 0.0175 | 0.0870 | 0.3400 | 0.7890 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11651.8 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4440 | 0.8655 | 0.0665 | 0.5588 | 0.8926 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4422 | 0.8790 | 0.1939 | 0.6512 | 0.7628 | 1.0 |
| xmeas_20 -> xmeas_19 | xmeas_20 -> xmeas_19 | 0.3173 | 0.3838 | 0.3597 | 0.0000 | 0.0218 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2959 | 0.4445 | 0.2867 | 0.3571 | 0.2585 | 1.0 |
| xmeas_22 -> xmv_02 | xmeas_22 -> xmv_02 | 0.2659 | 0.8206 | 0.3506 | 0.0000 | 0.9234 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4286 | 0.7508 | 0.4412 | 0.4903 | 0.6087 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.3549 | 0.7395 | 0.0630 | 0.1625 | 0.6473 | 1.0 |
| xmeas_20 -> xmeas_01 | xmeas_20 -> xmeas_01 | 0.3359 | 0.7768 | 0.4211 | 0.0000 | 0.9686 | 1.0 |
| xmeas_29 -> xmv_03 | xmeas_29 -> xmv_03 | 0.2902 | 0.6222 | 0.0691 | 0.4685 | 0.6746 | 1.0 |
| xmeas_23 -> xmeas_01 | xmeas_23 -> xmeas_01 | 0.2869 | 0.7654 | 0.4157 | 0.0000 | 0.9570 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2952 | 0.7554 | 0.0876 | 0.5785 | 0.8385 | 1.0 |
| xmeas_02 -> xmeas_29 | xmeas_02 -> xmeas_29 | 0.2408 | 0.4583 | 0.4059 | 0.0000 | 0.0270 | 1.0 |
| xmeas_20 -> xmeas_23 | xmeas_20 -> xmeas_23 | 0.2239 | 0.6913 | 0.1176 | 0.4794 | 0.5431 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2200 | 0.7264 | 0.2598 | 0.2044 | 0.7749 | 1.0 |
| xmeas_24 -> xmeas_07 | xmeas_24 -> xmeas_07 | 0.2142 | 0.5521 | 0.3603 | 0.0000 | 0.0699 | 1.0 |

