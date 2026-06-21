# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.20t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6298 +/- 0.0069 | 0.6430 +/- 0.0069 | 0.0175 | 0.0175 | 0.0817 | 0.3344 | 0.7992 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12208.4 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2916 | 0.6332 | 0.4554 | 0.0000 | 0.1125 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2817 | 0.7111 | 0.4705 | 0.2675 | 0.8124 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2579 | 0.4686 | 0.2369 | 0.3585 | 0.2644 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2287 | 0.6899 | 0.1728 | 0.5812 | 0.6603 | 1.0 |
| xmv_11 -> xmeas_20 | xmv_11 -> xmeas_20 | 0.2249 | 0.8117 | 0.5567 | 0.0000 | 0.7796 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4895 | 0.7425 | 0.2290 | 0.4713 | 0.5910 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.4212 | 0.7627 | 0.3424 | 0.0000 | 0.9986 | 1.0 |
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.2611 | 0.7525 | 0.4843 | 0.0000 | 0.9971 | 1.0 |
| xmeas_26 -> xmv_09 | xmeas_26 -> xmv_09 | 0.2574 | 0.6255 | 0.3355 | 0.0000 | 0.3094 | 1.0 |
| xmv_07 -> xmv_03 | xmv_07 -> xmv_03 | 0.2317 | 0.6617 | 0.3947 | 0.0000 | 0.6375 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3565 | 0.7387 | 0.1200 | 0.5789 | 0.8399 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.3005 | 0.6175 | 0.3789 | 0.0000 | 0.0074 | 1.0 |
| xmeas_39 -> xmeas_21 | xmeas_39 -> xmeas_21 | 0.2726 | 0.5048 | 0.3693 | 0.0000 | 0.0042 | 1.0 |
| xmeas_41 -> xmeas_25 | xmeas_41 -> xmeas_25 | 0.2427 | 0.3310 | 0.5020 | 0.0000 | 0.0091 | 1.0 |
| xmeas_28 -> xmeas_08 | xmeas_28 -> xmeas_08 | 0.2410 | 0.4324 | 0.5679 | 0.0000 | 0.1142 | 1.0 |

