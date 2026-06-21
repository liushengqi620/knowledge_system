# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert@0.00 | group_pair_inclusive+dedup-hard+prior-cover@0.05+prior-cal@0.10+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6088 +/- 0.0120 | 0.6168 +/- 0.0127 | 0.0000 | 0.0000 | 0.0284 | 0.2910 | 0.7668 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 8021.8 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.5238 | 0.8402 | 0.3597 | 0.0000 | 0.2829 | 1.0 |
| xmv_11 -> xmeas_03 | xmv_11 -> xmeas_03 | 0.3339 | 0.6911 | 0.2712 | 0.0000 | 0.8718 | 1.0 |
| xmv_11 -> xmeas_11 | xmv_11 -> xmeas_11 | 0.3257 | 0.6620 | 0.2602 | 0.5654 | 0.5005 | 1.0 |
| xmeas_03 -> xmv_05 | xmeas_03 -> xmv_05 | 0.2730 | 0.7682 | 0.2960 | 0.0000 | 0.9457 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.2324 | 0.6890 | 0.3320 | 0.0000 | 0.9255 | 1.0 |

### tep / event_quality_class_id / full / prior=expert@0.00 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_09 -> xmv_04 | xmv_09 -> xmv_04 | 0.6076 | 0.7148 | 0.3000 | 0.0000 | 0.2908 | 1.0 |
| xmeas_16 -> xmv_04 | xmeas_16 -> xmv_04 | 0.5877 | 0.7462 | 0.2669 | 0.0000 | 0.6656 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.5616 | 0.7544 | 0.2507 | 0.0000 | 0.6128 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.4673 | 0.7396 | 0.2693 | 0.0000 | 0.7184 | 1.0 |
| xmeas_26 -> xmv_04 | xmeas_26 -> xmv_04 | 0.3566 | 0.5330 | 0.2925 | 0.0000 | 0.4680 | 1.0 |

### tep / event_quality_class_id / full / prior=expert@0.00 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.4710 | 0.8210 | 0.3114 | 0.0000 | 0.5054 | 1.0 |
| xmeas_33 -> xmv_11 | xmeas_33 -> xmv_11 | 0.4316 | 0.7596 | 0.3205 | 0.0000 | 0.5531 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.3007 | 0.8009 | 0.3059 | 0.0000 | 0.6384 | 1.0 |
| xmv_02 -> xmv_10 | xmv_02 -> xmv_10 | 0.2662 | 0.5819 | 0.3293 | 0.0000 | 0.2981 | 1.0 |
| xmeas_33 -> xmv_10 | xmeas_33 -> xmv_10 | 0.2376 | 0.6375 | 0.3234 | 0.0000 | 0.2833 | 1.0 |

