# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+salience-class@0.00+class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.70-t0.08-relative_evidence-s0.20-proposal_feature-minsup0.50+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.00-thr0.02-t0.05-f0.25-prior-pstr0.50+prior-cover@0.20+candidate-cover@0.08+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@8+path-aux@0.05+router@0.05 | 3 | 0.6337 +/- 0.0019 | 0.6420 +/- 0.0022 | 0.0175 | 0.0175 | 0.0471 | 0.7813 | 0.7898 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 5573.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4145 | 0.8162 | 0.3178 | 0.2577 | 0.7837 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2672 | 0.7357 | 0.4158 | 0.0000 | 0.7837 | 1.0 |
| xmeas_38 -> xmv_09 | xmeas_38 -> xmv_09 | 0.2539 | 0.7373 | 0.3533 | 0.0000 | 0.7826 | 1.0 |
| xmeas_37 -> xmeas_18 | xmeas_37 -> xmeas_18 | 0.2270 | 0.8108 | 0.3956 | 0.0000 | 0.6650 | 1.0 |
| xmeas_38 -> xmeas_18 | xmeas_38 -> xmeas_18 | 0.2183 | 0.5956 | 0.3640 | 0.0000 | 0.6650 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_34 -> xmv_10 | xmeas_34 -> xmv_10 | 0.3152 | 0.6618 | 0.4549 | 0.0000 | 0.9050 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3076 | 0.6467 | 0.1394 | 0.1951 | 0.8050 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.2478 | 0.5269 | 0.2118 | 0.0222 | 0.8735 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2278 | 0.5905 | 0.2049 | 0.1683 | 0.8050 | 1.0 |
| xmeas_19 -> xmv_03 | xmeas_19 -> xmv_03 | 0.2255 | 0.5932 | 0.5602 | 0.0000 | 0.9905 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2494 | 0.7462 | 0.3320 | 0.1177 | 0.9903 | 1.0 |
| xmeas_02 -> xmv_05 | xmeas_02 -> xmv_05 | 0.2488 | 0.6945 | 0.3991 | 0.0000 | 0.7850 | 1.0 |
| xmeas_01 -> xmeas_35 | xmeas_01 -> xmeas_35 | 0.2266 | 0.7003 | 0.5353 | 0.0000 | 0.8782 | 1.0 |
| xmeas_41 -> xmeas_25 | xmeas_41 -> xmeas_25 | 0.2164 | 0.6117 | 0.4767 | 0.0000 | 0.8976 | 1.0 |
| xmv_06 -> xmeas_34 | xmv_06 -> xmeas_34 | 0.2064 | 0.6553 | 0.3250 | 0.0936 | 0.9157 | 1.0 |

