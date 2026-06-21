# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+learned-path-admit-s0.75-reg0.002+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-k8-edge4+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6179 +/- 0.0000 | 0.6347 +/- 0.0000 | n/a | n/a | 0.0919 | 0.3740 | 0.6240 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10515.2 | 175320 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmeas_13 | xmv_01 -> xmeas_13 | 0.3884 | 0.7011 | 0.4019 | 0.0000 | 0.6821 | 1.0 |
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.3692 | 0.7112 | 0.1142 | 0.2376 | 0.9620 | 1.0 |
| xmeas_33 -> xmv_05 | xmeas_33 -> xmv_05 | 0.3246 | 0.7152 | 0.4441 | 0.0000 | 0.9533 | 1.0 |
| xmeas_22 -> xmeas_26 | xmeas_22 -> xmeas_26 | 0.2525 | 0.7248 | 0.4497 | 0.0000 | 0.2382 | 1.0 |
| xmeas_32 -> xmv_05 | xmeas_32 -> xmv_05 | 0.2038 | 0.6538 | 0.0864 | 0.5118 | 0.8340 | 1.0 |

