# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-hybrid-k16-lag3@0.10+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6125 +/- 0.0047 | 0.6239 +/- 0.0046 | 0.0175 | 0.0175 | 0.3337 | 0.3328 | 0.7242 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7975.6 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_16 -> xmv_11 | xmeas_16 -> xmv_11 | 0.4607 | 0.8279 | 0.1806 | 0.8002 | 0.5211 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.3974 | 0.8372 | 0.2421 | 0.7579 | 0.3195 | 1.0 |
| xmeas_34 -> xmv_11 | xmeas_34 -> xmv_11 | 0.3781 | 0.7045 | 0.2813 | 0.0000 | 0.3580 | 1.0 |
| xmeas_37 -> xmv_11 | xmeas_37 -> xmv_11 | 0.2770 | 0.8021 | 0.3509 | 0.0000 | 0.6096 | 1.0 |
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.2362 | 0.6968 | 0.3040 | 0.0000 | 0.4701 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_36 -> xmv_04 | xmeas_36 -> xmv_04 | 0.5626 | 0.8412 | 0.3192 | 0.6419 | 0.5708 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.3976 | 0.7838 | 0.2526 | 0.6175 | 0.5430 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.3930 | 0.7879 | 0.2431 | 0.7514 | 0.7112 | 1.0 |
| xmeas_13 -> xmv_04 | xmeas_13 -> xmv_04 | 0.3783 | 0.7856 | 0.2021 | 0.7388 | 0.7146 | 1.0 |
| xmeas_31 -> xmv_11 | xmeas_31 -> xmv_11 | 0.3663 | 0.7710 | 0.2004 | 0.8237 | 0.3975 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmv_11 | xmeas_37 -> xmv_11 | 0.4104 | 0.7573 | 0.2702 | 0.0000 | 0.5011 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.4064 | 0.6385 | 0.3704 | 0.0000 | 0.2809 | 1.0 |
| xmeas_40 -> xmv_05 | xmeas_40 -> xmv_05 | 0.3809 | 0.7486 | 0.2821 | 0.0000 | 0.9803 | 1.0 |
| xmeas_39 -> xmv_10 | xmeas_39 -> xmv_10 | 0.3597 | 0.5622 | 0.2676 | 0.0000 | 0.2906 | 1.0 |
| xmv_11 -> xmeas_35 | xmv_11 -> xmeas_35 | 0.3248 | 0.7333 | 0.2476 | 0.7525 | 0.4851 | 1.0 |

