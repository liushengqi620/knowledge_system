# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-prior-cons-s0.25-thr0.35-t0.05-class_blend-cf0.25+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05 | 3 | 0.6261 +/- 0.0069 | 0.6397 +/- 0.0084 | 0.0526 | 0.0526 | 0.1103 | 0.2274 | 0.8035 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11199.8 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.5461 | 0.8524 | 0.9317 | 0.4854 | 0.4065 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.4239 | 0.7927 | 0.5634 | 0.2462 | 0.1051 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3261 | 0.7395 | 0.2138 | 0.5560 | 0.2340 | 1.0 |
| xmeas_26 -> xmeas_18 | xmeas_26 -> xmeas_18 | 0.2519 | 0.7634 | 0.3999 | 0.0000 | 0.2730 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2482 | 0.8221 | 0.4632 | 0.0000 | 0.2805 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4098 | 0.6697 | 0.2454 | 0.5608 | 0.4632 | 1.0 |
| xmeas_39 -> xmeas_03 | xmeas_39 -> xmeas_03 | 0.2612 | 0.5409 | 0.5163 | 0.0000 | 0.0302 | 1.0 |
| xmeas_15 -> xmeas_18 | xmeas_15 -> xmeas_18 | 0.2468 | 0.5085 | 0.5740 | 0.0000 | 0.4798 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2320 | 0.7116 | 0.4118 | 0.0000 | 0.3238 | 1.0 |
| xmeas_14 -> xmv_05 | xmeas_14 -> xmv_05 | 0.2191 | 0.6272 | 0.4920 | 0.0000 | 0.4022 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmeas_03 | xmeas_30 -> xmeas_03 | 0.6240 | 0.7045 | 0.3868 | 0.0000 | 0.2709 | 1.0 |
| xmeas_03 -> xmeas_11 | xmeas_03 -> xmeas_11 | 0.2707 | 0.5169 | 0.3952 | 0.0000 | 0.0874 | 1.0 |
| xmeas_32 -> xmv_05 | xmeas_32 -> xmv_05 | 0.2607 | 0.6687 | 0.3635 | 0.0000 | 0.4056 | 1.0 |
| xmv_10 -> xmeas_30 | xmv_10 -> xmeas_30 | 0.2277 | 0.8114 | 0.5790 | 0.0000 | 0.0328 | 1.0 |
| xmv_10 -> xmeas_13 | xmv_10 -> xmeas_13 | 0.2271 | 0.7939 | 0.4459 | 0.0000 | 0.1138 | 1.0 |

