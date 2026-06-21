# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | prior-cover@0.25+alg-prior-multiview-k16-g4-lag3@0.05+class-evidence@8 | 3 | 0.6156 +/- 0.0079 | 0.6354 +/- 0.0043 | 0.0351 | 0.0351 | 0.1891 | 0.2737 | 0.7239 | 1.0000 | 0.3345 | 0.00 | 0.00 | 0.00 | 0.0000 | on | 17205.5 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmv_09 | xmeas_18 -> xmv_09 | 0.3798 | 0.7126 | 0.1055 | 0.8471 | 0.3445 | 1.0 |
| xmv_10 -> xmv_11 | xmv_10 -> xmv_11 | 0.3689 | 0.7975 | 0.1767 | 0.8602 | 0.4826 | 1.0 |
| xmeas_17 -> xmv_11 | xmeas_17 -> xmv_11 | 0.3044 | 0.8321 | 0.1022 | 0.8239 | 0.2588 | 1.0 |
| xmv_09 -> xmeas_18 | xmv_09 -> xmeas_18 | 0.2600 | 0.7696 | 0.2211 | 0.8479 | 0.2600 | 1.0 |
| xmeas_28 -> xmeas_21 | xmeas_28 -> xmeas_21 | 0.1995 | 0.3624 | 0.5841 | 0.0000 | 0.0188 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.4594 | 0.8069 | 0.0880 | 0.7543 | 0.1705 | 1.0 |
| xmeas_08 -> xmv_04 | xmeas_08 -> xmv_04 | 0.3527 | 0.7170 | 0.1174 | 0.6011 | 0.3022 | 1.0 |
| xmeas_13 -> xmv_09 | xmeas_13 -> xmv_09 | 0.3141 | 0.8377 | 0.5930 | 0.0000 | 0.7437 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2962 | 0.8588 | 0.8293 | 0.7683 | 0.0436 | 1.0 |
| xmv_11 -> xmeas_22 | xmv_11 -> xmeas_22 | 0.2726 | 0.7809 | 0.8920 | 0.0000 | 0.4568 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_09 -> xmeas_18 | xmv_09 -> xmeas_18 | 0.2111 | 0.6825 | 0.0979 | 0.8479 | 0.3593 | 1.0 |
| xmv_04 -> xmv_07 | xmv_04 -> xmv_07 | 0.2050 | 0.8069 | 0.6148 | 0.0000 | 0.1994 | 1.0 |
| xmeas_30 -> xmv_05 | xmeas_30 -> xmv_05 | 0.1919 | 0.3959 | 0.4396 | 0.0000 | 0.1704 | 1.0 |
| xmeas_20 -> xmeas_36 | xmeas_20 -> xmeas_36 | 0.1917 | 0.3430 | 0.5638 | 0.0000 | 0.1611 | 1.0 |
| xmv_06 -> xmeas_34 | xmv_06 -> xmeas_34 | 0.1754 | 0.7641 | 0.8098 | 0.0000 | 0.0017 | 1.0 |

