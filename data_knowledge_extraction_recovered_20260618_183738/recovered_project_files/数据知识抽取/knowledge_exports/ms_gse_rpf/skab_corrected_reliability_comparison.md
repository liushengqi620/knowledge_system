# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Prior mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full | none | 3 | 0.8368 +/- 0.0238 | 0.8350 +/- 0.0254 | 0.4652 | 0.0000 | 2958.6 | 66375 |
| skab | anomaly | no_reliability | none | 3 | 0.8389 +/- 0.0266 | 0.8382 +/- 0.0283 | 0.2850 | 0.0000 | 3100.6 | 66374 |

## Top Evidence Paths

### skab / anomaly / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | 0.6750 | 0.7697 | 0.9513 | 0.0000 |
| Temperature -> Volume Flow RateRMS | 0.6054 | 0.7659 | 0.7722 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.3080 | 0.7825 | 0.8545 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.3012 | 0.7017 | 0.3547 | 0.0000 |
| Thermocouple -> Volume Flow RateRMS | 0.1564 | 0.2060 | 0.2074 | 0.0000 |

### skab / anomaly / full / prior=none / seed=43

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Temperature -> Volume Flow RateRMS | 0.4597 | 0.5482 | 0.8390 | 0.0000 |
| Accelerometer2RMS -> Temperature | 0.4107 | 0.7579 | 0.8953 | 0.0000 |
| Current -> Volume Flow RateRMS | 0.1363 | 0.5935 | 0.4148 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | 0.1317 | 0.4048 | 0.8253 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.1199 | 0.4007 | 0.6119 | 0.0000 |

### skab / anomaly / full / prior=none / seed=44

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | 0.5818 | 0.6860 | 0.5794 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.1663 | 0.7068 | 0.1354 | 0.0000 |
| Accelerometer2RMS -> Temperature | 0.1626 | 0.6454 | 0.9262 | 0.0000 |
| Current -> Volume Flow RateRMS | 0.1608 | 0.3358 | 0.2811 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.1390 | 0.6637 | 0.2791 | 0.0000 |

### skab / anomaly / no_reliability / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Temperature -> Volume Flow RateRMS | 0.7120 | 1.0000 | 0.8880 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | 0.6878 | 1.0000 | 0.9504 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.3728 | 1.0000 | 0.8632 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.3718 | 1.0000 | 0.1924 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | 0.1135 | 1.0000 | 0.4629 | 0.0000 |

### skab / anomaly / no_reliability / prior=none / seed=43

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Temperature -> Volume Flow RateRMS | 0.4705 | 1.0000 | 0.9649 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | 0.4503 | 1.0000 | 0.5484 | 0.0000 |
| Accelerometer2RMS -> Temperature | 0.3888 | 1.0000 | 0.9442 | 0.0000 |
| Current -> Thermocouple | 0.1810 | 1.0000 | 0.8904 | 0.0000 |
| Current -> Volume Flow RateRMS | 0.1628 | 1.0000 | 0.4275 | 0.0000 |

### skab / anomaly / no_reliability / prior=none / seed=44

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | 0.5517 | 1.0000 | 0.5285 | 0.0000 |
| Current -> Volume Flow RateRMS | 0.1875 | 1.0000 | 0.2825 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.1716 | 1.0000 | 0.3379 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.1692 | 1.0000 | 0.1290 | 0.0000 |
| Voltage -> Volume Flow RateRMS | 0.1668 | 1.0000 | 0.1968 | 0.0000 |

