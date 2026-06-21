# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-evid-cons-s0.10-thr0.05-t0.03+prior-cover@0.20+alg-prior-edge_pool-k8-g3-lag3-vote2-sv0.55-vb0.15-pool2.0-rank0.35@0.05+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@6+path-aux@0.05+router@0.05 | 1 | 0.0863 +/- 0.0000 | 0.1313 +/- 0.0000 | n/a | n/a | 0.2037 | 0.0384 | 0.2031 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12625.3 | 59697 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmeas_40 | xmeas_09 -> xmeas_40 | 0.1751 | 0.5143 | 0.1740 | 0.0000 | 0.0852 | 1.0 |
| xmeas_07 -> xmv_10 | xmeas_07 -> xmv_10 | 0.1246 | 0.4665 | 0.1633 | 0.0000 | 0.0441 | 1.0 |
| xmeas_06 -> xmeas_24 | xmeas_06 -> xmeas_24 | 0.1223 | 0.4891 | 0.1670 | 0.0000 | 0.0224 | 1.0 |
| xmeas_21 -> xmeas_33 | xmeas_21 -> xmeas_33 | 0.1162 | 0.5117 | 0.1647 | 0.0000 | 0.0044 | 1.0 |
| xmeas_06 -> xmeas_27 | xmeas_06 -> xmeas_27 | 0.1137 | 0.5241 | 0.1710 | 0.0000 | 0.0000 | 1.0 |

