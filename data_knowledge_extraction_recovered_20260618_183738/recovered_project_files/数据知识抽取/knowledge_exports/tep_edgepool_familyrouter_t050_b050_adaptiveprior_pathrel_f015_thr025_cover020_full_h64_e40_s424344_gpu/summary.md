# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+edge-family-router-t0.50-f0.05-b0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6209 +/- 0.0058 | 0.6336 +/- 0.0032 | 0.0000 | 0.0000 | 0.0831 | 0.4103 | 1.0482 | 1.0000 | 0.2991 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10979.7 | 162644 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_01 | xmv_05 -> xmv_01 | 0.3777 | 0.7551 | 0.1845 | 0.4868 | 0.9576 | 1.0 |
| xmeas_13 -> xmeas_07 | xmeas_13 -> xmeas_07 | 0.2865 | 0.6821 | 0.1787 | 0.5915 | 0.6910 | 1.0 |
| xmeas_28 -> xmeas_33 | xmeas_28 -> xmeas_33 | 0.2688 | 0.4679 | 0.8796 | 0.0000 | 0.0029 | 1.0 |
| xmeas_24 -> xmv_10 | xmeas_24 -> xmv_10 | 0.2652 | 0.5679 | 0.8317 | 0.0000 | 0.1404 | 1.0 |
| xmeas_08 -> xmv_09 | xmeas_08 -> xmv_09 | 0.2569 | 0.4234 | 0.8389 | 0.0000 | 0.0033 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_03 | xmv_10 -> xmv_03 | 0.4828 | 0.8364 | 0.1614 | 0.3536 | 0.6287 | 1.0 |
| xmeas_01 -> xmeas_22 | xmeas_01 -> xmeas_22 | 0.3397 | 0.7330 | 0.8332 | 0.0000 | 0.8668 | 1.0 |
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.3286 | 0.5433 | 0.7449 | 0.0000 | 0.5272 | 1.0 |
| xmv_10 -> xmeas_38 | xmv_10 -> xmeas_38 | 0.3201 | 0.6569 | 0.6508 | 0.0000 | 0.5609 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.3131 | 0.8731 | 0.1931 | 0.4560 | 0.9262 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_09 -> xmeas_32 | xmv_09 -> xmeas_32 | 0.5898 | 0.3769 | 0.7904 | 0.0000 | 0.2181 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3707 | 0.8023 | 0.9498 | 0.5453 | 0.8833 | 1.0 |
| xmeas_35 -> xmeas_36 | xmeas_35 -> xmeas_36 | 0.3541 | 0.8133 | 0.1642 | 0.5222 | 0.5134 | 1.0 |
| xmeas_06 -> xmv_02 | xmeas_06 -> xmv_02 | 0.3088 | 0.8291 | 0.1853 | 0.4737 | 0.8111 | 1.0 |
| xmv_06 -> xmeas_30 | xmv_06 -> xmeas_30 | 0.2986 | 0.6889 | 0.2610 | 0.4127 | 0.6869 | 1.0 |

