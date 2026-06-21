# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+class-evid-cert-focus_stability-f0.05-thr0.75-t0.05+prior-cover@0.20+alg-prior-edge_pool-k8-g3-lag3-vote2-sv0.55-vb0.15-pool2.0-rank0.35@0.05+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6263 +/- 0.0064 | 0.6418 +/- 0.0066 | 0.0175 | 0.0175 | 0.0402 | 0.0436 | 0.7763 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10884.3 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmeas_19 | xmeas_37 -> xmeas_19 | 0.2606 | 0.6740 | 0.4536 | 0.0000 | 0.0223 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2169 | 0.5506 | 0.1326 | 0.2692 | 0.1212 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2139 | 0.7054 | 0.6668 | 0.0000 | 0.0199 | 1.0 |
| xmeas_30 -> xmeas_19 | xmeas_30 -> xmeas_19 | 0.1990 | 0.4927 | 0.4092 | 0.0000 | 0.0434 | 1.0 |
| xmeas_10 -> xmeas_31 | xmeas_10 -> xmeas_31 | 0.1956 | 0.7675 | 0.5261 | 0.0000 | 0.0219 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3630 | 0.6876 | 0.3219 | 0.1653 | 0.0871 | 1.0 |
| xmeas_24 -> xmv_03 | xmeas_24 -> xmv_03 | 0.3352 | 0.7868 | 0.4819 | 0.0000 | 0.0404 | 1.0 |
| xmeas_06 -> xmv_03 | xmeas_06 -> xmv_03 | 0.3116 | 0.6691 | 0.4497 | 0.0000 | 0.0359 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.2935 | 0.7915 | 0.4341 | 0.0000 | 0.0667 | 1.0 |
| xmeas_41 -> xmeas_01 | xmeas_41 -> xmeas_01 | 0.2693 | 0.7829 | 0.4985 | 0.0000 | 0.0607 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_08 -> xmv_10 | xmeas_08 -> xmv_10 | 0.3634 | 0.8276 | 0.3342 | 0.0000 | 0.0287 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3467 | 0.7237 | 0.1462 | 0.1478 | 0.0696 | 1.0 |
| xmeas_33 -> xmeas_09 | xmeas_33 -> xmeas_09 | 0.3386 | 0.7551 | 0.3724 | 0.0000 | 0.0330 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3169 | 0.6553 | 0.1917 | 0.1619 | 0.0725 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.3138 | 0.6913 | 0.0978 | 0.3278 | 0.1585 | 1.0 |

