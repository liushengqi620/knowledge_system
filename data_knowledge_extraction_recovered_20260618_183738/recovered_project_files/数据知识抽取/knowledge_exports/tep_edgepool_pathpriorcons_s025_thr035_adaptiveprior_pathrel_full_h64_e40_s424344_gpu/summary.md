# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-prior-cons-s0.25-thr0.35-t0.05+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+path-aux@0.05 | 3 | 0.6389 +/- 0.0080 | 0.6514 +/- 0.0097 | 0.0175 | 0.0175 | 0.2272 | 0.0000 | 0.7747 | 0.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11996.1 | 160569 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_17 -> xmv_11 | xmeas_17 -> xmv_11 | 0.3090 | 0.5387 | 0.3949 | 0.7613 | 0.0000 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2713 | 0.8070 | 0.5015 | 0.6149 | 0.0000 | 1.0 |
| xmeas_09 -> xmv_03 | xmeas_09 -> xmv_03 | 0.2517 | 0.8356 | 0.5800 | 0.0000 | 0.0000 | 1.0 |
| xmeas_36 -> xmv_10 | xmeas_36 -> xmv_10 | 0.2013 | 0.7574 | 0.5338 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmv_11 | xmv_10 -> xmv_11 | 0.1742 | 0.5550 | 0.3619 | 0.8123 | 0.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.7512 | 0.7223 | 0.5843 | 0.6923 | 0.0000 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3548 | 0.6997 | 0.6511 | 0.7598 | 0.0000 | 1.0 |
| xmeas_41 -> xmeas_13 | xmeas_41 -> xmeas_13 | 0.1977 | 0.2495 | 0.4336 | 0.0000 | 0.0000 | 1.0 |
| xmeas_31 -> xmeas_07 | xmeas_31 -> xmeas_07 | 0.1939 | 0.5958 | 0.2365 | 0.8438 | 0.0000 | 1.0 |
| xmeas_25 -> xmeas_13 | xmeas_25 -> xmeas_13 | 0.1921 | 0.3979 | 0.1258 | 0.7339 | 0.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_15 -> xmeas_06 | xmeas_15 -> xmeas_06 | 0.1823 | 0.4940 | 0.2919 | 0.0000 | 0.0000 | 1.0 |
| xmeas_24 -> xmeas_38 | xmeas_24 -> xmeas_38 | 0.1716 | 0.4850 | 0.3107 | 0.0000 | 0.0000 | 1.0 |
| xmeas_18 -> xmeas_03 | xmeas_18 -> xmeas_03 | 0.1670 | 0.4782 | 0.3869 | 0.0000 | 0.0000 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.1650 | 0.5831 | 0.4019 | 0.8363 | 0.0000 | 1.0 |
| xmeas_18 -> xmv_08 | xmeas_18 -> xmv_08 | 0.1475 | 0.3330 | 0.3616 | 0.0000 | 0.0000 | 1.0 |

