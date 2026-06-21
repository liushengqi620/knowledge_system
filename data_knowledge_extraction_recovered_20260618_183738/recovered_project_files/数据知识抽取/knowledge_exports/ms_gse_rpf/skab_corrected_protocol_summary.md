# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Prior mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full | none | 3 | 0.7967 +/- 0.0281 | 0.7979 +/- 0.0239 | 0.3373 | 0.0000 | 3005.2 | 66374 |

## Top Evidence Paths

### skab / anomaly / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Temperature -> Volume Flow RateRMS | 0.5837 | 0.7529 | 0.8096 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.4421 | 0.6559 | 0.4734 | 0.0000 |
| Current -> Volume Flow RateRMS | 0.2857 | 0.5444 | 0.9571 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.2173 | 0.5085 | 0.9098 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.1868 | 0.6579 | 0.7663 | 0.0000 |

### skab / anomaly / full / prior=none / seed=43

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Temperature | 0.5033 | 0.7513 | 0.9979 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | 0.4856 | 0.6475 | 0.7461 | 0.0000 |
| Temperature -> Volume Flow RateRMS | 0.4476 | 0.3780 | 0.9983 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.1955 | 0.5940 | 0.7897 | 0.0000 |
| Current -> Thermocouple | 0.1182 | 0.2871 | 0.8377 | 0.0000 |

### skab / anomaly / full / prior=none / seed=44

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Temperature | 0.2991 | 0.5053 | 0.7991 | 0.0000 |
| Volume Flow RateRMS -> Current | 0.2646 | 0.6708 | 0.9461 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | 0.2353 | 0.4020 | 0.3145 | 0.0000 |
| Temperature -> Volume Flow RateRMS | 0.1968 | 0.6295 | 0.0201 | 0.0000 |
| Volume Flow RateRMS -> Temperature | 0.1666 | 0.7056 | 0.9039 | 0.0000 |

