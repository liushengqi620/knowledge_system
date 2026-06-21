# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6361 +/- 0.0051 | 0.6477 +/- 0.0044 | 0.0351 | 0.0351 | 0.0867 | 0.3437 | 0.7928 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12641.3 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4293 | 0.8433 | 0.0415 | 0.5594 | 0.8938 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2347 | 0.6146 | 0.2966 | 0.2783 | 0.8493 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2272 | 0.7978 | 0.0957 | 0.6743 | 0.7943 | 1.0 |
| xmeas_22 -> xmv_02 | xmeas_22 -> xmv_02 | 0.2262 | 0.7589 | 0.4375 | 0.0000 | 0.7310 | 1.0 |
| xmeas_06 -> xmeas_10 | xmeas_06 -> xmeas_10 | 0.2024 | 0.4651 | 0.5094 | 0.0000 | 0.3376 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4352 | 0.6637 | 0.3462 | 0.5102 | 0.6473 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.3480 | 0.8566 | 0.7226 | 0.6401 | 0.8074 | 1.0 |
| xmeas_10 -> xmv_09 | xmeas_10 -> xmv_09 | 0.2487 | 0.7307 | 0.6560 | 0.0000 | 0.8032 | 1.0 |
| xmeas_10 -> xmeas_01 | xmeas_10 -> xmeas_01 | 0.2354 | 0.7353 | 0.4623 | 0.0000 | 0.9962 | 1.0 |
| xmeas_29 -> xmv_05 | xmeas_29 -> xmv_05 | 0.2157 | 0.5362 | 0.0791 | 0.5476 | 0.8017 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_03 -> xmeas_20 | xmeas_03 -> xmeas_20 | 0.4726 | 0.4825 | 0.3891 | 0.0000 | 0.5936 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3965 | 0.7146 | 0.1367 | 0.5649 | 0.8155 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.2947 | 0.7976 | 0.3673 | 0.0000 | 0.0572 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2303 | 0.8346 | 0.5256 | 0.0000 | 0.7491 | 1.0 |
| xmeas_30 -> xmeas_18 | xmeas_30 -> xmeas_18 | 0.2033 | 0.7687 | 0.4217 | 0.0000 | 0.6112 | 1.0 |

