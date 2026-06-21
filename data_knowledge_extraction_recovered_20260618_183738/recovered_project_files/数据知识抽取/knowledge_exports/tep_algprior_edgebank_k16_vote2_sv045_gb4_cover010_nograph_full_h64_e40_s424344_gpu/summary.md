# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.10+alg-prior-edge_bank-k16-lag3-vote2-sv0.45-vb0.15-gb4.0+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6138 +/- 0.0062 | 0.6377 +/- 0.0036 | 0.0000 | 0.0000 | 0.1060 | 0.3041 | 0.7432 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 19157.4 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_23 -> xmv_05 | xmeas_23 -> xmv_05 | 0.4063 | 0.8809 | 0.0967 | 0.7758 | 0.9974 | 1.0 |
| xmeas_26 -> xmeas_31 | xmeas_26 -> xmeas_31 | 0.3442 | 0.8164 | 0.4225 | 0.0000 | 0.8769 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3322 | 0.8241 | 0.7795 | 0.6741 | 0.1210 | 1.0 |
| xmeas_25 -> xmv_05 | xmeas_25 -> xmv_05 | 0.3246 | 0.7941 | 0.1616 | 0.6756 | 0.8676 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2848 | 0.8630 | 0.3540 | 0.6669 | 0.7936 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_22 -> xmv_11 | xmeas_22 -> xmv_11 | 0.4550 | 0.7180 | 0.3686 | 0.6536 | 0.5898 | 1.0 |
| xmv_07 -> xmeas_19 | xmv_07 -> xmeas_19 | 0.4056 | 0.5914 | 0.2887 | 0.0000 | 0.4295 | 1.0 |
| xmeas_18 -> xmv_04 | xmeas_18 -> xmv_04 | 0.4020 | 0.7366 | 0.3439 | 0.0000 | 0.7370 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4000 | 0.6280 | 0.2493 | 0.7794 | 0.6166 | 1.0 |
| xmv_09 -> xmv_11 | xmv_09 -> xmv_11 | 0.3941 | 0.7018 | 0.3479 | 0.0000 | 0.7063 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_08 -> xmeas_33 | xmv_08 -> xmeas_33 | 0.4231 | 0.2104 | 0.3354 | 0.0000 | 0.0137 | 1.0 |
| xmv_10 -> xmeas_28 | xmv_10 -> xmeas_28 | 0.2887 | 0.7609 | 0.3813 | 0.0000 | 0.2620 | 1.0 |
| xmv_06 -> xmv_02 | xmv_06 -> xmv_02 | 0.1966 | 0.5878 | 0.3425 | 0.0000 | 0.2588 | 1.0 |
| xmv_10 -> xmeas_03 | xmv_10 -> xmeas_03 | 0.1795 | 0.8738 | 0.4758 | 0.0000 | 0.1699 | 1.0 |
| xmeas_36 -> xmv_05 | xmeas_36 -> xmv_05 | 0.1751 | 0.4725 | 0.3236 | 0.0000 | 0.9599 | 1.0 |

