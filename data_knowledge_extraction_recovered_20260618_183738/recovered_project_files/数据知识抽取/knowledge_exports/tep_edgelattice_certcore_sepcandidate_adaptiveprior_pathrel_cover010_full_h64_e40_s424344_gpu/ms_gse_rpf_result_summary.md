# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+graph-core-cert-k8-g3-f0.05-thr0.35-t0.05-d1.00-grp0.40-stab0.50-p0.20-sep-path-candidate+prior-cover@0.10+alg-prior-edge_lattice-k8-g3-lag3-vote2-sv0.45-vb0.12-pool3.0-rank0.30@0.04+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6238 +/- 0.0061 | 0.6372 +/- 0.0021 | 0.0175 | 0.0175 | 0.0306 | 0.0495 | 0.7749 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10402.5 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_09 -> xmeas_21 | xmv_09 -> xmeas_21 | 0.4017 | 0.5211 | 0.3519 | 0.0000 | 0.0282 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3224 | 0.6805 | 0.3589 | 0.1840 | 0.0381 | 1.0 |
| xmv_05 -> xmeas_21 | xmv_05 -> xmeas_21 | 0.3060 | 0.7719 | 0.4113 | 0.0000 | 0.0727 | 1.0 |
| xmeas_32 -> xmv_02 | xmeas_32 -> xmv_02 | 0.2876 | 0.4290 | 0.2689 | 0.0000 | 0.0027 | 1.0 |
| xmv_05 -> xmeas_09 | xmv_05 -> xmeas_09 | 0.2817 | 0.7504 | 0.3321 | 0.0000 | 0.0743 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_24 -> xmv_10 | xmeas_24 -> xmv_10 | 0.3495 | 0.4257 | 0.4214 | 0.0000 | 0.0062 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3216 | 0.4349 | 0.4864 | 0.0000 | 0.1023 | 1.0 |
| xmeas_31 -> xmv_06 | xmeas_31 -> xmv_06 | 0.2921 | 0.6247 | 0.4005 | 0.0000 | 0.0202 | 1.0 |
| xmeas_09 -> xmeas_01 | xmeas_09 -> xmeas_01 | 0.2613 | 0.6141 | 0.6039 | 0.0000 | 0.0542 | 1.0 |
| xmeas_31 -> xmv_10 | xmeas_31 -> xmv_10 | 0.2470 | 0.3747 | 0.1657 | 0.1585 | 0.0381 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2631 | 0.8489 | 0.5806 | 0.1923 | 0.0704 | 1.0 |
| xmeas_08 -> xmeas_04 | xmeas_08 -> xmeas_04 | 0.2343 | 0.7487 | 0.1161 | 0.1513 | 0.0403 | 1.0 |
| xmeas_33 -> xmeas_09 | xmeas_33 -> xmeas_09 | 0.2317 | 0.6176 | 0.3614 | 0.0000 | 0.0504 | 1.0 |
| xmeas_24 -> xmeas_23 | xmeas_24 -> xmeas_23 | 0.2072 | 0.6317 | 0.5401 | 0.0000 | 0.0456 | 1.0 |
| xmeas_41 -> xmeas_04 | xmeas_41 -> xmeas_04 | 0.1972 | 0.4895 | 0.3889 | 0.0000 | 0.0106 | 1.0 |

