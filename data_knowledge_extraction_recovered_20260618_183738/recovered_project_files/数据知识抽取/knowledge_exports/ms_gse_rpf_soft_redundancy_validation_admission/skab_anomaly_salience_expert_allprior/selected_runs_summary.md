# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full_admitted | expert@0.00 | 1 | 0.8157 +/- 0.0000 | 0.8097 +/- 0.0000 | n/a | n/a | 0.0197 | 0.0000 | 0.4730 | 3247.1 | 66375 |
| skab | anomaly | full_admitted | none | 2 | 0.8352 +/- 0.0155 | 0.8352 +/- 0.0160 | 0.2500 | 0.2500 | 0.0000 | 0.3394 | 0.4575 | 3180.3 | 66375 |

## Top Evidence Paths

### skab / anomaly / full_admitted / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.3569 | 0.5291 | 0.9737 | 0.0000 | 0.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.3226 | 0.7130 | 0.9255 | 0.0000 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | Thermocouple -> Accelerometer2RMS | 0.2731 | 0.6162 | 0.8880 | 0.0000 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | Accelerometer2RMS -> Accelerometer1RMS | 0.1247 | 0.4324 | 0.6434 | 0.0000 | 0.0000 |
| Current -> Accelerometer2RMS | Current -> Accelerometer2RMS | 0.1123 | 0.2854 | 0.4690 | 0.0000 | 0.0000 |

### skab / anomaly / full_admitted / prior=expert@0.00 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.2928 | 0.7987 | 0.6463 | 0.0000 | 0.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.2705 | 0.8999 | 0.9992 | 0.0000 | 0.0000 |
| Accelerometer2RMS -> Temperature | Accelerometer2RMS -> Temperature | 0.2337 | 0.7188 | 0.9929 | 0.0000 | 0.0000 |
| Current -> Temperature | Current -> Temperature | 0.1818 | 0.7333 | 0.4006 | 0.4500 | 0.0000 |
| Pressure -> Volume Flow RateRMS | Pressure -> Volume Flow RateRMS | 0.1726 | 0.6143 | 0.5884 | 0.3500 | 0.0000 |

### skab / anomaly / full_admitted / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Thermocouple -> Volume Flow RateRMS | Thermocouple -> Volume Flow RateRMS | 0.2917 | 0.4801 | 0.5424 | 0.0000 | 0.4772 |
| Accelerometer1RMS -> Volume Flow RateRMS | Accelerometer1RMS -> Volume Flow RateRMS | 0.2623 | 0.4533 | 0.6016 | 0.0000 | 1.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.2577 | 0.6683 | 0.4656 | 0.0000 | 0.4772 |
| Pressure -> Volume Flow RateRMS | Pressure -> Volume Flow RateRMS | 0.2063 | 0.4194 | 0.4136 | 0.0000 | 0.4772 |
| Current -> Volume Flow RateRMS | Current -> Volume Flow RateRMS | 0.1726 | 0.5201 | 0.6053 | 0.0000 | 0.4772 |

