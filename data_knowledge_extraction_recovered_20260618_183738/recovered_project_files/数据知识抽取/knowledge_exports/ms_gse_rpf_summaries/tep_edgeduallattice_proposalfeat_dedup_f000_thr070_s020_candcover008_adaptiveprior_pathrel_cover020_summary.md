# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.70-t0.08-relative_evidence-s0.20-proposal_feature+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+prior-cover@0.20+candidate-cover@0.08+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@1.00@8+path-aux@0.05+router@0.05 | 3 | 0.6365 +/- 0.0018 | 0.6480 +/- 0.0020 | 0.0351 | 0.0351 | 0.0909 | 0.3727 | 0.7662 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 5679.5 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4577 | 0.8939 | 0.2859 | 0.6091 | 0.7313 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3088 | 0.7600 | 0.1175 | 0.6475 | 0.8957 | 1.0 |
| xmeas_11 -> xmv_05 | xmeas_11 -> xmv_05 | 0.2906 | 0.8183 | 0.3607 | 0.0000 | 0.8729 | 1.0 |
| xmeas_06 -> xmeas_10 | xmeas_06 -> xmeas_10 | 0.2733 | 0.6365 | 0.5852 | 0.0000 | 0.1909 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2316 | 0.5478 | 0.2437 | 0.3797 | 0.2730 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3044 | 0.6248 | 0.1590 | 0.6037 | 0.6209 | 1.0 |
| xmeas_30 -> xmv_03 | xmeas_30 -> xmv_03 | 0.2948 | 0.7143 | 0.6590 | 0.0000 | 0.6246 | 1.0 |
| xmv_09 -> xmv_03 | xmv_09 -> xmv_03 | 0.2768 | 0.7022 | 0.0573 | 0.0268 | 0.6385 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.2732 | 0.7406 | 0.0556 | 0.5154 | 0.6229 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.2407 | 0.6412 | 0.1784 | 0.1090 | 0.9128 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3234 | 0.7866 | 0.5479 | 0.6524 | 0.8259 | 1.0 |
| xmeas_20 -> xmeas_38 | xmeas_20 -> xmeas_38 | 0.2301 | 0.5213 | 0.0949 | 0.4060 | 0.4906 | 1.0 |
| xmeas_24 -> xmeas_07 | xmeas_24 -> xmeas_07 | 0.2032 | 0.3413 | 0.5354 | 0.0000 | 0.0801 | 1.0 |
| xmeas_20 -> xmeas_29 | xmeas_20 -> xmeas_29 | 0.1971 | 0.4801 | 0.0722 | 0.5150 | 0.6030 | 1.0 |
| xmv_10 -> xmeas_19 | xmv_10 -> xmeas_19 | 0.1960 | 0.6983 | 0.8397 | 0.0000 | 0.7012 | 1.0 |

