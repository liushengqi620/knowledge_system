# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.10-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.10+edge-cal-f0.05-b1.5-reg0.05+alg-prior-edge_sieve-k20-g4-lag3-vote2-sv0.25-vb0.12-gb5.0-pool3.0-rank0.25@0.03+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6321 +/- 0.0048 | 0.6459 +/- 0.0008 | 0.0721 | 0.0721 | 0.0521 | 0.3184 | 0.7961 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10827.6 | 166677 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3941 | 0.9314 | 0.9486 | 0.5739 | 0.8551 | 1.0 |
| xmv_05 -> xmeas_07 | xmv_05 -> xmeas_07 | 0.3316 | 0.8636 | 0.3449 | 0.0000 | 0.9840 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2813 | 0.8331 | 0.7888 | 0.0000 | 0.8758 | 1.0 |
| xmeas_23 -> xmeas_13 | xmeas_23 -> xmeas_13 | 0.2492 | 0.8125 | 0.4043 | 0.0000 | 0.8353 | 1.0 |
| xmeas_08 -> xmeas_13 | xmeas_08 -> xmeas_13 | 0.2473 | 0.7714 | 0.4016 | 0.0000 | 0.3330 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.5336 | 0.7424 | 0.4610 | 0.0000 | 0.9986 | 1.0 |
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.4403 | 0.7177 | 0.4247 | 0.0000 | 0.9993 | 1.0 |
| xmeas_06 -> xmv_03 | xmeas_06 -> xmv_03 | 0.3993 | 0.7420 | 0.5976 | 0.0000 | 0.6342 | 1.0 |
| xmv_09 -> xmv_03 | xmv_09 -> xmv_03 | 0.3523 | 0.7642 | 0.6082 | 0.0000 | 0.6365 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.3291 | 0.7028 | 0.5742 | 0.0000 | 0.9430 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3274 | 0.6591 | 0.1443 | 0.5645 | 0.6990 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2649 | 0.8097 | 0.2349 | 0.5644 | 0.8521 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.2617 | 0.7103 | 0.3361 | 0.0000 | 0.0545 | 1.0 |
| xmeas_39 -> xmv_05 | xmeas_39 -> xmv_05 | 0.2370 | 0.6523 | 0.3937 | 0.0000 | 0.9159 | 1.0 |
| xmeas_30 -> xmv_05 | xmeas_30 -> xmv_05 | 0.2302 | 0.6287 | 0.3102 | 0.0000 | 0.8803 | 1.0 |

