# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Runs | Macro-F1 | Balanced Acc. | Prior mass | Inference/s | Params |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| cmapss | degradation_stage_id | full | none | 1 | 0.7050 +/- 0.0000 | 0.6990 +/- 0.0000 | 0.0000 | 1855.5 | 30791 |
| hydraulic | cooler | full | none | 1 | 0.9982 +/- 0.0000 | 0.9982 +/- 0.0000 | 0.0000 | 869.8 | 67271 |
| hydraulic | hydraulic_accumulator | full | none | 1 | 0.8479 +/- 0.0000 | 0.8509 +/- 0.0000 | 0.0000 | 1098.5 | 67304 |
| hydraulic | internal_pump_leakage | full | none | 1 | 0.9220 +/- 0.0000 | 0.9214 +/- 0.0000 | 0.0000 | 1020.1 | 67271 |
| hydraulic | valve | full | none | 1 | 0.6926 +/- 0.0000 | 0.7074 +/- 0.0000 | 0.0000 | 1056.6 | 67304 |
| skab | anomaly | full | expert@0.00 | 1 | 0.7805 +/- 0.0000 | 0.7690 +/- 0.0000 | 0.0201 | 2489.3 | 66374 |
| skab | anomaly | full | expert@0.10 | 1 | 0.7533 +/- 0.0000 | 0.7404 +/- 0.0000 | 0.0206 | 3006.3 | 66374 |
| skab | anomaly | full | expert@0.50 | 1 | 0.7361 +/- 0.0000 | 0.7198 +/- 0.0000 | 0.0397 | 3111.9 | 66374 |
| skab | anomaly | full | none | 1 | 0.8249 +/- 0.0000 | 0.8114 +/- 0.0000 | 0.0000 | 3169.1 | 66374 |

## Top Evidence Paths

### cmapss / degradation_stage_id / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| cycle -> sensor_09 | 0.4245 | 0.7837 | 0.6051 | 0.0000 |
| op_setting_1 -> sensor_07 | 0.1830 | 0.4613 | 0.1982 | 0.0000 |
| op_setting_1 -> sensor_14 | 0.1773 | 0.5079 | 0.8289 | 0.0000 |
| op_setting_1 -> sensor_18 | 0.1654 | 0.6103 | 0.2598 | 0.0000 |
| cycle -> sensor_21 | 0.1584 | 0.6626 | 0.3449 | 0.0000 |

### hydraulic / cooler / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| PS6_mean -> FS1_max | 0.2318 | 0.4942 | 0.1821 | 0.0000 |
| CP_min -> TS3_mean | 0.2312 | 0.4478 | 0.1957 | 0.0000 |
| VS1_last_minus_first -> TS1_max | 0.2093 | 0.4085 | 0.1837 | 0.0000 |
| FS1_last_minus_first -> TS3_mean | 0.1815 | 0.5896 | 0.3493 | 0.0000 |
| VS1_mean -> TS4_std | 0.1684 | 0.5226 | 0.1762 | 0.0000 |

### hydraulic / hydraulic_accumulator / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| TS4_min -> TS3_min | 0.3179 | 0.5585 | 0.2891 | 0.0000 |
| TS2_min -> TS4_max | 0.2728 | 0.6739 | 0.3151 | 0.0000 |
| FS2_max -> EPS1_std | 0.2619 | 0.4973 | 0.2860 | 0.0000 |
| FS1_std -> EPS1_max | 0.2274 | 0.6634 | 0.2271 | 0.0000 |
| PS3_last_minus_first -> FS2_std | 0.2053 | 0.6089 | 0.2845 | 0.0000 |

### hydraulic / internal_pump_leakage / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| SE_mean -> PS5_mean | 0.3599 | 0.6197 | 0.3660 | 0.0000 |
| PS3_max -> SE_std | 0.3201 | 0.6415 | 0.2264 | 0.0000 |
| PS2_max -> SE_mean | 0.2944 | 0.7164 | 0.3624 | 0.0000 |
| PS2_max -> FS2_std | 0.2684 | 0.7306 | 0.2290 | 0.0000 |
| PS2_std -> FS2_std | 0.2636 | 0.6786 | 0.2420 | 0.0000 |

### hydraulic / valve / full / prior=none / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| PS2_std -> PS6_max | 0.3080 | 0.5394 | 0.2521 | 0.0000 |
| PS2_std -> FS1_last_minus_first | 0.2416 | 0.5278 | 0.2326 | 0.0000 |
| TS4_max -> FS1_last_minus_first | 0.2096 | 0.4748 | 0.2333 | 0.0000 |
| PS2_std -> CE_std | 0.1988 | 0.5126 | 0.2462 | 0.0000 |
| FS1_mean -> PS6_max | 0.1922 | 0.4872 | 0.2762 | 0.0000 |

### skab / anomaly / full / prior=expert / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Accelerometer2RMS -> Accelerometer1RMS | 0.4414 | 0.6251 | 0.5937 | 0.0000 |
| Volume Flow RateRMS -> Temperature | 0.2812 | 0.5722 | 0.8263 | 0.0000 |
| Thermocouple -> Volume Flow RateRMS | 0.2508 | 0.4997 | 0.7924 | 0.0000 |
| Thermocouple -> Accelerometer1RMS | 0.2425 | 0.6156 | 0.7849 | 0.0000 |
| Accelerometer1RMS -> Accelerometer2RMS | 0.2055 | 0.4241 | 0.5136 | 0.0000 |

### skab / anomaly / full / prior=expert / seed=42

| Path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight |
|---|---:|---:|---:|---:|
| Thermocouple -> Volume Flow RateRMS | 0.4360 | 0.6631 | 0.7995 | 0.0000 |
| Accelerometer2RMS -> Accelerometer1RMS | 0.3537 | 0.6157 | 0.9066 | 0.0000 |
| Pressure -> Accelerometer1RMS | 0.3472 | 0.5574 | 0.3266 | 0.0000 |
| Current -> Accelerometer1RMS | 0.2130 | 0.3083 | 0.1411 | 0.0000 |
| Volume Flow RateRMS -> Accelerometer2RMS | 0.1362 | 0.6013 | 0.8421 | 0.0000 |

### skab / anomaly / full / prior=expert / seed=42

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

