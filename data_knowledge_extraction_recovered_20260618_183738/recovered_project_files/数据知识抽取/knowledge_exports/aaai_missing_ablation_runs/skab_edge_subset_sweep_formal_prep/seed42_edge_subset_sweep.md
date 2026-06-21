# SKAB Dynamic Edge Subset Sweep

- Status: ok
- Seed: 42
- Epochs: 8
- Baseline validation Macro-F1: 0.9434
- Baseline test Macro-F1: 0.8891
- Candidate subsets: 21
- Validation-positive subsets: 8

| Rank | Subset | Val Macro-F1 | Val Gain | Test Macro-F1 | Test Gain |
|---:|---|---:|---:|---:|---:|
| 1 | Current->Temperature@2 | 0.9616 | +0.0182 | 0.9097 | +0.0207 |
| 2 | Accelerometer2RMS->Accelerometer1RMS@1 | 0.9597 | +0.0163 | 0.8899 | +0.0008 |
| 3 | Volume Flow RateRMS->Temperature@1 | 0.9549 | +0.0115 | 0.9021 | +0.0131 |
| 4 | Current->Temperature@2, Temperature->Volume Flow RateRMS@1 | 0.9546 | +0.0112 | 0.9123 | +0.0233 |
| 5 | Current->Temperature@2, Accelerometer2RMS->Accelerometer1RMS@1 | 0.9543 | +0.0109 | 0.8863 | -0.0027 |
| 6 | Temperature->Volume Flow RateRMS@1 | 0.9530 | +0.0096 | 0.8989 | +0.0098 |
| 7 | Current->Temperature@2, Volume Flow RateRMS->Temperature@1 | 0.9495 | +0.0061 | 0.9036 | +0.0145 |
| 8 | Volume Flow RateRMS->Pressure@1 | 0.9463 | +0.0029 | 0.9004 | +0.0114 |
| 9 | Volume Flow RateRMS->Pressure@1, Temperature->Volume Flow RateRMS@1 | 0.9425 | -0.0009 | 0.8920 | +0.0029 |
| 10 | Current->Temperature@2, Volume Flow RateRMS->Pressure@1 | 0.9410 | -0.0023 | 0.8915 | +0.0025 |
