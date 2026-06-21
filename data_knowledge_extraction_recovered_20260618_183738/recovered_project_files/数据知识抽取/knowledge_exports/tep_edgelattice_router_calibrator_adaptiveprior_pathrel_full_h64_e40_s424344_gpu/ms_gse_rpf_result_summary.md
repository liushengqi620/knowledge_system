# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+edge-family-router-t0.85-f0.10-b0.85-bal0.005+prior-cover@0.20+edge-cal-f0.10-b1.5-reg0.01+alg-prior-edge_lattice-k10-g4-lag3-vote2-sv0.50-vb0.12-pool3.0-rank0.30@0.03+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6300 +/- 0.0015 | 0.6443 +/- 0.0013 | 0.0175 | 0.0175 | 0.0428 | 0.0490 | 0.7984 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9264.3 | 167065 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4150 | 0.8182 | 0.7659 | 0.1451 | 0.0543 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.3196 | 0.7860 | 0.7818 | 0.0000 | 0.0267 | 1.0 |
| xmeas_21 -> xmv_10 | xmeas_21 -> xmv_10 | 0.3140 | 0.8155 | 0.5706 | 0.0000 | 0.0287 | 1.0 |
| xmeas_23 -> xmeas_04 | xmeas_23 -> xmeas_04 | 0.2874 | 0.8148 | 0.3998 | 0.0000 | 0.0539 | 1.0 |
| xmv_05 -> xmeas_10 | xmv_05 -> xmeas_10 | 0.2530 | 0.8873 | 0.4645 | 0.0000 | 0.0719 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.5069 | 0.7627 | 0.2648 | 0.1458 | 0.0525 | 1.0 |
| xmv_11 -> xmeas_25 | xmv_11 -> xmeas_25 | 0.3917 | 0.6882 | 0.1781 | 0.1867 | 0.0337 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.3442 | 0.6900 | 0.1885 | 0.1626 | 0.0325 | 1.0 |
| xmv_01 -> xmv_11 | xmv_01 -> xmv_11 | 0.3287 | 0.6465 | 0.2662 | 0.1707 | 0.0314 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3276 | 0.4785 | 0.3299 | 0.2211 | 0.0832 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.4201 | 0.7668 | 0.1507 | 0.1459 | 0.0715 | 1.0 |
| xmeas_41 -> xmeas_25 | xmeas_41 -> xmeas_25 | 0.2848 | 0.7146 | 0.4795 | 0.0000 | 0.0010 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2830 | 0.6035 | 0.3150 | 0.2527 | 0.1263 | 1.0 |
| xmeas_12 -> xmv_05 | xmeas_12 -> xmv_05 | 0.2363 | 0.5936 | 0.6201 | 0.0000 | 0.0685 | 1.0 |
| xmeas_19 -> xmeas_34 | xmeas_19 -> xmeas_34 | 0.2161 | 0.6821 | 0.4057 | 0.0000 | 0.0602 | 1.0 |

