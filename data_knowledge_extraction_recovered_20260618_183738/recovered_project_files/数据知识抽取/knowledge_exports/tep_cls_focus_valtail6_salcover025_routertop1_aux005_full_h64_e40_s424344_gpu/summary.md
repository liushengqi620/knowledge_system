# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | salience-cover@0.25+class-evidence-focus-explicit6-router1-temp0.50@8+router@0.05 | 3 | 0.6110 +/- 0.0041 | 0.6318 +/- 0.0021 | 0.0000 | 0.0000 | 0.0000 | 0.1570 | 0.6808 | 1.0000 | 0.3321 | 0.00 | 0.00 | 0.00 | 0.0000 | on | 17316.2 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_04 -> xmeas_19 | xmeas_04 -> xmeas_19 | 0.3875 | 0.6775 | 0.1714 | 0.0000 | 1.0000 | 1.0 |
| xmeas_32 -> xmv_11 | xmeas_32 -> xmv_11 | 0.2293 | 0.6312 | 0.5384 | 0.0000 | 0.0000 | 1.0 |
| xmeas_19 -> xmeas_36 | xmeas_19 -> xmeas_36 | 0.2115 | 0.7089 | 0.2794 | 0.0000 | 1.0000 | 1.0 |
| xmeas_18 -> xmeas_11 | xmeas_18 -> xmeas_11 | 0.1875 | 0.7848 | 0.5283 | 0.0000 | 0.3251 | 1.0 |
| xmeas_18 -> xmeas_36 | xmeas_18 -> xmeas_36 | 0.1785 | 0.7684 | 0.3442 | 0.0000 | 1.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_40 -> xmv_09 | xmeas_40 -> xmv_09 | 0.2711 | 0.4127 | 0.4979 | 0.0000 | 0.8299 | 1.0 |
| xmeas_10 -> xmeas_16 | xmeas_10 -> xmeas_16 | 0.2029 | 0.6580 | 0.7892 | 0.0000 | 0.1403 | 1.0 |
| xmeas_39 -> xmeas_18 | xmeas_39 -> xmeas_18 | 0.1719 | 0.3493 | 0.5000 | 0.0000 | 0.8831 | 1.0 |
| xmeas_36 -> xmv_11 | xmeas_36 -> xmv_11 | 0.1702 | 0.3486 | 0.2497 | 0.0000 | 1.0000 | 1.0 |
| xmv_10 -> xmeas_17 | xmv_10 -> xmeas_17 | 0.1645 | 0.4654 | 0.3994 | 0.0000 | 0.8096 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_40 -> xmeas_20 | xmeas_40 -> xmeas_20 | 0.2618 | 0.6911 | 0.3635 | 0.0000 | 1.0000 | 1.0 |
| xmeas_39 -> xmeas_21 | xmeas_39 -> xmeas_21 | 0.2568 | 0.5240 | 0.5372 | 0.0000 | 0.0000 | 1.0 |
| xmeas_19 -> xmeas_21 | xmeas_19 -> xmeas_21 | 0.1951 | 0.7824 | 0.7168 | 0.0000 | 0.0000 | 1.0 |
| xmeas_18 -> xmeas_20 | xmeas_18 -> xmeas_20 | 0.1882 | 0.5839 | 0.4101 | 0.0000 | 0.7639 | 1.0 |
| xmeas_08 -> xmeas_13 | xmeas_08 -> xmeas_13 | 0.1813 | 0.2203 | 0.2648 | 0.0000 | 0.7027 | 1.0 |

