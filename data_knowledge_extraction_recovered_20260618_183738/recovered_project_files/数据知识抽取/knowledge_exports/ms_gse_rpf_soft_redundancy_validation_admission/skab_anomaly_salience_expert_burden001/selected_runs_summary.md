# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full_admitted | none | 3 | 0.8307 +/- 0.0141 | 0.8281 +/- 0.0164 | 0.2778 | 0.2778 | 0.0000 | 0.5026 | 0.4630 | 3194.6 | 66375 |

## Top Evidence Paths

### skab / anomaly / full_admitted / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.3569 | 0.5291 | 0.9737 | 0.0000 | 0.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.3226 | 0.7130 | 0.9255 | 0.0000 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | Thermocouple -> Accelerometer2RMS | 0.2731 | 0.6162 | 0.8880 | 0.0000 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | Accelerometer2RMS -> Accelerometer1RMS | 0.1247 | 0.4324 | 0.6434 | 0.0000 | 0.0000 |
| Current -> Accelerometer2RMS | Current -> Accelerometer2RMS | 0.1123 | 0.2854 | 0.4690 | 0.0000 | 0.0000 |

### skab / anomaly / full_admitted / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Accelerometer1RMS -> Volume Flow RateRMS | Accelerometer1RMS -> Volume Flow RateRMS | 0.3120 | 0.9086 | 1.0221 | 0.0000 | 1.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.3041 | 0.8633 | 0.9020 | 0.0000 | 1.0000 |
| Pressure -> Volume Flow RateRMS | Pressure -> Volume Flow RateRMS | 0.2721 | 0.3988 | 0.4482 | 0.0000 | 1.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.2524 | 0.0546 | 0.6373 | 0.0000 | 1.0000 |
| Voltage -> Volume Flow RateRMS | Voltage -> Volume Flow RateRMS | 0.2041 | 0.2018 | 0.6372 | 0.0000 | 1.0000 |

### skab / anomaly / full_admitted / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Thermocouple -> Volume Flow RateRMS | Thermocouple -> Volume Flow RateRMS | 0.2917 | 0.4801 | 0.5424 | 0.0000 | 0.4772 |
| Accelerometer1RMS -> Volume Flow RateRMS | Accelerometer1RMS -> Volume Flow RateRMS | 0.2623 | 0.4533 | 0.6016 | 0.0000 | 1.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.2577 | 0.6683 | 0.4656 | 0.0000 | 0.4772 |
| Pressure -> Volume Flow RateRMS | Pressure -> Volume Flow RateRMS | 0.2063 | 0.4194 | 0.4136 | 0.0000 | 0.4772 |
| Current -> Volume Flow RateRMS | Current -> Volume Flow RateRMS | 0.1726 | 0.5201 | 0.6053 | 0.0000 | 0.4772 |

