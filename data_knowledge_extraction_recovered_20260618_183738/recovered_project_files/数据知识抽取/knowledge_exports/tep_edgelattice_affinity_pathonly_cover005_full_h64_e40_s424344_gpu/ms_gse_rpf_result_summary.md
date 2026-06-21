# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.05+alg-prior-edge_lattice-k8-g3-lag3-vote2-sv0.45-vb0.12-pool3.0-rank0.30+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6235 +/- 0.0074 | 0.6383 +/- 0.0068 | 0.0175 | 0.0175 | 0.0248 | 0.0500 | 0.7982 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12279.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3447 | 0.8370 | 0.7156 | 0.1828 | 0.0546 | 1.0 |
| xmv_09 -> xmeas_13 | xmv_09 -> xmeas_13 | 0.2921 | 0.5373 | 0.3130 | 0.0000 | 0.0519 | 1.0 |
| xmeas_35 -> xmeas_05 | xmeas_35 -> xmeas_05 | 0.2884 | 0.5273 | 0.4011 | 0.0000 | 0.0061 | 1.0 |
| xmv_05 -> xmeas_21 | xmv_05 -> xmeas_21 | 0.2678 | 0.6527 | 0.4015 | 0.0000 | 0.0657 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2417 | 0.6138 | 0.4043 | 0.1934 | 0.0480 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_35 -> xmeas_16 | xmeas_35 -> xmeas_16 | 0.3796 | 0.5081 | 0.3709 | 0.0000 | 0.0512 | 1.0 |
| xmeas_06 -> xmv_03 | xmeas_06 -> xmv_03 | 0.3514 | 0.7221 | 0.3975 | 0.0000 | 0.0403 | 1.0 |
| xmv_05 -> xmv_03 | xmv_05 -> xmv_03 | 0.3489 | 0.7134 | 0.1952 | 0.1318 | 0.0411 | 1.0 |
| xmv_06 -> xmv_03 | xmv_06 -> xmv_03 | 0.3303 | 0.7399 | 0.4039 | 0.0000 | 0.0422 | 1.0 |
| xmeas_24 -> xmv_10 | xmeas_24 -> xmv_10 | 0.3281 | 0.5227 | 0.4106 | 0.0000 | 0.0030 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_28 | xmv_10 -> xmeas_28 | 0.4198 | 0.7474 | 0.8000 | 0.0000 | 0.0301 | 1.0 |
| xmv_01 -> xmv_10 | xmv_01 -> xmv_10 | 0.2880 | 0.6158 | 0.3472 | 0.0000 | 0.0351 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2001 | 0.8018 | 0.4943 | 0.1922 | 0.0704 | 1.0 |
| xmeas_39 -> xmv_10 | xmeas_39 -> xmv_10 | 0.1873 | 0.6743 | 0.3502 | 0.0000 | 0.0654 | 1.0 |
| xmeas_28 -> xmeas_29 | xmeas_28 -> xmeas_29 | 0.1807 | 0.6362 | 0.3613 | 0.0000 | 0.0660 | 1.0 |

