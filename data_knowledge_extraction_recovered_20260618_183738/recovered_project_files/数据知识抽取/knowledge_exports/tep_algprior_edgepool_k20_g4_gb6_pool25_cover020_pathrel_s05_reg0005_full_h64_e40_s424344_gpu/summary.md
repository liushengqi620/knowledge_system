# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6299 +/- 0.0089 | 0.6418 +/- 0.0073 | 0.0175 | 0.0175 | 0.1609 | 0.3067 | 0.7709 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12307.2 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4271 | 0.9029 | 0.1666 | 0.8102 | 0.7409 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3945 | 0.5916 | 0.1936 | 0.8852 | 0.1733 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3284 | 0.9002 | 0.1568 | 0.6149 | 0.8318 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3195 | 0.7765 | 0.5709 | 0.3180 | 0.8426 | 1.0 |
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.2804 | 0.8347 | 0.5508 | 0.0000 | 0.1725 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.5143 | 0.7447 | 0.3491 | 0.7191 | 0.6020 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.2863 | 0.7363 | 0.4793 | 0.0000 | 0.9953 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.2781 | 0.7381 | 0.4522 | 0.0000 | 0.9970 | 1.0 |
| xmeas_20 -> xmv_05 | xmeas_20 -> xmv_05 | 0.2416 | 0.6317 | 0.1073 | 0.8518 | 0.5642 | 1.0 |
| xmeas_36 -> xmeas_03 | xmeas_36 -> xmeas_03 | 0.2117 | 0.7495 | 0.4959 | 0.0000 | 0.3716 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_38 -> xmv_05 | xmeas_38 -> xmv_05 | 0.4294 | 0.6563 | 0.3453 | 0.0000 | 0.9081 | 1.0 |
| xmv_01 -> xmv_10 | xmv_01 -> xmv_10 | 0.3260 | 0.6923 | 0.4087 | 0.0000 | 0.2863 | 1.0 |
| xmv_06 -> xmeas_09 | xmv_06 -> xmeas_09 | 0.2719 | 0.4130 | 0.4695 | 0.0000 | 0.1864 | 1.0 |
| xmeas_01 -> xmeas_31 | xmeas_01 -> xmeas_31 | 0.2415 | 0.7069 | 0.5020 | 0.0000 | 0.9436 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2362 | 0.6874 | 0.1252 | 0.6697 | 0.8219 | 1.0 |

