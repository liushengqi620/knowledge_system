# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Runs | Macro-F1 | Balanced Acc. | Inference/s | Params |
|---|---|---|---:|---:|---:|---:|---:|
| skab | anomaly | full | 1 | 0.8013 +/- 0.0000 | 0.7903 +/- 0.0000 | 2641.5 | 66246 |
| skab | anomaly | no_graph | 1 | 0.7177 +/- 0.0000 | 0.7128 +/- 0.0000 | 3211.3 | 66246 |
| skab | anomaly | no_path_fusion | 1 | 0.6818 +/- 0.0000 | 0.6985 +/- 0.0000 | 3611.2 | 66246 |
| skab | anomaly | no_reliability | 1 | 0.7465 +/- 0.0000 | 0.7434 +/- 0.0000 | 3076.0 | 66246 |
| skab | anomaly | single_scale | 1 | 0.7027 +/- 0.0000 | 0.7020 +/- 0.0000 | 5537.9 | 59078 |
| skab | anomaly | with_residual_evidence | 1 | 0.6793 +/- 0.0000 | 0.6900 +/- 0.0000 | 2661.5 | 66246 |

## Top Evidence Paths

### skab / anomaly / full / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight |
|---|---:|---:|---:|
| Accelerometer2RMS -> Accelerometer1RMS | 0.3210 | 0.5959 | 0.5521 |
| Accelerometer2RMS -> Thermocouple | 0.3021 | 0.5678 | 0.6241 |
| Accelerometer1RMS -> Volume Flow RateRMS | 0.2837 | 0.7318 | 0.9600 |
| Accelerometer1RMS -> Thermocouple | 0.2301 | 0.5077 | 0.4536 |
| Accelerometer1RMS -> Temperature | 0.1818 | 0.4699 | 0.4017 |

### skab / anomaly / no_graph / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight |
|---|---:|---:|---:|
| Volume Flow RateRMS -> Accelerometer2RMS | 0.2544 | 0.4958 | 0.0000 |
| Temperature -> Accelerometer2RMS | 0.1329 | 0.2775 | 0.0000 |
| Volume Flow RateRMS -> Accelerometer1RMS | 0.1264 | 0.3830 | 0.0000 |
| Thermocouple -> Accelerometer2RMS | 0.1197 | 0.3518 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.0568 | 0.3223 | 0.0000 |

### skab / anomaly / no_reliability / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight |
|---|---:|---:|---:|
| Accelerometer2RMS -> Thermocouple | 0.4003 | 1.0000 | 0.6994 |
| Accelerometer1RMS -> Temperature | 0.3277 | 1.0000 | 0.3054 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.2173 | 1.0000 | 0.5439 |
| Accelerometer2RMS -> Temperature | 0.1832 | 1.0000 | 0.1945 |
| Accelerometer1RMS -> Thermocouple | 0.1800 | 1.0000 | 0.3026 |

### skab / anomaly / single_scale / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight |
|---|---:|---:|---:|
| Thermocouple -> Accelerometer1RMS | 0.4854 | 0.7067 | 0.5931 |
| Volume Flow RateRMS -> Temperature | 0.4035 | 0.6908 | 0.8843 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.1733 | 0.4727 | 0.2584 |
| Thermocouple -> Accelerometer2RMS | 0.1660 | 0.4229 | 0.4524 |
| Temperature -> Thermocouple | 0.1487 | 0.4416 | 0.2216 |

### skab / anomaly / with_residual_evidence / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight |
|---|---:|---:|---:|
| Accelerometer2RMS -> Temperature | 0.4416 | 0.5418 | 0.4371 |
| Volume Flow RateRMS -> Thermocouple | 0.3817 | 0.5584 | 0.8583 |
| Volume Flow RateRMS -> Accelerometer1RMS | 0.3084 | 0.6860 | 0.9327 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.2268 | 0.4474 | 0.6431 |
| Thermocouple -> Accelerometer1RMS | 0.1950 | 0.2934 | 0.6721 |

