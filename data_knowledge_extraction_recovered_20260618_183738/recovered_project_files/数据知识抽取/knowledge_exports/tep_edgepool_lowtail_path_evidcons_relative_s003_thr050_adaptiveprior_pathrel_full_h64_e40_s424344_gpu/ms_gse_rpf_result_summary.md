# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-evid-cons-s0.03-thr0.50-t0.05-relative+prior-cover@0.20+alg-prior-edge_pool-k8-g3-lag3-vote2-sv0.55-vb0.15-pool2.0-rank0.35@0.05+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6304 +/- 0.0029 | 0.6445 +/- 0.0045 | 0.0351 | 0.0351 | 0.0409 | 0.0476 | 0.7895 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9807.3 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_10 -> xmeas_19 | xmeas_10 -> xmeas_19 | 0.3213 | 0.6155 | 0.3977 | 0.0000 | 0.0169 | 1.0 |
| xmeas_14 -> xmv_09 | xmeas_14 -> xmv_09 | 0.3061 | 0.6730 | 0.4114 | 0.0000 | 0.0018 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2859 | 0.6753 | 0.0643 | 0.1449 | 0.0710 | 1.0 |
| xmeas_23 -> xmeas_10 | xmeas_23 -> xmeas_10 | 0.2509 | 0.7589 | 0.4400 | 0.0000 | 0.0268 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2241 | 0.7620 | 0.5912 | 0.0000 | 0.0775 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.4253 | 0.7059 | 0.4384 | 0.1692 | 0.0849 | 1.0 |
| xmv_09 -> xmv_03 | xmv_09 -> xmv_03 | 0.2634 | 0.6355 | 0.3927 | 0.0000 | 0.0595 | 1.0 |
| xmeas_35 -> xmv_10 | xmeas_35 -> xmv_10 | 0.2590 | 0.5993 | 0.4529 | 0.0000 | 0.0647 | 1.0 |
| xmeas_09 -> xmeas_01 | xmeas_09 -> xmeas_01 | 0.2561 | 0.6060 | 0.5389 | 0.0000 | 0.0544 | 1.0 |
| xmeas_10 -> xmeas_25 | xmeas_10 -> xmeas_25 | 0.2230 | 0.4999 | 0.5766 | 0.0000 | 0.0290 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4773 | 0.7423 | 0.3484 | 0.1478 | 0.0697 | 1.0 |
| xmeas_08 -> xmv_10 | xmeas_08 -> xmv_10 | 0.4343 | 0.7712 | 0.3432 | 0.0000 | 0.0282 | 1.0 |
| xmeas_06 -> xmv_10 | xmeas_06 -> xmv_10 | 0.3447 | 0.7237 | 0.3544 | 0.0000 | 0.0296 | 1.0 |
| xmeas_01 -> xmv_10 | xmeas_01 -> xmv_10 | 0.3343 | 0.6332 | 0.4399 | 0.0000 | 0.0335 | 1.0 |
| xmeas_33 -> xmeas_09 | xmeas_33 -> xmeas_09 | 0.3143 | 0.7221 | 0.4485 | 0.0000 | 0.0449 | 1.0 |

