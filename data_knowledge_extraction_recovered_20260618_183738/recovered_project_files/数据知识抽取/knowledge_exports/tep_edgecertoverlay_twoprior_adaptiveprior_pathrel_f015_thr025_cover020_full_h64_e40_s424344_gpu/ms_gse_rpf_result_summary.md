# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_cert_overlay-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6311 +/- 0.0067 | 0.6420 +/- 0.0068 | 0.0351 | 0.0351 | 0.0851 | 0.3313 | 0.7985 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9425.9 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4687 | 0.8240 | 0.0950 | 0.5570 | 0.8893 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4092 | 0.8897 | 0.1523 | 0.6637 | 0.7795 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2321 | 0.5614 | 0.2759 | 0.2743 | 0.8348 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2111 | 0.6668 | 0.4351 | 0.0000 | 0.1730 | 1.0 |
| xmv_10 -> xmeas_31 | xmv_10 -> xmeas_31 | 0.1997 | 0.7989 | 0.4526 | 0.0000 | 0.1571 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4865 | 0.7281 | 0.3567 | 0.4915 | 0.6182 | 1.0 |
| xmv_09 -> xmv_03 | xmv_09 -> xmv_03 | 0.2598 | 0.6867 | 0.3864 | 0.0000 | 0.6227 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.1980 | 0.5360 | 0.2248 | 0.3945 | 0.6671 | 1.0 |
| xmeas_08 -> xmeas_01 | xmeas_08 -> xmeas_01 | 0.1973 | 0.6728 | 0.1195 | 0.1428 | 0.8792 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.1795 | 0.8637 | 0.8580 | 0.6458 | 0.8176 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.4966 | 0.7477 | 0.5262 | 0.0000 | 0.1344 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4132 | 0.7689 | 0.2786 | 0.5647 | 0.7981 | 1.0 |
| xmeas_07 -> xmeas_09 | xmeas_07 -> xmeas_09 | 0.3839 | 0.4556 | 0.3948 | 0.0000 | 0.0530 | 1.0 |
| xmeas_30 -> xmv_04 | xmeas_30 -> xmv_04 | 0.2785 | 0.7895 | 0.3816 | 0.0000 | 0.4278 | 1.0 |
| xmeas_41 -> xmeas_01 | xmeas_41 -> xmeas_01 | 0.2438 | 0.4007 | 0.5327 | 0.0000 | 0.3718 | 1.0 |

