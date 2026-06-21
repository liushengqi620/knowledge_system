# SKAB Dynamic Edge Subset Sweep

- Status: ok
- Seed: 43
- Epochs: 8
- Baseline validation Macro-F1: 0.9502
- Baseline test Macro-F1: 0.8094
- Candidate subsets: 21
- Validation-positive subsets: 1

| Rank | Subset | Val Macro-F1 | Val Gain | Test Macro-F1 | Test Gain |
|---:|---|---:|---:|---:|---:|
| 1 | Accelerometer1RMS->Accelerometer2RMS@1 | 0.9620 | +0.0119 | 0.8359 | +0.0264 |
| 2 | Volume Flow RateRMS->Pressure@1, Accelerometer2RMS->Accelerometer1RMS@1 | 0.9486 | -0.0015 | 0.8041 | -0.0053 |
| 3 | Volume Flow RateRMS->Pressure@1, Accelerometer1RMS->Accelerometer2RMS@1 | 0.9418 | -0.0084 | 0.8061 | -0.0033 |
| 4 | Current->Temperature@2, Volume Flow RateRMS->Pressure@1 | 0.9355 | -0.0146 | 0.8043 | -0.0051 |
| 5 | Accelerometer2RMS->Accelerometer1RMS@1, Volume Flow RateRMS->Temperature@1 | 0.9350 | -0.0152 | 0.8067 | -0.0028 |
| 6 | Accelerometer2RMS->Accelerometer1RMS@1, Temperature->Volume Flow RateRMS@1 | 0.9348 | -0.0153 | 0.8071 | -0.0023 |
| 7 | Accelerometer2RMS->Accelerometer1RMS@1 | 0.9327 | -0.0175 | 0.8110 | +0.0016 |
| 8 | Volume Flow RateRMS->Temperature@1 | 0.9314 | -0.0188 | 0.8133 | +0.0039 |
| 9 | Current->Temperature@2 | 0.9206 | -0.0295 | 0.8274 | +0.0180 |
| 10 | Volume Flow RateRMS->Pressure@1 | 0.9197 | -0.0304 | 0.7924 | -0.0170 |
