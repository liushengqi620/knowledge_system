# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.15+alg-prior-edge_sieve-k20-g4-lag3-vote2-sv0.30-vb0.12-gb6.0-pool3.0-rank0.25@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6285 +/- 0.0068 | 0.6402 +/- 0.0093 | 0.0175 | 0.0175 | 0.0773 | 0.3231 | 0.7273 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11375.5 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3051 | 0.7973 | 0.7454 | 0.0000 | 0.8765 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2736 | 0.8802 | 0.9466 | 0.5800 | 0.8543 | 1.0 |
| xmv_05 -> xmeas_13 | xmv_05 -> xmeas_13 | 0.2477 | 0.8599 | 0.3719 | 0.0000 | 0.5150 | 1.0 |
| xmeas_01 -> xmeas_08 | xmeas_01 -> xmeas_08 | 0.2064 | 0.6740 | 0.6150 | 0.0000 | 0.9506 | 1.0 |
| xmv_05 -> xmeas_11 | xmv_05 -> xmeas_11 | 0.2044 | 0.9146 | 0.3488 | 0.0000 | 0.9180 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_03 | xmv_05 -> xmv_03 | 0.3735 | 0.6641 | 0.0446 | 0.3584 | 0.6357 | 1.0 |
| xmeas_39 -> xmv_03 | xmeas_39 -> xmv_03 | 0.3715 | 0.7231 | 0.4651 | 0.0000 | 0.6379 | 1.0 |
| xmeas_06 -> xmv_03 | xmeas_06 -> xmv_03 | 0.3655 | 0.7208 | 0.5120 | 0.0000 | 0.6386 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.3620 | 0.7297 | 0.5822 | 0.0000 | 0.9844 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.2906 | 0.7291 | 0.5379 | 0.0000 | 0.9949 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_08 -> xmeas_24 | xmv_08 -> xmeas_24 | 0.3791 | 0.5496 | 0.2646 | 0.0000 | 0.0166 | 1.0 |
| xmv_06 -> xmeas_10 | xmv_06 -> xmeas_10 | 0.3101 | 0.6768 | 0.1071 | 0.8788 | 0.9261 | 1.0 |
| xmv_07 -> xmv_10 | xmv_07 -> xmv_10 | 0.3061 | 0.4216 | 0.3440 | 0.0000 | 0.1978 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2616 | 0.7472 | 0.2246 | 0.5551 | 0.8206 | 1.0 |
| xmeas_24 -> xmeas_23 | xmeas_24 -> xmeas_23 | 0.2311 | 0.6509 | 0.4263 | 0.0000 | 0.6196 | 1.0 |

