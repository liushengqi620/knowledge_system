# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.20-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.60-t0.08-relative_evidence-s0.25-coverage_feature+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+prior-cover@0.15+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.45-vb0.12-gb6.0-pool3.0-rank0.35@0.05+class-evidence-focus-low_train_separation6@1.00@10+path-aux@0.05+router@0.05 | 3 | 0.6237 +/- 0.0071 | 0.6322 +/- 0.0082 | 0.0721 | 0.0721 | 0.0828 | 0.3909 | 0.8090 | 1.0000 | 0.3716 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7094.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3488 | 0.7310 | 0.2378 | 0.4626 | 0.2461 | 1.0 |
| xmeas_34 -> xmeas_19 | xmeas_34 -> xmeas_19 | 0.2940 | 0.7353 | 0.1046 | 0.4221 | 0.8447 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2592 | 0.9218 | 0.1801 | 0.6659 | 0.8333 | 1.0 |
| xmv_02 -> xmv_05 | xmv_02 -> xmv_05 | 0.2397 | 0.7540 | 0.1385 | 0.1541 | 0.9822 | 1.0 |
| xmeas_13 -> xmeas_11 | xmeas_13 -> xmeas_11 | 0.2172 | 0.8011 | 0.0769 | 0.7015 | 0.7161 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.4084 | 0.7325 | 0.1456 | 0.5824 | 0.7576 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2892 | 0.8048 | 0.0915 | 0.7377 | 0.9722 | 1.0 |
| xmeas_35 -> xmv_10 | xmeas_35 -> xmv_10 | 0.2779 | 0.7317 | 0.4522 | 0.0000 | 0.8454 | 1.0 |
| xmeas_24 -> xmeas_23 | xmeas_24 -> xmeas_23 | 0.2087 | 0.6679 | 0.5858 | 0.0000 | 0.8041 | 1.0 |
| xmeas_06 -> xmeas_25 | xmeas_06 -> xmeas_25 | 0.1973 | 0.4321 | 0.6370 | 0.0000 | 0.3258 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_10 -> xmeas_39 | xmeas_10 -> xmeas_39 | 0.2517 | 0.7195 | 0.1745 | 0.3838 | 0.7267 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2272 | 0.7360 | 0.3230 | 0.6583 | 0.8382 | 1.0 |
| xmeas_14 -> xmeas_09 | xmeas_14 -> xmeas_09 | 0.2097 | 0.2455 | 0.3992 | 0.1688 | 0.3382 | 1.0 |
| xmeas_03 -> xmeas_09 | xmeas_03 -> xmeas_09 | 0.1830 | 0.3972 | 0.4625 | 0.0723 | 0.5339 | 1.0 |
| xmeas_11 -> xmeas_13 | xmeas_11 -> xmeas_13 | 0.1827 | 0.6844 | 0.0825 | 0.6987 | 0.7470 | 1.0 |

