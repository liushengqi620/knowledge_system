# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-prior-cons-s0.15-thr0.50-t0.05+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+path-aux@0.05 | 3 | 0.6307 +/- 0.0053 | 0.6448 +/- 0.0067 | 0.0175 | 0.0175 | 0.1827 | 0.0000 | 0.7963 | 0.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10541.8 | 160569 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmv_11 | xmv_03 -> xmv_11 | 0.3303 | 0.4924 | 0.4368 | 0.0000 | 0.0000 | 1.0 |
| xmeas_09 -> xmv_03 | xmeas_09 -> xmv_03 | 0.2188 | 0.8099 | 0.6771 | 0.0000 | 0.0000 | 1.0 |
| xmv_04 -> xmeas_13 | xmv_04 -> xmeas_13 | 0.2120 | 0.8472 | 0.5106 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmeas_13 | xmv_10 -> xmeas_13 | 0.2109 | 0.7431 | 0.5637 | 0.0000 | 0.0000 | 1.0 |
| xmeas_21 -> xmv_11 | xmeas_21 -> xmv_11 | 0.2074 | 0.6627 | 0.5988 | 0.0000 | 0.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_32 -> xmv_11 | xmeas_32 -> xmv_11 | 0.3713 | 0.4528 | 0.4827 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmv_11 | xmv_10 -> xmv_11 | 0.2920 | 0.6145 | 0.5954 | 0.7372 | 0.0000 | 1.0 |
| xmv_02 -> xmeas_11 | xmv_02 -> xmeas_11 | 0.2914 | 0.6441 | 0.4528 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmeas_17 | xmv_10 -> xmeas_17 | 0.2372 | 0.5340 | 0.4837 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2309 | 0.6140 | 0.4726 | 0.7167 | 0.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_35 -> xmv_10 | xmeas_35 -> xmv_10 | 0.5616 | 0.9509 | 0.3773 | 0.0000 | 0.0000 | 1.0 |
| xmeas_40 -> xmv_10 | xmeas_40 -> xmv_10 | 0.3792 | 0.7968 | 0.4486 | 0.0000 | 0.0000 | 1.0 |
| xmeas_29 -> xmeas_18 | xmeas_29 -> xmeas_18 | 0.2721 | 0.6554 | 0.3462 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmeas_07 | xmv_10 -> xmeas_07 | 0.2677 | 0.9724 | 0.3815 | 0.0000 | 0.0000 | 1.0 |
| xmeas_19 -> xmeas_25 | xmeas_19 -> xmeas_25 | 0.2668 | 0.5949 | 0.3514 | 0.0000 | 0.0000 | 1.0 |

