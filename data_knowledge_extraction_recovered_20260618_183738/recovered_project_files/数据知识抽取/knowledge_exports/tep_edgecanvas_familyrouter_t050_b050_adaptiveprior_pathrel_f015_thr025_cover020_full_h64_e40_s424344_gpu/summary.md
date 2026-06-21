# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+edge-family-router-t0.50-f0.05-b0.50+prior-cover@0.20+alg-prior-edge_canvas-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6259 +/- 0.0039 | 0.6378 +/- 0.0034 | 0.0175 | 0.0175 | 0.0922 | 0.4106 | 0.9584 | 1.0000 | 0.3106 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10443.7 | 162644 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_02 -> xmv_05 | xmv_02 -> xmv_05 | 0.4201 | 0.8322 | 0.2390 | 0.6478 | 0.9322 | 1.0 |
| xmeas_08 -> xmv_09 | xmeas_08 -> xmv_09 | 0.3895 | 0.2492 | 0.7227 | 0.0000 | 0.0001 | 1.0 |
| xmv_05 -> xmeas_16 | xmv_05 -> xmeas_16 | 0.3620 | 0.9412 | 0.1111 | 0.5902 | 0.9223 | 1.0 |
| xmeas_08 -> xmv_04 | xmeas_08 -> xmv_04 | 0.3582 | 0.3616 | 0.7370 | 0.0000 | 0.2222 | 1.0 |
| xmv_05 -> xmeas_13 | xmv_05 -> xmeas_13 | 0.3304 | 0.9318 | 0.2500 | 0.6898 | 0.8689 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3862 | 0.7840 | 0.1004 | 0.7088 | 0.9319 | 1.0 |
| xmeas_20 -> xmeas_01 | xmeas_20 -> xmeas_01 | 0.3477 | 0.7101 | 0.3414 | 0.3982 | 0.8326 | 1.0 |
| xmeas_27 -> xmeas_13 | xmeas_27 -> xmeas_13 | 0.2745 | 0.5895 | 0.3181 | 0.3360 | 0.2499 | 1.0 |
| xmeas_18 -> xmeas_22 | xmeas_18 -> xmeas_22 | 0.2421 | 0.5234 | 0.1633 | 0.3530 | 0.4722 | 1.0 |
| xmeas_13 -> xmeas_10 | xmeas_13 -> xmeas_10 | 0.2414 | 0.6019 | 0.2215 | 0.5577 | 0.6911 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_04 -> xmeas_10 | xmeas_04 -> xmeas_10 | 0.3532 | 0.7535 | 0.1644 | 0.5097 | 0.9593 | 1.0 |
| xmeas_12 -> xmv_05 | xmeas_12 -> xmv_05 | 0.3518 | 0.8114 | 0.7450 | 0.0000 | 0.9992 | 1.0 |
| xmv_10 -> xmeas_13 | xmv_10 -> xmeas_13 | 0.3423 | 0.6725 | 0.2364 | 0.6292 | 0.6987 | 1.0 |
| xmeas_02 -> xmeas_20 | xmeas_02 -> xmeas_20 | 0.3275 | 0.3751 | 0.5664 | 0.0000 | 0.2487 | 1.0 |
| xmeas_02 -> xmv_02 | xmeas_02 -> xmv_02 | 0.3184 | 0.7170 | 0.1739 | 0.5264 | 0.8019 | 1.0 |

