# SKAB Dynamic Edge Subset Sweep

- Status: ok
- Seed: 44
- Epochs: 8
- Baseline validation Macro-F1: 0.7621
- Baseline test Macro-F1: 0.9252
- Candidate subsets: 21
- Validation-positive subsets: 20

| Rank | Subset | Val Macro-F1 | Val Gain | Test Macro-F1 | Test Gain |
|---:|---|---:|---:|---:|---:|
| 1 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 | 0.8082 | +0.0461 | 0.8953 | -0.0299 |
| 2 | Temperature->Volume Flow RateRMS@1 | 0.7946 | +0.0325 | 0.9114 | -0.0138 |
| 3 | Accelerometer1RMS->Accelerometer2RMS@1, Temperature->Volume Flow RateRMS@1 | 0.7925 | +0.0304 | 0.9108 | -0.0143 |
| 4 | Volume Flow RateRMS->Pressure@1, Temperature->Volume Flow RateRMS@1 | 0.7905 | +0.0284 | 0.8869 | -0.0383 |
| 5 | Current->Temperature@2, Volume Flow RateRMS->Temperature@1 | 0.7896 | +0.0275 | 0.9030 | -0.0222 |
| 6 | Current->Temperature@2, Temperature->Volume Flow RateRMS@1 | 0.7878 | +0.0258 | 0.9104 | -0.0148 |
| 7 | Accelerometer1RMS->Accelerometer2RMS@1 | 0.7870 | +0.0249 | 0.8924 | -0.0328 |
| 8 | Current->Temperature@2, Accelerometer2RMS->Accelerometer1RMS@1 | 0.7811 | +0.0190 | 0.8911 | -0.0340 |
| 9 | Accelerometer2RMS->Accelerometer1RMS@1 | 0.7737 | +0.0116 | 0.8935 | -0.0317 |
| 10 | Accelerometer2RMS->Accelerometer1RMS@1, Volume Flow RateRMS->Temperature@1 | 0.7734 | +0.0113 | 0.9141 | -0.0111 |
