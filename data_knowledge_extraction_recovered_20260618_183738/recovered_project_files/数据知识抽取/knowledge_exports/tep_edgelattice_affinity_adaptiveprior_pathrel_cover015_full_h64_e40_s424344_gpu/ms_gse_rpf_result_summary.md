# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.15+alg-prior-edge_lattice-k8-g3-lag3-vote2-sv0.45-vb0.12-pool3.0-rank0.30@0.04+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6278 +/- 0.0044 | 0.6412 +/- 0.0010 | 0.0370 | 0.0370 | 0.0411 | 0.0491 | 0.8063 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10687.3 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.3474 | 0.6432 | 0.0880 | 0.4619 | 0.4038 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2780 | 0.7534 | 0.5358 | 0.0000 | 0.0248 | 1.0 |
| xmv_05 -> xmeas_21 | xmv_05 -> xmeas_21 | 0.2544 | 0.5974 | 0.3552 | 0.0000 | 0.0756 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2355 | 0.7544 | 0.3298 | 0.1852 | 0.0547 | 1.0 |
| xmv_02 -> xmv_05 | xmv_02 -> xmv_05 | 0.2217 | 0.6847 | 0.3467 | 0.0000 | 0.0643 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.3762 | 0.6545 | 0.2268 | 0.1512 | 0.0840 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3521 | 0.5611 | 0.6415 | 0.0000 | 0.0898 | 1.0 |
| xmeas_02 -> xmeas_25 | xmeas_02 -> xmeas_25 | 0.3483 | 0.6457 | 0.5400 | 0.0000 | 0.0121 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.2617 | 0.6463 | 0.5811 | 0.0000 | 0.0665 | 1.0 |
| xmv_09 -> xmeas_05 | xmv_09 -> xmeas_05 | 0.2596 | 0.6913 | 0.5723 | 0.0000 | 0.0054 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4946 | 0.7991 | 0.7167 | 0.1921 | 0.0693 | 1.0 |
| xmeas_24 -> xmeas_23 | xmeas_24 -> xmeas_23 | 0.3354 | 0.6395 | 0.4877 | 0.0000 | 0.0438 | 1.0 |
| xmeas_24 -> xmeas_04 | xmeas_24 -> xmeas_04 | 0.2914 | 0.5315 | 0.3636 | 0.0000 | 0.0129 | 1.0 |
| xmv_06 -> xmeas_10 | xmv_06 -> xmeas_10 | 0.2532 | 0.5775 | 0.2472 | 0.2076 | 0.0702 | 1.0 |
| xmeas_22 -> xmv_10 | xmeas_22 -> xmv_10 | 0.2076 | 0.5621 | 0.3405 | 0.0000 | 0.0524 | 1.0 |

