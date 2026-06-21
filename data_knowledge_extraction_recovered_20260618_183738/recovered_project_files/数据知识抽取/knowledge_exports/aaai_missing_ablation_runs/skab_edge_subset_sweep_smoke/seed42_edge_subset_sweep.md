# SKAB Dynamic Edge Subset Sweep

- Status: ok
- Seed: 42
- Epochs: 1
- Baseline validation Macro-F1: 0.8070
- Baseline test Macro-F1: 0.7743
- Candidate subsets: 21
- Validation-positive subsets: 17

| Rank | Subset | Val Macro-F1 | Val Gain | Test Macro-F1 | Test Gain |
|---:|---|---:|---:|---:|---:|
| 1 | Accelerometer1RMS->Accelerometer2RMS@1 | 0.8393 | +0.0323 | 0.7970 | +0.0227 |
| 2 | Current->Temperature@2, Accelerometer1RMS->Accelerometer2RMS@1 | 0.8392 | +0.0322 | 0.7900 | +0.0157 |
| 3 | Accelerometer2RMS->Accelerometer1RMS@1 | 0.8378 | +0.0308 | 0.7941 | +0.0197 |
| 4 | Volume Flow RateRMS->Pressure@1, Accelerometer1RMS->Accelerometer2RMS@1 | 0.8344 | +0.0274 | 0.7898 | +0.0155 |
| 5 | Volume Flow RateRMS->Pressure@1, Accelerometer2RMS->Accelerometer1RMS@1 | 0.8324 | +0.0253 | 0.7850 | +0.0106 |
| 6 | Accelerometer1RMS->Accelerometer2RMS@1, Volume Flow RateRMS->Temperature@1 | 0.8275 | +0.0205 | 0.7832 | +0.0089 |
| 7 | Current->Temperature@2, Volume Flow RateRMS->Pressure@1 | 0.8251 | +0.0181 | 0.7891 | +0.0147 |
| 8 | Accelerometer2RMS->Accelerometer1RMS@1, Temperature->Volume Flow RateRMS@1 | 0.8247 | +0.0177 | 0.7864 | +0.0121 |
| 9 | Temperature->Volume Flow RateRMS@1 | 0.8217 | +0.0147 | 0.7891 | +0.0148 |
| 10 | Volume Flow RateRMS->Pressure@1, Temperature->Volume Flow RateRMS@1 | 0.8211 | +0.0141 | 0.7873 | +0.0129 |
