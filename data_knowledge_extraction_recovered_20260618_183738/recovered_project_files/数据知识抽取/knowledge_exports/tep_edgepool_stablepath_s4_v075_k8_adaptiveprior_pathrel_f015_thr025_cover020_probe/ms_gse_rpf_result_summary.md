# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w1.00-lag3@0.50-k8-class-filter0.25+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6314 +/- 0.0000 | 0.6476 +/- 0.0000 | n/a | n/a | 0.0802 | 0.6247 | 0.7924 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10401.2 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmeas_28 | xmv_05 -> xmeas_28 | 0.2535 | 0.8859 | 0.3369 | 0.0000 | 0.9459 | 1.0 |
| xmeas_28 -> xmeas_25 | xmeas_28 -> xmeas_25 | 0.2349 | 0.3270 | 0.3755 | 0.0000 | 0.4965 | 1.0 |
| xmeas_02 -> xmeas_19 | xmeas_02 -> xmeas_19 | 0.2069 | 0.4916 | 0.4065 | 0.0000 | 0.4454 | 1.0 |
| xmeas_22 -> xmeas_21 | xmeas_22 -> xmeas_21 | 0.2057 | 0.8219 | 0.4627 | 0.0000 | 0.9487 | 1.0 |
| xmv_05 -> xmv_09 | xmv_05 -> xmv_09 | 0.1894 | 0.6143 | 0.1609 | 0.4415 | 0.7703 | 1.0 |

