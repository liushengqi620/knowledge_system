# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+multihop@0.10+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6003 +/- 0.0153 | 0.6083 +/- 0.0183 | 0.0000 | 0.0000 | 0.0000 | 0.3152 | 0.7961 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 8661.7 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.3488 | 0.8470 | 0.3998 | 0.0000 | 0.2605 | 1.0 |
| xmv_11 -> xmeas_06 -> xmv_09 | xmv_11 -> xmeas_06 -> xmv_09 | 0.2793 | 0.7868 | 0.4630 | 0.0000 | 0.3154 | 2.0 |
| xmeas_09 -> xmv_11 -> xmeas_29 | xmeas_09 -> xmv_11 -> xmeas_29 | 0.2764 | 0.6544 | 0.3324 | 0.0000 | 0.6406 | 2.0 |
| xmeas_22 -> xmeas_31 -> xmeas_07 | xmeas_22 -> xmeas_31 -> xmeas_07 | 0.2707 | 0.6742 | 0.4539 | 0.0000 | 0.7791 | 2.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2521 | 0.8332 | 0.3399 | 0.0000 | 0.7326 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_31 -> xmv_04 | xmeas_31 -> xmv_04 | 0.5371 | 0.7848 | 0.4475 | 0.0000 | 0.4318 | 1.0 |
| xmeas_18 -> xmv_04 | xmeas_18 -> xmv_04 | 0.5106 | 0.6820 | 0.2456 | 0.0000 | 0.2893 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.5031 | 0.8779 | 0.4409 | 0.0000 | 0.7524 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.4965 | 0.8709 | 0.3107 | 0.0000 | 0.7435 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.4604 | 0.7874 | 0.2850 | 0.0000 | 0.4718 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmv_10 | xmeas_14 -> xmv_10 | 0.4151 | 0.6173 | 0.2797 | 0.0000 | 0.3981 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.3922 | 0.8121 | 0.3130 | 0.0000 | 0.4654 | 1.0 |
| xmeas_01 -> xmv_03 -> xmv_11 | xmeas_01 -> xmv_03 -> xmv_11 | 0.3279 | 0.8193 | 0.5672 | 0.0000 | 0.9521 | 2.0 |
| xmeas_19 -> xmeas_21 -> xmv_11 | xmeas_19 -> xmeas_21 -> xmv_11 | 0.3183 | 0.9051 | 0.4660 | 0.0000 | 0.9059 | 2.0 |
| xmeas_10 -> xmeas_21 -> xmv_11 | xmeas_10 -> xmeas_21 -> xmv_11 | 0.3148 | 0.8770 | 0.5050 | 0.0000 | 0.6046 | 2.0 |

