# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.70-t0.08-relative_evidence-s0.20-proposal_feature+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+prior-cover@0.20+candidate-cover@0.04+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@1.00@8+path-aux@0.05+router@0.05 | 3 | 0.6334 +/- 0.0043 | 0.6448 +/- 0.0051 | 0.0175 | 0.0175 | 0.0789 | 0.3433 | 0.8257 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 5745.8 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3259 | 0.7231 | 0.2759 | 0.3992 | 0.8374 | 1.0 |
| xmeas_06 -> xmeas_10 | xmeas_06 -> xmeas_10 | 0.2681 | 0.7517 | 0.5740 | 0.0000 | 0.3413 | 1.0 |
| xmv_09 -> xmeas_03 | xmv_09 -> xmeas_03 | 0.2670 | 0.6926 | 0.0904 | 0.3145 | 0.5793 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2324 | 0.6837 | 0.4871 | 0.7257 | 0.7956 | 1.0 |
| xmeas_10 -> xmeas_19 | xmeas_10 -> xmeas_19 | 0.2236 | 0.7386 | 0.4820 | 0.0000 | 0.2230 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.4938 | 0.7772 | 0.2124 | 0.1188 | 0.9733 | 1.0 |
| xmeas_07 -> xmv_03 | xmeas_07 -> xmv_03 | 0.4131 | 0.7331 | 0.4061 | 0.0000 | 0.5999 | 1.0 |
| xmeas_08 -> xmeas_31 | xmeas_08 -> xmeas_31 | 0.4095 | 0.7753 | 0.4706 | 0.0000 | 0.6558 | 1.0 |
| xmeas_40 -> xmv_03 | xmeas_40 -> xmv_03 | 0.3839 | 0.7701 | 0.4862 | 0.0000 | 0.5797 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.2915 | 0.7316 | 0.4525 | 0.0000 | 0.9772 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3699 | 0.7954 | 0.2085 | 0.6494 | 0.8228 | 1.0 |
| xmeas_22 -> xmeas_13 | xmeas_22 -> xmeas_13 | 0.2928 | 0.7065 | 0.1274 | 0.0665 | 0.7203 | 1.0 |
| xmeas_20 -> xmeas_38 | xmeas_20 -> xmeas_38 | 0.2693 | 0.5921 | 0.0879 | 0.4470 | 0.5525 | 1.0 |
| xmeas_27 -> xmv_05 | xmeas_27 -> xmv_05 | 0.2500 | 0.4951 | 0.0992 | 0.1272 | 0.9211 | 1.0 |
| xmv_06 -> xmeas_28 | xmv_06 -> xmeas_28 | 0.2290 | 0.7533 | 0.6179 | 0.0002 | 0.0549 | 1.0 |

