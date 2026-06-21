# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.70-t0.08-relative_evidence-s0.20-proposal_feature-minsup0.50+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+prior-cover@0.20+candidate-cover@0.08+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@1.00@8+path-aux@0.05+router@0.05 | 3 | 0.6375 +/- 0.0044 | 0.6483 +/- 0.0065 | 0.0351 | 0.0351 | 0.0880 | 0.3596 | 0.8004 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 6754.8 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4139 | 0.8298 | 0.2388 | 0.6153 | 0.7492 | 1.0 |
| xmeas_35 -> xmeas_10 | xmeas_35 -> xmeas_10 | 0.3815 | 0.6091 | 0.3466 | 0.0000 | 0.7712 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3395 | 0.6866 | 0.0886 | 0.6361 | 0.8775 | 1.0 |
| xmv_10 -> xmeas_02 | xmv_10 -> xmeas_02 | 0.2692 | 0.5442 | 0.5910 | 0.0000 | 0.1668 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2448 | 0.6820 | 0.4496 | 0.6480 | 0.6838 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3130 | 0.6599 | 0.1840 | 0.6358 | 0.6748 | 1.0 |
| xmv_09 -> xmv_03 | xmv_09 -> xmv_03 | 0.2869 | 0.7405 | 0.0617 | 0.0298 | 0.6472 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.2728 | 0.7590 | 0.0529 | 0.5144 | 0.6213 | 1.0 |
| xmeas_40 -> xmv_03 | xmeas_40 -> xmv_03 | 0.2549 | 0.8022 | 0.3903 | 0.0000 | 0.6391 | 1.0 |
| xmeas_30 -> xmv_03 | xmeas_30 -> xmv_03 | 0.2264 | 0.7117 | 0.6002 | 0.0000 | 0.6005 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4394 | 0.8242 | 0.3205 | 0.6464 | 0.8158 | 1.0 |
| xmeas_03 -> xmeas_24 | xmeas_03 -> xmeas_24 | 0.3221 | 0.5690 | 0.4559 | 0.0000 | 0.0261 | 1.0 |
| xmeas_15 -> xmv_05 | xmeas_15 -> xmv_05 | 0.2106 | 0.7168 | 0.0960 | 0.0113 | 0.9383 | 1.0 |
| xmeas_28 -> xmeas_08 | xmeas_28 -> xmeas_08 | 0.2084 | 0.7184 | 0.5542 | 0.0000 | 0.1681 | 1.0 |
| xmeas_27 -> xmeas_39 | xmeas_27 -> xmeas_39 | 0.2044 | 0.2215 | 0.6182 | 0.0000 | 0.1206 | 1.0 |

