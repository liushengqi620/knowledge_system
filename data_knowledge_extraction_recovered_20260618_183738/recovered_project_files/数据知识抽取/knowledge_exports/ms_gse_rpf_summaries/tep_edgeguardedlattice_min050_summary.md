# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+salience-class@0.00+class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.70-t0.08-relative_evidence-s0.20-proposal_feature-minsup0.50+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+candidate-cover@0.08+alg-prior-edge_guarded_lattice-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@8+path-aux@0.05+router@0.05 | 3 | 0.6279 +/- 0.0037 | 0.6421 +/- 0.0002 | 0.0351 | 0.0351 | 0.0427 | 0.7887 | 0.7682 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 5659.0 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3328 | 0.6838 | 0.1431 | 0.3134 | 0.8025 | 1.0 |
| xmv_07 -> xmeas_19 | xmv_07 -> xmeas_19 | 0.3326 | 0.8568 | 0.4075 | 0.0000 | 0.8025 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2932 | 0.8102 | 0.4470 | 0.2064 | 0.7837 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2814 | 0.7693 | 0.3126 | 0.1094 | 0.9866 | 1.0 |
| xmv_05 -> xmeas_28 | xmv_05 -> xmeas_28 | 0.2649 | 0.7613 | 0.4732 | 0.0000 | 0.9022 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.4275 | 0.5867 | 0.1224 | 0.1139 | 0.9905 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3501 | 0.6902 | 0.3147 | 0.1813 | 0.8050 | 1.0 |
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.2635 | 0.4980 | 0.0983 | 0.0102 | 0.8903 | 1.0 |
| xmeas_19 -> xmeas_18 | xmeas_19 -> xmeas_18 | 0.2498 | 0.5915 | 0.0947 | 0.1520 | 0.8048 | 1.0 |
| xmeas_06 -> xmv_03 | xmeas_06 -> xmv_03 | 0.2376 | 0.6014 | 0.4481 | 0.0000 | 0.9905 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_28 -> xmeas_23 | xmeas_28 -> xmeas_23 | 0.3040 | 0.6880 | 0.3901 | 0.0000 | 0.8981 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2336 | 0.5578 | 0.1775 | 0.1156 | 0.9903 | 1.0 |
| xmeas_20 -> xmeas_08 | xmeas_20 -> xmeas_08 | 0.2320 | 0.7456 | 0.3897 | 0.0000 | 0.7319 | 1.0 |
| xmv_06 -> xmeas_21 | xmv_06 -> xmeas_21 | 0.2060 | 0.6324 | 0.8433 | 0.0000 | 0.9157 | 1.0 |
| xmeas_01 -> xmeas_25 | xmeas_01 -> xmeas_25 | 0.2030 | 0.6550 | 0.3680 | 0.0000 | 0.8976 | 1.0 |

