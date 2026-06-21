# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Duplicate rate | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full | expert@0.00 | 3 | 0.8117 +/- 0.0297 | 0.8140 +/- 0.0260 | 0.2010 | 0.2010 | 0.0208 | 0.0000 | 0.4705 | 3206.5 | 66375 |

## Top Evidence Paths

### skab / anomaly / full / prior=expert@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.3898 | 0.8809 | 0.9154 | 0.0000 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | Accelerometer1RMS -> Volume Flow RateRMS | 0.3301 | 0.6941 | 0.3557 | 0.3000 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.2942 | 0.5196 | 0.9315 | 0.0000 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | Thermocouple -> Accelerometer2RMS | 0.1769 | 0.5676 | 0.7578 | 0.0000 | 0.0000 |
| Thermocouple -> Volume Flow RateRMS | Thermocouple -> Volume Flow RateRMS | 0.1505 | 0.1794 | 0.6915 | 0.0000 | 0.0000 |

### skab / anomaly / full / prior=expert@0.00 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.2928 | 0.7987 | 0.6463 | 0.0000 | 0.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.2705 | 0.8999 | 0.9992 | 0.0000 | 0.0000 |
| Accelerometer2RMS -> Temperature | Accelerometer2RMS -> Temperature | 0.2337 | 0.7188 | 0.9929 | 0.0000 | 0.0000 |
| Current -> Temperature | Current -> Temperature | 0.1818 | 0.7333 | 0.4006 | 0.4500 | 0.0000 |
| Pressure -> Volume Flow RateRMS | Pressure -> Volume Flow RateRMS | 0.1726 | 0.6143 | 0.5884 | 0.3500 | 0.0000 |

### skab / anomaly / full / prior=expert@0.00 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight |
|---|---|---:|---:|---:|---:|---:|
| Thermocouple -> Accelerometer1RMS | Thermocouple -> Accelerometer1RMS | 0.3457 | 0.7023 | 0.9896 | 0.0000 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | Accelerometer2RMS -> Volume Flow RateRMS | 0.2491 | 0.4974 | 0.6689 | 0.0000 | 0.0000 |
| Pressure -> Accelerometer2RMS | Pressure -> Accelerometer2RMS | 0.2145 | 0.8399 | 0.3886 | 0.0000 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | Accelerometer1RMS -> Accelerometer2RMS | 0.1883 | 0.7471 | 0.3701 | 0.0000 | 0.0000 |
| Temperature -> Volume Flow RateRMS | Temperature -> Volume Flow RateRMS | 0.1763 | 0.6965 | 0.7208 | 0.0000 | 0.0000 |

