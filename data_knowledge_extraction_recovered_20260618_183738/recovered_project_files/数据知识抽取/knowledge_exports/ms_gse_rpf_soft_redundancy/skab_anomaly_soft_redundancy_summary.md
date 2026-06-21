# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full | none | 3 | 0.8150 +/- 0.0257 | 0.8164 +/- 0.0246 | 0.1657 | 0.1657 | 0.0000 | 0.0000 | 0.4616 | 3224.5 | 66375 |

## Top Evidence Paths

### skab / anomaly / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.3569 | 0.5291 | 0.9737 | 0.0000 | 0.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.3226 | 0.7130 | 0.9255 | 0.0000 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | Thermocouple -> Accelerometer2RMS | 0.2731 | 0.6162 | 0.8880 | 0.0000 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | Accelerometer2RMS -> Accelerometer1RMS | 0.1247 | 0.4324 | 0.6434 | 0.0000 | 0.0000 |
| Current -> Accelerometer2RMS | Current -> Accelerometer2RMS | 0.1123 | 0.2854 | 0.4690 | 0.0000 | 0.0000 |

### skab / anomaly / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.2751 | 0.4332 | 0.9928 | 0.0000 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.2468 | 0.5768 | 0.5187 | 0.0000 | 0.0000 |
| Pressure -> Volume Flow RateRMS | Pressure -> Volume Flow RateRMS | 0.2337 | 0.4898 | 0.5929 | 0.0000 | 0.0000 |
| Accelerometer2RMS -> Temperature | Accelerometer2RMS -> Temperature | 0.1987 | 0.6554 | 0.9970 | 0.0000 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | Accelerometer1RMS -> Volume Flow RateRMS | 0.1890 | 0.6012 | 0.4361 | 0.0000 | 0.0000 |

### skab / anomaly / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Thermocouple -> Volume Flow RateRMS | Thermocouple -> Volume Flow RateRMS | 0.2624 | 0.5028 | 0.4092 | 0.0000 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | Accelerometer1RMS -> Volume Flow RateRMS | 0.2340 | 0.5009 | 0.4567 | 0.0000 | 0.0000 |
| Temperature -> Current | Temperature -> Current | 0.2203 | 0.5015 | 0.3474 | 0.0000 | 0.0000 |
| Thermocouple -> Accelerometer1RMS | Thermocouple -> Accelerometer1RMS | 0.2136 | 0.6787 | 0.9768 | 0.0000 | 0.0000 |
| Temperature -> Thermocouple | Temperature -> Thermocouple | 0.1395 | 0.5584 | 0.3405 | 0.0000 | 0.0000 |

