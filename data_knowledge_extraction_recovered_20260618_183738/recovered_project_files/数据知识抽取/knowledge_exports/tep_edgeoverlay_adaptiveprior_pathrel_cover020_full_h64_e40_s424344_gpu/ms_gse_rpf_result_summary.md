# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_overlay-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6342 +/- 0.0025 | 0.6462 +/- 0.0029 | 0.0351 | 0.0351 | 0.0810 | 0.3317 | 0.7746 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10982.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2888 | 0.6701 | 0.0473 | 0.6056 | 0.8269 | 1.0 |
| xmeas_14 -> xmeas_18 | xmeas_14 -> xmeas_18 | 0.2811 | 0.6761 | 0.4583 | 0.0000 | 0.1253 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2720 | 0.8110 | 0.1811 | 0.6193 | 0.7503 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2357 | 0.6954 | 0.4874 | 0.7635 | 0.8441 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2213 | 0.6849 | 0.2630 | 0.3928 | 0.8185 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4024 | 0.7139 | 0.1995 | 0.4902 | 0.6353 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.3920 | 0.6468 | 0.0840 | 0.5217 | 0.6327 | 1.0 |
| xmeas_24 -> xmv_03 | xmeas_24 -> xmv_03 | 0.3380 | 0.6880 | 0.4848 | 0.0000 | 0.6326 | 1.0 |
| xmv_06 -> xmv_03 | xmv_06 -> xmv_03 | 0.3065 | 0.6807 | 0.4685 | 0.0000 | 0.6429 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2840 | 0.8332 | 0.7437 | 0.7097 | 0.8344 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.5891 | 0.8111 | 0.6002 | 0.6599 | 0.8377 | 1.0 |
| xmeas_41 -> xmeas_01 | xmeas_41 -> xmeas_01 | 0.3387 | 0.4621 | 0.4855 | 0.0000 | 0.3582 | 1.0 |
| xmeas_15 -> xmv_10 | xmeas_15 -> xmv_10 | 0.3235 | 0.6750 | 0.4722 | 0.0000 | 0.8319 | 1.0 |
| xmv_09 -> xmeas_18 | xmv_09 -> xmeas_18 | 0.2259 | 0.5317 | 0.1518 | 0.5005 | 0.4605 | 1.0 |
| xmeas_20 -> xmeas_23 | xmeas_20 -> xmeas_23 | 0.2219 | 0.5855 | 0.1389 | 0.4290 | 0.4497 | 1.0 |

