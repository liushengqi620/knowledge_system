# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_cert_overlay-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6329 +/- 0.0075 | 0.6436 +/- 0.0095 | 0.0175 | 0.0175 | 0.0803 | 0.3333 | 0.7890 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10627.8 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmv_09 | xmeas_14 -> xmv_09 | 0.4600 | 0.5692 | 0.3821 | 0.0000 | 0.0022 | 1.0 |
| xmv_05 -> xmeas_41 | xmv_05 -> xmeas_41 | 0.4228 | 0.7666 | 0.4930 | 0.0000 | 0.9929 | 1.0 |
| xmeas_24 -> xmv_02 | xmeas_24 -> xmv_02 | 0.3005 | 0.5198 | 0.3599 | 0.0000 | 0.0195 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2479 | 0.7660 | 0.2011 | 0.3622 | 0.7432 | 1.0 |
| xmeas_12 -> xmeas_08 | xmeas_12 -> xmeas_08 | 0.2037 | 0.3917 | 0.4464 | 0.0000 | 0.1652 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_26 -> xmv_03 | xmeas_26 -> xmv_03 | 0.4929 | 0.7736 | 0.5075 | 0.0000 | 0.6366 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.4243 | 0.6149 | 0.0653 | 0.5195 | 0.6293 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3838 | 0.7082 | 0.2234 | 0.4864 | 0.6216 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2957 | 0.8307 | 0.7977 | 0.6941 | 0.8108 | 1.0 |
| xmeas_39 -> xmv_03 | xmeas_39 -> xmv_03 | 0.2696 | 0.6682 | 0.5094 | 0.0000 | 0.6378 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4353 | 0.7192 | 0.7658 | 0.6338 | 0.7961 | 1.0 |
| xmeas_22 -> xmeas_25 | xmeas_22 -> xmeas_25 | 0.2654 | 0.7147 | 0.5969 | 0.0000 | 0.7277 | 1.0 |
| xmeas_27 -> xmeas_01 | xmeas_27 -> xmeas_01 | 0.2464 | 0.3589 | 0.4890 | 0.0000 | 0.7982 | 1.0 |
| xmeas_14 -> xmv_04 | xmeas_14 -> xmv_04 | 0.2285 | 0.4295 | 0.6084 | 0.0000 | 0.0070 | 1.0 |
| xmeas_01 -> xmeas_31 | xmeas_01 -> xmeas_31 | 0.2050 | 0.5989 | 0.4099 | 0.0000 | 0.3985 | 1.0 |

