# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_cert_overlay-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6304 +/- 0.0060 | 0.6440 +/- 0.0082 | 0.0175 | 0.0175 | 0.0822 | 0.3314 | 0.7946 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11225.4 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4689 | 0.8782 | 0.0753 | 0.5582 | 0.8915 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3639 | 0.7777 | 0.3534 | 0.2812 | 0.8626 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3279 | 0.8863 | 0.1755 | 0.6531 | 0.7656 | 1.0 |
| xmeas_20 -> xmeas_19 | xmeas_20 -> xmeas_19 | 0.2322 | 0.8361 | 0.3432 | 0.0000 | 0.0151 | 1.0 |
| xmeas_18 -> xmv_09 | xmeas_18 -> xmv_09 | 0.2140 | 0.2516 | 0.1271 | 0.5081 | 0.5114 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4807 | 0.7200 | 0.3932 | 0.4872 | 0.6108 | 1.0 |
| xmeas_23 -> xmeas_01 | xmeas_23 -> xmeas_01 | 0.4386 | 0.7684 | 0.3955 | 0.0000 | 0.9740 | 1.0 |
| xmeas_12 -> xmeas_01 | xmeas_12 -> xmeas_01 | 0.4260 | 0.7596 | 0.3456 | 0.0000 | 0.9990 | 1.0 |
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.4150 | 0.7357 | 0.4276 | 0.0000 | 0.9937 | 1.0 |
| xmeas_24 -> xmv_03 | xmeas_24 -> xmv_03 | 0.3056 | 0.6870 | 0.4492 | 0.0000 | 0.6112 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_36 -> xmv_05 | xmeas_36 -> xmv_05 | 0.3145 | 0.2921 | 0.3311 | 0.0000 | 0.8705 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2979 | 0.7217 | 0.2847 | 0.5566 | 0.7885 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.2117 | 0.8005 | 0.4961 | 0.0000 | 0.0087 | 1.0 |
| xmeas_30 -> xmeas_17 | xmeas_30 -> xmeas_17 | 0.1943 | 0.8133 | 0.4202 | 0.0000 | 0.0031 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.1943 | 0.7990 | 0.5824 | 0.0000 | 0.6759 | 1.0 |

