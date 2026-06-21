# SKAB Dynamic Edge Subset Sweep

- Status: ok
- Seed: 44
- Epochs: 1
- Baseline validation Macro-F1: 0.7736
- Baseline test Macro-F1: 0.8083
- Candidate subsets: 21
- Validation-positive subsets: 18

| Rank | Subset | Val Macro-F1 | Val Gain | Test Macro-F1 | Test Gain |
|---:|---|---:|---:|---:|---:|
| 1 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 | 0.8906 | +0.1169 | 0.9013 | +0.0930 |
| 2 | Current->Temperature@2, Accelerometer2RMS->Accelerometer1RMS@1 | 0.8895 | +0.1159 | 0.9069 | +0.0986 |
| 3 | Accelerometer1RMS->Accelerometer2RMS@1, Volume Flow RateRMS->Temperature@1 | 0.8870 | +0.1133 | 0.9173 | +0.1090 |
| 4 | Accelerometer1RMS->Accelerometer2RMS@1, Temperature->Volume Flow RateRMS@1 | 0.8843 | +0.1107 | 0.9178 | +0.1095 |
| 5 | Current->Temperature@2, Volume Flow RateRMS->Pressure@1 | 0.8842 | +0.1106 | 0.9204 | +0.1121 |
| 6 | Current->Temperature@2, Volume Flow RateRMS->Temperature@1 | 0.8803 | +0.1066 | 0.9135 | +0.1053 |
| 7 | Accelerometer2RMS->Accelerometer1RMS@1, Volume Flow RateRMS->Temperature@1 | 0.8777 | +0.1040 | 0.9186 | +0.1103 |
| 8 | Temperature->Volume Flow RateRMS@1, Volume Flow RateRMS->Temperature@1 | 0.8775 | +0.1039 | 0.9311 | +0.1228 |
| 9 | Current->Temperature@2, Temperature->Volume Flow RateRMS@1 | 0.8772 | +0.1036 | 0.9034 | +0.0951 |
| 10 | Current->Temperature@2, Accelerometer1RMS->Accelerometer2RMS@1 | 0.8754 | +0.1018 | 0.9087 | +0.1004 |
