# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_cert_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6247 +/- 0.0027 | 0.6376 +/- 0.0036 | 0.0000 | 0.0000 | 0.0853 | 0.3354 | 0.7851 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10158.2 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.4978 | 0.7125 | 0.6361 | 0.0000 | 0.2105 | 1.0 |
| xmeas_37 -> xmeas_19 | xmeas_37 -> xmeas_19 | 0.3049 | 0.5559 | 0.3484 | 0.0000 | 0.0243 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.1864 | 0.6014 | 0.3431 | 0.3571 | 0.6649 | 1.0 |
| xmeas_01 -> xmeas_18 | xmeas_01 -> xmeas_18 | 0.1812 | 0.6973 | 0.8350 | 0.0000 | 0.8961 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.1809 | 0.7096 | 0.3280 | 0.6854 | 0.8065 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_06 -> xmv_03 | xmeas_06 -> xmv_03 | 0.4579 | 0.6809 | 0.6262 | 0.0000 | 0.6271 | 1.0 |
| xmv_05 -> xmv_03 | xmv_05 -> xmv_03 | 0.3648 | 0.7052 | 0.0777 | 0.4970 | 0.6433 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3369 | 0.6206 | 0.5802 | 0.0000 | 0.6617 | 1.0 |
| xmeas_19 -> xmv_03 | xmeas_19 -> xmv_03 | 0.2874 | 0.6817 | 0.6122 | 0.0000 | 0.6172 | 1.0 |
| xmv_11 -> xmeas_22 | xmv_11 -> xmeas_22 | 0.2630 | 0.6571 | 0.7016 | 0.3181 | 0.5126 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_08 -> xmv_07 | xmv_08 -> xmv_07 | 0.3938 | 0.6819 | 0.4016 | 0.0000 | 0.1976 | 1.0 |
| xmeas_10 -> xmeas_22 | xmeas_10 -> xmeas_22 | 0.3291 | 0.8734 | 0.2749 | 0.4559 | 0.9038 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3111 | 0.8239 | 0.0648 | 0.7141 | 0.8447 | 1.0 |
| xmeas_11 -> xmv_05 | xmeas_11 -> xmv_05 | 0.2701 | 0.6032 | 0.0471 | 0.5591 | 0.9967 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2415 | 0.5998 | 0.4423 | 0.0000 | 0.3359 | 1.0 |

