# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+edge-cal-f0.20-b4.0-reg1.00+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6203 +/- 0.0078 | 0.6419 +/- 0.0056 | 0.0175 | 0.0175 | 0.3039 | 0.3346 | 0.7650 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 17436.1 | 153678 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmeas_18 | xmeas_14 -> xmeas_18 | 0.3266 | 0.5613 | 0.3134 | 0.3314 | 0.2022 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2995 | 0.7094 | 0.5946 | 0.0000 | 0.1615 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2900 | 0.8562 | 0.4725 | 0.6922 | 0.8371 | 1.0 |
| xmv_08 -> xmeas_38 | xmv_08 -> xmeas_38 | 0.2605 | 0.5273 | 0.3505 | 0.0000 | 0.1188 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2299 | 0.5836 | 0.1426 | 0.8649 | 0.6827 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmv_04 | xmeas_18 -> xmv_04 | 0.5646 | 0.7481 | 0.5454 | 0.0000 | 0.7378 | 1.0 |
| xmeas_25 -> xmv_04 | xmeas_25 -> xmv_04 | 0.5314 | 0.8037 | 0.2154 | 0.6383 | 0.7878 | 1.0 |
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.5025 | 0.8609 | 0.1471 | 0.8109 | 0.8473 | 1.0 |
| xmeas_21 -> xmv_10 | xmeas_21 -> xmv_10 | 0.4077 | 0.7418 | 0.7170 | 0.0000 | 0.9528 | 1.0 |
| xmeas_10 -> xmeas_01 | xmeas_10 -> xmeas_01 | 0.3601 | 0.8170 | 0.5348 | 0.3408 | 0.9657 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_13 -> xmv_05 | xmeas_13 -> xmv_05 | 0.2672 | 0.3099 | 0.2411 | 0.6948 | 0.8373 | 1.0 |
| xmeas_08 -> xmeas_33 | xmeas_08 -> xmeas_33 | 0.2592 | 0.7641 | 0.4392 | 0.0000 | 0.6105 | 1.0 |
| xmeas_35 -> xmeas_37 | xmeas_35 -> xmeas_37 | 0.2480 | 0.3584 | 0.4425 | 0.0000 | 0.0208 | 1.0 |
| xmeas_27 -> xmv_05 | xmeas_27 -> xmv_05 | 0.2215 | 0.2834 | 0.3637 | 0.0000 | 0.9958 | 1.0 |
| xmeas_05 -> xmv_01 | xmeas_05 -> xmv_01 | 0.1959 | 0.6379 | 0.5735 | 0.0000 | 0.3938 | 1.0 |

