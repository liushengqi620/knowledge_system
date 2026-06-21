# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Prior mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full | expert@0.00 | 1 | 0.8670 +/- 0.0000 | 0.8657 +/- 0.0000 | n/a | 0.0153 | 3147.6 | 66375 |
| skab | anomaly | full | expert_llm@0.00 | 1 | 0.8670 +/- 0.0000 | 0.8657 +/- 0.0000 | n/a | 0.0153 | 3031.5 | 66375 |
| skab | anomaly | full | expert_llm@0.10 | 1 | 0.8376 +/- 0.0000 | 0.8405 +/- 0.0000 | n/a | 0.0209 | 3420.7 | 66375 |
| skab | anomaly | full | none | 3 | 0.8368 +/- 0.0238 | 0.8350 +/- 0.0254 | 0.4652 | 0.0000 | 2958.6 | 66375 |

## Top Evidence Paths

### skab / anomaly / full / prior=expert_llm@0.10 / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | 0.6767 | 0.6705 | 0.9732 | 0.0000 |
| Temperature -> Volume Flow RateRMS | 0.6496 | 0.7681 | 0.8883 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.3965 | 0.8120 | 0.8072 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.2814 | 0.7908 | 0.1753 | 0.3000 |
| Thermocouple -> Volume Flow RateRMS | 0.2484 | 0.2683 | 0.2523 | 0.0000 |

### skab / anomaly / full / prior=expert_llm@0.00 / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | 0.6591 | 0.7167 | 0.9379 | 0.0000 |
| Temperature -> Volume Flow RateRMS | 0.6418 | 0.7473 | 0.8382 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.3223 | 0.5852 | 0.3690 | 0.3000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.2785 | 0.6970 | 0.8741 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | 0.1165 | 0.3345 | 0.4730 | 0.0000 |

### skab / anomaly / full / prior=expert@0.00 / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Volume Flow RateRMS | 0.6591 | 0.7167 | 0.9379 | 0.0000 |
| Temperature -> Volume Flow RateRMS | 0.6418 | 0.7473 | 0.8382 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.3223 | 0.5852 | 0.3690 | 0.3000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.2785 | 0.6970 | 0.8741 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | 0.1165 | 0.3345 | 0.4730 | 0.0000 |

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

