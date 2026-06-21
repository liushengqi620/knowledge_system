# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+salience-cover@0.10+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_pool-k8-g3-lag3-vote2-sv0.55-vb0.15-pool2.0-rank0.35@0.05+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6309 +/- 0.0010 | 0.6435 +/- 0.0020 | 0.0175 | 0.0175 | 0.0350 | 0.0540 | 0.8069 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12054.2 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_36 -> xmeas_38 | xmeas_36 -> xmeas_38 | 0.4252 | 0.6996 | 0.2682 | 0.0000 | 0.0575 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3038 | 0.7494 | 0.2205 | 0.1955 | 0.1021 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2910 | 0.7835 | 0.7905 | 0.0000 | 0.0238 | 1.0 |
| xmeas_38 -> xmv_05 | xmeas_38 -> xmv_05 | 0.2598 | 0.6983 | 0.2616 | 0.0000 | 0.0843 | 1.0 |
| xmeas_29 -> xmeas_30 | xmeas_29 -> xmeas_30 | 0.2540 | 0.7423 | 0.2378 | 0.0000 | 0.0514 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.3872 | 0.7176 | 0.3144 | 0.0000 | 0.0625 | 1.0 |
| xmeas_12 -> xmeas_01 | xmeas_12 -> xmeas_01 | 0.3703 | 0.7045 | 0.2576 | 0.0000 | 0.0633 | 1.0 |
| xmeas_36 -> xmeas_09 | xmeas_36 -> xmeas_09 | 0.2841 | 0.2559 | 0.4222 | 0.0000 | 0.0368 | 1.0 |
| xmeas_39 -> xmeas_01 | xmeas_39 -> xmeas_01 | 0.2824 | 0.6587 | 0.1964 | 0.0000 | 0.0629 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2707 | 0.5826 | 0.3397 | 0.1674 | 0.0920 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_03 -> xmeas_09 | xmeas_03 -> xmeas_09 | 0.5437 | 0.8033 | 0.2675 | 0.0000 | 0.0513 | 1.0 |
| xmv_05 -> xmeas_09 | xmv_05 -> xmeas_09 | 0.4401 | 0.7481 | 0.1920 | 0.0000 | 0.1156 | 1.0 |
| xmeas_41 -> xmeas_09 | xmeas_41 -> xmeas_09 | 0.3961 | 0.8025 | 0.3122 | 0.0000 | 0.0506 | 1.0 |
| xmeas_13 -> xmv_05 | xmeas_13 -> xmv_05 | 0.3496 | 0.6878 | 0.1870 | 0.0000 | 0.1433 | 1.0 |
| xmeas_04 -> xmv_05 | xmeas_04 -> xmv_05 | 0.3024 | 0.7587 | 0.2143 | 0.0000 | 0.0958 | 1.0 |

