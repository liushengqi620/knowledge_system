# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.70-t0.08-relative_evidence-s0.20-proposal_feature-minsup0.70+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+prior-cover@0.20+candidate-cover@0.08+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@1.00@8+path-aux@0.05+router@0.05 | 3 | 0.6285 +/- 0.0052 | 0.6428 +/- 0.0031 | 0.0175 | 0.0175 | 0.0903 | 0.3588 | 0.7276 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 6790.3 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmeas_19 | xmeas_37 -> xmeas_19 | 0.3518 | 0.4670 | 0.4829 | 0.0000 | 0.0451 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.2715 | 0.7500 | 0.8754 | 0.0000 | 0.3337 | 1.0 |
| xmv_10 -> xmeas_02 | xmv_10 -> xmeas_02 | 0.2601 | 0.5693 | 0.6000 | 0.0000 | 0.1195 | 1.0 |
| xmv_10 -> xmeas_31 | xmv_10 -> xmeas_31 | 0.2431 | 0.6767 | 0.4130 | 0.0243 | 0.2529 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2245 | 0.8436 | 0.4866 | 0.6145 | 0.8385 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_09 -> xmeas_27 | xmv_09 -> xmeas_27 | 0.3378 | 0.6233 | 0.5968 | 0.0000 | 0.0422 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.2763 | 0.6568 | 0.1640 | 0.5034 | 0.6557 | 1.0 |
| xmeas_01 -> xmeas_23 | xmeas_01 -> xmeas_23 | 0.2473 | 0.7868 | 0.8336 | 0.0000 | 0.8632 | 1.0 |
| xmeas_01 -> xmv_05 | xmeas_01 -> xmv_05 | 0.2170 | 0.6074 | 0.0980 | 0.3759 | 0.8769 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.2155 | 0.7237 | 0.2213 | 0.1184 | 0.9670 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.5007 | 0.7651 | 0.5057 | 0.6210 | 0.7989 | 1.0 |
| xmeas_13 -> xmv_05 | xmeas_13 -> xmv_05 | 0.3205 | 0.3131 | 0.3271 | 0.0000 | 0.3644 | 1.0 |
| xmv_05 -> xmeas_23 | xmv_05 -> xmeas_23 | 0.2687 | 0.7466 | 0.0769 | 0.0881 | 0.7032 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2560 | 0.6358 | 0.2375 | 0.4934 | 0.3180 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2182 | 0.6616 | 0.2894 | 0.5336 | 0.7383 | 1.0 |

