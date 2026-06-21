# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Prior mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| skab | anomaly | full | expert@0.00 | 1 | 0.7805 +/- 0.0000 | 0.7690 +/- 0.0000 | n/a | 0.0201 | 2489.3 | 66374 |
| skab | anomaly | full | expert@0.10 | 1 | 0.7533 +/- 0.0000 | 0.7404 +/- 0.0000 | n/a | 0.0206 | 3006.3 | 66374 |
| skab | anomaly | full | expert@0.50 | 1 | 0.7361 +/- 0.0000 | 0.7198 +/- 0.0000 | n/a | 0.0397 | 3111.9 | 66374 |
| skab | anomaly | full | none | 3 | 0.6548 +/- 0.1208 | 0.6631 +/- 0.1050 | 0.1352 | 0.0000 | 2943.2 | 66374 |

## Top Evidence Paths

### skab / anomaly / full / prior=expert@0.10 / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Accelerometer1RMS | 0.4414 | 0.6251 | 0.5937 | 0.0000 |
| Volume Flow RateRMS -> Temperature | 0.2812 | 0.5722 | 0.8263 | 0.0000 |
| Thermocouple -> Volume Flow RateRMS | 0.2508 | 0.4997 | 0.7924 | 0.0000 |
| Thermocouple -> Accelerometer1RMS | 0.2425 | 0.6156 | 0.7849 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.2055 | 0.4241 | 0.5136 | 0.0000 |

### skab / anomaly / full / prior=expert@0.50 / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Thermocouple -> Volume Flow RateRMS | 0.4360 | 0.6631 | 0.7995 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.3537 | 0.6157 | 0.9066 | 0.0000 |
| Pressure -> Accelerometer1RMS | 0.3472 | 0.5574 | 0.3266 | 0.0000 |
| Current -> Accelerometer1RMS | 0.2130 | 0.3083 | 0.1411 | 0.0000 |
| Volume Flow RateRMS -> Accelerometer2RMS | 0.1362 | 0.6013 | 0.8421 | 0.0000 |

### skab / anomaly / full / prior=expert@0.00 / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Thermocouple -> Volume Flow RateRMS | 0.3022 | 0.4922 | 0.9012 | 0.0000 |
| Volume Flow RateRMS -> Temperature | 0.2507 | 0.5717 | 0.7702 | 0.0000 |
| Accelerometer2RMS -> Thermocouple | 0.2214 | 0.5844 | 0.6477 | 0.0000 |
| Temperature -> Volume Flow RateRMS | 0.1679 | 0.4352 | 0.2142 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.1639 | 0.4892 | 0.3963 | 0.0000 |

### skab / anomaly / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Thermocouple -> Volume Flow RateRMS | 0.3049 | 0.4355 | 0.9572 | 0.0000 |
| Thermocouple -> Accelerometer1RMS | 0.2626 | 0.4702 | 0.7527 | 0.0000 |
| Accelerometer2RMS -> Thermocouple | 0.2266 | 0.6109 | 0.5681 | 0.0000 |
| Volume Flow RateRMS -> Temperature | 0.1893 | 0.5580 | 0.7035 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.1647 | 0.4643 | 0.4215 | 0.0000 |

### skab / anomaly / full / prior=none / seed=43

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Pressure -> Temperature | 0.2514 | 0.5023 | 0.2816 | 0.0000 |
| Accelerometer1RMS -> Temperature | 0.2428 | 0.5705 | 0.2447 | 0.0000 |
| Pressure -> Volume Flow RateRMS | 0.2272 | 0.4911 | 0.7152 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.1961 | 0.6373 | 0.4606 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.1929 | 0.5861 | 0.1672 | 0.0000 |

### skab / anomaly / full / prior=none / seed=44

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Current -> Temperature | 0.3982 | 0.6246 | 0.3699 | 0.0000 |
| Accelerometer1RMS -> Temperature | 0.3906 | 0.6215 | 0.4783 | 0.0000 |
| Temperature -> Accelerometer1RMS | 0.2673 | 0.5568 | 0.8131 | 0.0000 |
| Volume Flow RateRMS -> Temperature | 0.1870 | 0.4639 | 0.7520 | 0.0000 |
| Current -> Accelerometer1RMS | 0.1521 | 0.5622 | 0.1659 | 0.0000 |

