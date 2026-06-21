# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Prior mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full | none | 3 | 0.7967 +/- 0.0281 | 0.7979 +/- 0.0239 | 0.3373 | 0.0000 | 3005.2 | 66374 |
| skab | anomaly | no_graph | none | 1 | 0.7155 +/- 0.0000 | 0.7279 +/- 0.0000 | n/a | 0.0000 | 3292.3 | 66374 |
| skab | anomaly | no_path_fusion | none | 1 | 0.5493 +/- 0.0000 | 0.5650 +/- 0.0000 | n/a | 0.0000 | 2845.2 | 66374 |
| skab | anomaly | no_reliability | none | 1 | 0.8745 +/- 0.0000 | 0.8736 +/- 0.0000 | n/a | 0.0000 | 3112.1 | 66374 |
| skab | anomaly | single_scale | none | 1 | 0.7709 +/- 0.0000 | 0.7679 +/- 0.0000 | n/a | 0.0000 | 5532.2 | 59206 |
| skab | anomaly | with_residual_evidence | none | 1 | 0.8455 +/- 0.0000 | 0.8459 +/- 0.0000 | n/a | 0.0000 | 2424.0 | 66374 |

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

### skab / anomaly / no_graph / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Volume Flow RateRMS -> Accelerometer1RMS | 0.3843 | 0.2317 | 0.0000 | 0.0000 |
| Volume Flow RateRMS -> Accelerometer2RMS | 0.1181 | 0.2196 | 0.0000 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.0907 | 0.1984 | 0.0000 | 0.0000 |
| Temperature -> Accelerometer2RMS | 0.0793 | 0.2580 | 0.0000 | 0.0000 |
| Temperature -> Accelerometer1RMS | 0.0777 | 0.1191 | 0.0000 | 0.0000 |

### skab / anomaly / no_reliability / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Temperature -> Volume Flow RateRMS | 0.7120 | 1.0000 | 0.8880 | 0.0000 |
| Accelerometer2RMS -> Volume Flow RateRMS | 0.6878 | 1.0000 | 0.9504 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.3728 | 1.0000 | 0.8632 | 0.0000 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.3718 | 1.0000 | 0.1924 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | 0.1135 | 1.0000 | 0.4629 | 0.0000 |

### skab / anomaly / single_scale / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Volume Flow RateRMS -> Accelerometer1RMS | 0.3272 | 0.4548 | 0.2964 | 0.0000 |
| Thermocouple -> Accelerometer1RMS | 0.2406 | 0.7035 | 0.2832 | 0.0000 |
| Accelerometer2RMS -> Temperature | 0.1882 | 0.6033 | 0.4039 | 0.0000 |
| Volume Flow RateRMS -> Thermocouple | 0.1502 | 0.7353 | 0.9924 | 0.0000 |
| Temperature -> Current | 0.1491 | 0.4993 | 0.1163 | 0.0000 |

### skab / anomaly / with_residual_evidence / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Volume Flow RateRMS -> Accelerometer2RMS | 0.6254 | 0.7546 | 0.9234 | 0.0000 |
| Thermocouple -> Volume Flow RateRMS | 0.5904 | 0.3390 | 0.9829 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.4929 | 0.6165 | 0.8267 | 0.0000 |
| Temperature -> Volume Flow RateRMS | 0.2398 | 0.5547 | 0.9398 | 0.0000 |
| Volume Flow RateRMS -> Thermocouple | 0.1796 | 0.4339 | 0.7163 | 0.0000 |

