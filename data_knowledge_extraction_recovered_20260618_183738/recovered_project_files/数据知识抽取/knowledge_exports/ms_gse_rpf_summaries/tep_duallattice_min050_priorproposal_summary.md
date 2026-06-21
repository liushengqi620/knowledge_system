# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+salience-class@0.00+class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.70-t0.08-relative_evidence-s0.20-proposal_feature-minsup0.50+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.50-thr0.02-t0.05-f0.25-prior+prior-cover@0.20+candidate-cover@0.08+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@8+path-aux@0.05+router@0.05 | 3 | 0.6343 +/- 0.0079 | 0.6464 +/- 0.0100 | 0.0546 | 0.0546 | 0.0459 | 0.7892 | 0.7886 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 5673.3 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3953 | 0.8244 | 0.2579 | 0.2385 | 0.7837 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3140 | 0.5805 | 0.2399 | 0.2680 | 0.8025 | 1.0 |
| xmeas_01 -> xmv_10 | xmeas_01 -> xmv_10 | 0.2409 | 0.7080 | 0.5587 | 0.0000 | 0.8733 | 1.0 |
| xmeas_01 -> xmeas_07 | xmeas_01 -> xmeas_07 | 0.2131 | 0.6676 | 0.6500 | 0.0000 | 0.8733 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2091 | 0.5324 | 0.3354 | 0.1533 | 0.7837 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.4684 | 0.6494 | 0.3263 | 0.1824 | 0.8050 | 1.0 |
| xmv_05 -> xmv_03 | xmv_05 -> xmv_03 | 0.3016 | 0.6469 | 0.0302 | 0.0933 | 0.9905 | 1.0 |
| xmeas_19 -> xmv_03 | xmeas_19 -> xmv_03 | 0.2342 | 0.7557 | 0.5968 | 0.0000 | 0.9905 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2264 | 0.6264 | 0.1414 | 0.1362 | 0.8050 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.2103 | 0.5749 | 0.1018 | 0.1150 | 0.9905 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmeas_27 | xmeas_30 -> xmeas_27 | 0.2989 | 0.4925 | 0.3756 | 0.0000 | 0.5848 | 1.0 |
| xmeas_33 -> xmeas_35 | xmeas_33 -> xmeas_35 | 0.2813 | 0.7710 | 0.3341 | 0.0000 | 0.8008 | 1.0 |
| xmv_06 -> xmeas_35 | xmv_06 -> xmeas_35 | 0.2411 | 0.5717 | 0.3999 | 0.0000 | 0.9157 | 1.0 |
| xmeas_28 -> xmeas_23 | xmeas_28 -> xmeas_23 | 0.1752 | 0.6559 | 0.3667 | 0.0000 | 0.8981 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.1732 | 0.5723 | 0.3747 | 0.1750 | 0.8172 | 1.0 |

