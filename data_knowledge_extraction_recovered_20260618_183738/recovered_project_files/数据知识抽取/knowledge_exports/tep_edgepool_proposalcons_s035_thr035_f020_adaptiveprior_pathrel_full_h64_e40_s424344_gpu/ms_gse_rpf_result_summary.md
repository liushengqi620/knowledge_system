# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.35-thr0.35-t0.05-f0.20+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6330 +/- 0.0071 | 0.6450 +/- 0.0063 | 0.0351 | 0.0351 | 0.0845 | 0.3981 | 0.7697 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11125.6 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.5342 | 0.7532 | 0.1556 | 0.3931 | 0.2737 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3895 | 0.7888 | 0.1112 | 0.6348 | 0.7305 | 1.0 |
| xmv_07 -> xmeas_07 | xmv_07 -> xmeas_07 | 0.3491 | 0.6036 | 0.2963 | 0.0000 | 0.1787 | 1.0 |
| xmv_07 -> xmv_09 | xmv_07 -> xmv_09 | 0.3137 | 0.7055 | 0.3197 | 0.0000 | 0.4829 | 1.0 |
| xmv_10 -> xmeas_07 | xmv_10 -> xmeas_07 | 0.3102 | 0.7928 | 0.4929 | 0.0000 | 0.2408 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3486 | 0.6494 | 0.3538 | 0.5027 | 0.6355 | 1.0 |
| xmeas_20 -> xmeas_01 | xmeas_20 -> xmeas_01 | 0.2688 | 0.8308 | 0.5568 | 0.0000 | 0.9860 | 1.0 |
| xmeas_06 -> xmv_10 | xmeas_06 -> xmv_10 | 0.2094 | 0.4619 | 0.2872 | 0.0000 | 0.5480 | 1.0 |
| xmeas_06 -> xmv_03 | xmeas_06 -> xmv_03 | 0.2023 | 0.6451 | 0.4575 | 0.0000 | 0.5690 | 1.0 |
| xmeas_01 -> xmeas_23 | xmeas_01 -> xmeas_23 | 0.1828 | 0.8281 | 0.9488 | 0.0000 | 0.9177 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3592 | 0.7085 | 0.1391 | 0.5802 | 0.8405 | 1.0 |
| xmeas_22 -> xmeas_04 | xmeas_22 -> xmeas_04 | 0.2786 | 0.3840 | 0.2917 | 0.0000 | 0.4740 | 1.0 |
| xmeas_15 -> xmeas_09 | xmeas_15 -> xmeas_09 | 0.2378 | 0.3248 | 0.3333 | 0.0000 | 0.2986 | 1.0 |
| xmv_08 -> xmv_05 | xmv_08 -> xmv_05 | 0.2368 | 0.5209 | 0.4693 | 0.0000 | 0.9649 | 1.0 |
| xmeas_26 -> xmeas_38 | xmeas_26 -> xmeas_38 | 0.2003 | 0.5941 | 0.3110 | 0.0000 | 0.6302 | 1.0 |

