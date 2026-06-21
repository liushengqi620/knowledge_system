# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-evid-cons-s0.10-thr0.50-t0.05-relative+prior-cover@0.20+alg-prior-edge_pool-k8-g3-lag3-vote2-sv0.55-vb0.15-pool2.0-rank0.35@0.05+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@6+path-aux@0.05+router@0.05 | 1 | 0.0854 +/- 0.0000 | 0.1273 +/- 0.0000 | n/a | n/a | 0.2047 | 0.0407 | 0.1891 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11422.2 | 59697 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmeas_40 | xmeas_09 -> xmeas_40 | 0.1736 | 0.5174 | 0.1684 | 0.0000 | 0.0913 | 1.0 |
| xmeas_32 -> xmeas_15 | xmeas_32 -> xmeas_15 | 0.1227 | 0.4855 | 0.1700 | 0.2938 | 0.0548 | 1.0 |
| xmeas_05 -> xmeas_12 | xmeas_05 -> xmeas_12 | 0.1184 | 0.5213 | 0.1698 | 0.0000 | 0.0987 | 1.0 |
| xmeas_06 -> xmeas_24 | xmeas_06 -> xmeas_24 | 0.1144 | 0.4958 | 0.1645 | 0.0000 | 0.0247 | 1.0 |
| xmeas_02 -> xmeas_37 | xmeas_02 -> xmeas_37 | 0.1067 | 0.4828 | 0.1562 | 0.0000 | 0.0030 | 1.0 |

