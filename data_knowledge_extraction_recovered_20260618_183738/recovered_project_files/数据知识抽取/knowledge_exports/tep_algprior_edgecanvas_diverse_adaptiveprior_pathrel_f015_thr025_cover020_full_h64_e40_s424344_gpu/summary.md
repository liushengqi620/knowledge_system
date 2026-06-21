# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_canvas-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6311 +/- 0.0080 | 0.6369 +/- 0.0067 | 0.0351 | 0.0351 | 0.1049 | 0.4157 | 0.9930 | 1.0000 | 0.3101 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11813.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_07 -> xmeas_11 | xmeas_07 -> xmeas_11 | 0.3587 | 0.6980 | 0.2631 | 0.6429 | 0.7937 | 1.0 |
| xmeas_40 -> xmeas_41 | xmeas_40 -> xmeas_41 | 0.2999 | 0.6268 | 0.3363 | 0.2403 | 0.5471 | 1.0 |
| xmv_05 -> xmeas_13 | xmv_05 -> xmeas_13 | 0.2598 | 0.6693 | 0.3399 | 0.6383 | 0.7939 | 1.0 |
| xmv_03 -> xmeas_39 | xmv_03 -> xmeas_39 | 0.2498 | 0.2559 | 0.7534 | 0.0000 | 0.0914 | 1.0 |
| xmv_10 -> xmv_03 | xmv_10 -> xmv_03 | 0.2487 | 0.7492 | 0.8332 | 0.2833 | 0.1998 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmv_03 | xmeas_30 -> xmv_03 | 0.4355 | 0.8560 | 0.4817 | 0.3980 | 0.6327 | 1.0 |
| xmv_10 -> xmv_03 | xmv_10 -> xmv_03 | 0.3614 | 0.8464 | 0.1594 | 0.6052 | 0.6501 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3044 | 0.8696 | 0.1551 | 0.7070 | 0.8871 | 1.0 |
| xmeas_40 -> xmv_03 | xmeas_40 -> xmv_03 | 0.2990 | 0.7585 | 0.8581 | 0.0000 | 0.6297 | 1.0 |
| xmeas_04 -> xmeas_18 | xmeas_04 -> xmeas_18 | 0.2907 | 0.2536 | 0.7676 | 0.0000 | 0.1038 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3521 | 0.8090 | 0.2591 | 0.6622 | 0.8179 | 1.0 |
| xmeas_41 -> xmeas_24 | xmeas_41 -> xmeas_24 | 0.3386 | 0.6393 | 0.2104 | 0.2325 | 0.6964 | 1.0 |
| xmeas_04 -> xmeas_10 | xmeas_04 -> xmeas_10 | 0.3275 | 0.7705 | 0.4524 | 0.5556 | 0.8597 | 1.0 |
| xmv_09 -> xmeas_29 | xmv_09 -> xmeas_29 | 0.3123 | 0.6853 | 0.6387 | 0.0000 | 0.8913 | 1.0 |
| xmeas_24 -> xmv_06 | xmeas_24 -> xmv_06 | 0.2993 | 0.7087 | 0.4355 | 0.4438 | 0.7634 | 1.0 |

