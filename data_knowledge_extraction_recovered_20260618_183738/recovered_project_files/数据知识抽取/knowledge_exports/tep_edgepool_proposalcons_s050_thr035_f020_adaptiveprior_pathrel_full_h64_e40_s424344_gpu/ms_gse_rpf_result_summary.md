# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.50-thr0.35-t0.05-f0.20+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6359 +/- 0.0015 | 0.6466 +/- 0.0040 | 0.0175 | 0.0175 | 0.0893 | 0.4064 | 0.7911 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11441.6 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.6552 | 0.8169 | 0.1197 | 0.6599 | 0.7728 | 1.0 |
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.3018 | 0.5425 | 0.2732 | 0.0000 | 0.5043 | 1.0 |
| xmeas_01 -> xmeas_07 | xmeas_01 -> xmeas_07 | 0.2365 | 0.7768 | 0.6978 | 0.0000 | 0.7487 | 1.0 |
| xmeas_23 -> xmv_11 | xmeas_23 -> xmv_11 | 0.2204 | 0.8404 | 0.1317 | 0.4583 | 0.5527 | 1.0 |
| xmeas_31 -> xmv_11 | xmeas_31 -> xmv_11 | 0.1993 | 0.7388 | 0.2788 | 0.0000 | 0.8811 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_08 -> xmv_05 | xmv_08 -> xmv_05 | 0.3503 | 0.5459 | 0.3067 | 0.0000 | 0.7119 | 1.0 |
| xmeas_20 -> xmv_05 | xmeas_20 -> xmv_05 | 0.3112 | 0.5791 | 0.0633 | 0.7169 | 0.8023 | 1.0 |
| xmeas_33 -> xmeas_01 | xmeas_33 -> xmeas_01 | 0.3063 | 0.7284 | 0.2552 | 0.0000 | 0.9841 | 1.0 |
| xmeas_17 -> xmv_03 | xmeas_17 -> xmv_03 | 0.2906 | 0.7058 | 0.3940 | 0.0000 | 0.5997 | 1.0 |
| xmeas_09 -> xmv_05 | xmeas_09 -> xmv_05 | 0.2592 | 0.5878 | 0.4662 | 0.0000 | 0.6537 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_15 -> xmeas_09 | xmeas_15 -> xmeas_09 | 0.4910 | 0.5635 | 0.3393 | 0.0000 | 0.5224 | 1.0 |
| xmeas_20 -> xmeas_35 | xmeas_20 -> xmeas_35 | 0.3175 | 0.5889 | 0.2981 | 0.0000 | 0.3741 | 1.0 |
| xmv_09 -> xmeas_13 | xmv_09 -> xmeas_13 | 0.2659 | 0.6251 | 0.2915 | 0.0000 | 0.5667 | 1.0 |
| xmeas_06 -> xmv_05 | xmeas_06 -> xmv_05 | 0.2523 | 0.6462 | 0.3170 | 0.0000 | 0.8184 | 1.0 |
| xmeas_08 -> xmv_05 | xmeas_08 -> xmv_05 | 0.2310 | 0.5266 | 0.2596 | 0.0000 | 0.7537 | 1.0 |

