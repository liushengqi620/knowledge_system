# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-evidence-family3@0.25@8+path-aux@0.05+router@0.05 | 3 | 0.6058 +/- 0.0151 | 0.6121 +/- 0.0155 | 0.0000 | 0.0000 | 0.0000 | 0.2790 | 0.7554 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9146.1 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.4829 | 0.9059 | 0.2732 | 0.0000 | 0.3332 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.4722 | 0.9090 | 0.3044 | 0.0000 | 0.6237 | 1.0 |
| xmv_10 -> xmeas_41 | xmv_10 -> xmeas_41 | 0.3774 | 0.8073 | 0.2791 | 0.0000 | 0.2918 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.3269 | 0.7462 | 0.2710 | 0.0000 | 0.8901 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.2856 | 0.7907 | 0.2737 | 0.0000 | 0.5327 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_31 -> xmv_04 | xmeas_31 -> xmv_04 | 0.5102 | 0.8060 | 0.3170 | 0.0000 | 0.5298 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.4947 | 0.7941 | 0.2619 | 0.0000 | 0.6144 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.4473 | 0.6762 | 0.2741 | 0.0000 | 0.3265 | 1.0 |
| xmeas_26 -> xmv_04 | xmeas_26 -> xmv_04 | 0.4270 | 0.8291 | 0.3131 | 0.0000 | 0.6468 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.3997 | 0.7095 | 0.2961 | 0.0000 | 0.5618 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.5739 | 0.7498 | 0.3937 | 0.0000 | 0.3356 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.5145 | 0.8437 | 0.2992 | 0.0000 | 0.3623 | 1.0 |
| xmeas_07 -> xmv_10 | xmeas_07 -> xmv_10 | 0.3833 | 0.6951 | 0.2842 | 0.0000 | 0.4188 | 1.0 |
| xmeas_33 -> xmv_11 | xmeas_33 -> xmv_11 | 0.3465 | 0.6947 | 0.2989 | 0.0000 | 0.4646 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2384 | 0.6026 | 0.2671 | 0.0000 | 0.0229 | 1.0 |

