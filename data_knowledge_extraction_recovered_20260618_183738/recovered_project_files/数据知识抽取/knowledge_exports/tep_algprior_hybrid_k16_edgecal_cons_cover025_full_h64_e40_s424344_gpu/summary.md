# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+edge-cal-f0.20-b4.0+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6094 +/- 0.0085 | 0.6331 +/- 0.0045 | 0.0000 | 0.0000 | 0.2784 | 0.3383 | 0.7419 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 17197.6 | 153678 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmeas_20 | xmv_01 -> xmeas_20 | 0.2999 | 0.5941 | 0.4429 | 0.0000 | 0.7995 | 1.0 |
| xmeas_41 -> xmeas_20 | xmeas_41 -> xmeas_20 | 0.2746 | 0.6010 | 0.2543 | 0.5289 | 0.7959 | 1.0 |
| xmeas_17 -> xmv_11 | xmeas_17 -> xmv_11 | 0.2668 | 0.8066 | 0.6313 | 0.3287 | 0.5430 | 1.0 |
| xmv_02 -> xmv_05 | xmv_02 -> xmv_05 | 0.2656 | 0.4956 | 0.4236 | 0.0000 | 0.7397 | 1.0 |
| xmeas_06 -> xmv_05 | xmeas_06 -> xmv_05 | 0.2635 | 0.6136 | 0.4419 | 0.0000 | 0.9923 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_12 -> xmv_11 | xmeas_12 -> xmv_11 | 0.6639 | 0.5547 | 0.3743 | 0.0000 | 0.1663 | 1.0 |
| xmeas_25 -> xmv_11 | xmeas_25 -> xmv_11 | 0.5715 | 0.8374 | 0.1584 | 0.7802 | 0.8386 | 1.0 |
| xmeas_06 -> xmv_11 | xmeas_06 -> xmv_11 | 0.5646 | 0.6073 | 0.4619 | 0.0000 | 0.5666 | 1.0 |
| xmeas_29 -> xmv_11 | xmeas_29 -> xmv_11 | 0.3571 | 0.6985 | 0.1440 | 0.7470 | 0.6633 | 1.0 |
| xmeas_25 -> xmeas_01 | xmeas_25 -> xmeas_01 | 0.2541 | 0.4331 | 0.4678 | 0.0000 | 0.8507 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_41 -> xmeas_27 | xmeas_41 -> xmeas_27 | 0.3111 | 0.4620 | 0.3809 | 0.0000 | 0.0217 | 1.0 |
| xmeas_35 -> xmv_05 | xmeas_35 -> xmv_05 | 0.3005 | 0.5689 | 0.1070 | 0.6439 | 0.9992 | 1.0 |
| xmv_10 -> xmeas_13 | xmv_10 -> xmeas_13 | 0.2666 | 0.9022 | 0.1588 | 0.7153 | 0.9309 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2602 | 0.9043 | 0.3490 | 0.6896 | 0.8255 | 1.0 |
| xmv_07 -> xmeas_31 | xmv_07 -> xmeas_31 | 0.2422 | 0.9272 | 0.4986 | 0.0000 | 0.0267 | 1.0 |

