# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.10-thr0.50-t0.05-f0.20-relative_evidence-retain0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6294 +/- 0.0027 | 0.6416 +/- 0.0036 | 0.0351 | 0.0351 | 0.0841 | 0.3375 | 0.8101 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11664.6 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3462 | 0.6851 | 0.3434 | 0.3218 | 0.1849 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2692 | 0.8539 | 0.1186 | 0.5314 | 0.8379 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2316 | 0.7514 | 0.4416 | 0.0000 | 0.2056 | 1.0 |
| xmv_10 -> xmeas_07 | xmv_10 -> xmeas_07 | 0.2168 | 0.9007 | 0.5856 | 0.0000 | 0.2067 | 1.0 |
| xmeas_03 -> xmeas_37 | xmeas_03 -> xmeas_37 | 0.2136 | 0.7044 | 0.4248 | 0.0000 | 0.0856 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4499 | 0.7183 | 0.2252 | 0.4953 | 0.6237 | 1.0 |
| xmeas_33 -> xmeas_01 | xmeas_33 -> xmeas_01 | 0.4177 | 0.7318 | 0.5018 | 0.0000 | 0.8876 | 1.0 |
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.3968 | 0.6947 | 0.3531 | 0.0000 | 0.9879 | 1.0 |
| xmeas_38 -> xmv_03 | xmeas_38 -> xmv_03 | 0.3170 | 0.7085 | 0.3334 | 0.0000 | 0.6378 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.3030 | 0.7691 | 0.4234 | 0.0000 | 0.9980 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_08 -> xmv_08 | xmeas_08 -> xmv_08 | 0.3760 | 0.5213 | 0.3417 | 0.0000 | 0.3988 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2982 | 0.6960 | 0.3368 | 0.5842 | 0.8477 | 1.0 |
| xmeas_09 -> xmeas_12 | xmeas_09 -> xmeas_12 | 0.2370 | 0.7105 | 0.3616 | 0.0000 | 0.6099 | 1.0 |
| xmv_09 -> xmeas_37 | xmv_09 -> xmeas_37 | 0.2027 | 0.7170 | 0.3601 | 0.0000 | 0.0423 | 1.0 |
| xmeas_10 -> xmeas_20 | xmeas_10 -> xmeas_20 | 0.1888 | 0.6612 | 0.4135 | 0.0000 | 0.5319 | 1.0 |

