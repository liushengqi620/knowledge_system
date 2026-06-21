# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+class-prior-admit-f0.20-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.60-t0.08-relative_evidence-s0.25-coverage_feature+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+prior-cover@0.15+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.45-vb0.12-gb6.0-pool3.0-rank0.35@0.05+class-evidence-focus-low_train_separation6@1.00@10+path-aux@0.05+router@0.05 | 3 | 0.6341 +/- 0.0022 | 0.6454 +/- 0.0043 | 0.0175 | 0.0175 | 0.0756 | 0.3636 | 0.8171 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 5678.5 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_15 -> xmv_07 | xmeas_15 -> xmv_07 | 0.4610 | 0.5330 | 0.5748 | 0.0000 | 0.0037 | 1.0 |
| xmeas_08 -> xmeas_20 | xmeas_08 -> xmeas_20 | 0.2377 | 0.6996 | 0.3730 | 0.0000 | 0.5634 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2319 | 0.6990 | 0.0456 | 0.5713 | 0.6691 | 1.0 |
| xmv_09 -> xmv_06 | xmv_09 -> xmv_06 | 0.2165 | 0.8083 | 0.3267 | 0.0000 | 0.1049 | 1.0 |
| xmeas_12 -> xmeas_08 | xmeas_12 -> xmeas_08 | 0.2141 | 0.4076 | 0.3780 | 0.0000 | 0.3049 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4371 | 0.7078 | 0.4172 | 0.4966 | 0.6205 | 1.0 |
| xmeas_20 -> xmv_03 | xmeas_20 -> xmv_03 | 0.3662 | 0.6889 | 0.3551 | 0.0000 | 0.6331 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.3616 | 0.6927 | 0.0588 | 0.5270 | 0.6126 | 1.0 |
| xmeas_33 -> xmeas_01 | xmeas_33 -> xmeas_01 | 0.3290 | 0.7219 | 0.3576 | 0.0000 | 0.9606 | 1.0 |
| xmeas_09 -> xmeas_01 | xmeas_09 -> xmeas_01 | 0.3237 | 0.5774 | 0.2609 | 0.2407 | 0.8087 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3278 | 0.7876 | 0.3370 | 0.6593 | 0.8400 | 1.0 |
| xmeas_27 -> xmv_05 | xmeas_27 -> xmv_05 | 0.3216 | 0.6131 | 0.1516 | 0.1812 | 0.9933 | 1.0 |
| xmeas_41 -> xmeas_01 | xmeas_41 -> xmeas_01 | 0.3125 | 0.5366 | 0.4183 | 0.0000 | 0.4067 | 1.0 |
| xmeas_01 -> xmeas_18 | xmeas_01 -> xmeas_18 | 0.2769 | 0.5761 | 0.3827 | 0.0000 | 0.4650 | 1.0 |
| xmeas_16 -> xmeas_07 | xmeas_16 -> xmeas_07 | 0.2514 | 0.7301 | 0.1274 | 0.5156 | 0.4018 | 1.0 |

