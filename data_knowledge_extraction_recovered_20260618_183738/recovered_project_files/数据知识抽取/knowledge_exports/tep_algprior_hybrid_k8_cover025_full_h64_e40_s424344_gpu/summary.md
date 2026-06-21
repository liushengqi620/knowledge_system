# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-hybrid-k8-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6262 +/- 0.0050 | 0.6443 +/- 0.0056 | 0.0000 | 0.0000 | 0.2484 | 0.3176 | 0.7647 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11900.7 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.6069 | 0.7790 | 0.3745 | 0.0000 | 0.5786 | 1.0 |
| xmeas_33 -> xmv_11 | xmeas_33 -> xmv_11 | 0.4488 | 0.7711 | 0.3417 | 0.0000 | 0.7819 | 1.0 |
| xmeas_12 -> xmv_11 | xmeas_12 -> xmv_11 | 0.3646 | 0.7386 | 0.3552 | 0.0000 | 0.8886 | 1.0 |
| xmv_10 -> xmeas_38 | xmv_10 -> xmeas_38 | 0.3345 | 0.8148 | 0.3671 | 0.0000 | 0.7439 | 1.0 |
| xmeas_31 -> xmv_11 | xmeas_31 -> xmv_11 | 0.3015 | 0.8672 | 0.4376 | 0.0000 | 0.9379 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmv_04 | xmeas_30 -> xmv_04 | 0.4586 | 0.7959 | 0.4145 | 0.0000 | 0.7025 | 1.0 |
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.4033 | 0.8603 | 0.1123 | 0.8059 | 0.8572 | 1.0 |
| xmv_09 -> xmv_04 | xmv_09 -> xmv_04 | 0.3635 | 0.7469 | 0.4505 | 0.0000 | 0.5296 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3354 | 0.7972 | 0.3409 | 0.8085 | 0.6150 | 1.0 |
| xmeas_03 -> xmv_04 | xmeas_03 -> xmv_04 | 0.3067 | 0.8554 | 0.3457 | 0.0000 | 0.9423 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmeas_09 | xmeas_18 -> xmeas_09 | 0.3028 | 0.8102 | 0.4051 | 0.0000 | 0.5486 | 1.0 |
| xmeas_28 -> xmeas_09 | xmeas_28 -> xmeas_09 | 0.2551 | 0.7508 | 0.2698 | 0.0000 | 0.5381 | 1.0 |
| xmeas_25 -> xmeas_09 | xmeas_25 -> xmeas_09 | 0.2290 | 0.7180 | 0.3853 | 0.0000 | 0.5508 | 1.0 |
| xmeas_23 -> xmv_04 | xmeas_23 -> xmv_04 | 0.1970 | 0.6538 | 0.3322 | 0.0000 | 0.8623 | 1.0 |
| xmeas_17 -> xmeas_24 | xmeas_17 -> xmeas_24 | 0.1890 | 0.4170 | 0.3376 | 0.0000 | 0.2118 | 1.0 |

