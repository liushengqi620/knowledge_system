# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+graph-core-cert-k8-g3-f0.05-thr0.35-t0.05-d1.00-grp0.40-stab0.50-p0.20+prior-cover@0.10+alg-prior-edge_lattice-k8-g3-lag3-vote2-sv0.45-vb0.12-pool3.0-rank0.30@0.04+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6304 +/- 0.0116 | 0.6439 +/- 0.0084 | 0.0000 | 0.0000 | 0.0219 | 0.0490 | 0.8306 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10782.3 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmeas_19 | xmeas_37 -> xmeas_19 | 0.4932 | 0.7246 | 0.4185 | 0.0000 | 0.0036 | 1.0 |
| xmeas_20 -> xmeas_11 | xmeas_20 -> xmeas_11 | 0.3189 | 0.6846 | 0.4017 | 0.0000 | 0.0587 | 1.0 |
| xmeas_25 -> xmv_05 | xmeas_25 -> xmv_05 | 0.2477 | 0.5417 | 0.3934 | 0.0000 | 0.0628 | 1.0 |
| xmv_10 -> xmeas_13 | xmv_10 -> xmeas_13 | 0.2455 | 0.7595 | 0.3411 | 0.0000 | 0.0324 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2328 | 0.6323 | 0.4189 | 0.1549 | 0.0673 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_13 -> xmeas_18 | xmeas_13 -> xmeas_18 | 0.3557 | 0.6259 | 0.4674 | 0.0000 | 0.0603 | 1.0 |
| xmeas_15 -> xmv_10 | xmeas_15 -> xmv_10 | 0.3318 | 0.5840 | 0.4466 | 0.0000 | 0.0230 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.3018 | 0.6454 | 0.4396 | 0.0000 | 0.0633 | 1.0 |
| xmeas_35 -> xmv_10 | xmeas_35 -> xmv_10 | 0.3013 | 0.5664 | 0.3300 | 0.0000 | 0.0309 | 1.0 |
| xmeas_06 -> xmv_03 | xmeas_06 -> xmv_03 | 0.3004 | 0.6758 | 0.5533 | 0.0000 | 0.0405 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_39 -> xmv_05 | xmeas_39 -> xmv_05 | 0.5504 | 0.5657 | 0.4066 | 0.0000 | 0.0728 | 1.0 |
| xmv_01 -> xmv_10 | xmv_01 -> xmv_10 | 0.4868 | 0.7001 | 0.4973 | 0.0000 | 0.0281 | 1.0 |
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.4683 | 0.6739 | 0.3566 | 0.0000 | 0.0054 | 1.0 |
| xmeas_30 -> xmv_05 | xmeas_30 -> xmv_05 | 0.3908 | 0.5177 | 0.3322 | 0.0000 | 0.0736 | 1.0 |
| xmeas_24 -> xmeas_09 | xmeas_24 -> xmeas_09 | 0.3174 | 0.6382 | 0.4577 | 0.0000 | 0.0564 | 1.0 |

