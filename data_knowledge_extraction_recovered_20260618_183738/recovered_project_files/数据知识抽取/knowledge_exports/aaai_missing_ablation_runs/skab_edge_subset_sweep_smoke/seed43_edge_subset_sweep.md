# SKAB Dynamic Edge Subset Sweep

- Status: ok
- Seed: 43
- Epochs: 1
- Baseline validation Macro-F1: 0.7881
- Baseline test Macro-F1: 0.6902
- Candidate subsets: 21
- Validation-positive subsets: 21

| Rank | Subset | Val Macro-F1 | Val Gain | Test Macro-F1 | Test Gain |
|---:|---|---:|---:|---:|---:|
| 1 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 | 0.8740 | +0.0859 | 0.7433 | +0.0531 |
| 2 | Current->Temperature@2, Accelerometer1RMS->Accelerometer2RMS@1 | 0.8732 | +0.0850 | 0.7486 | +0.0584 |
| 3 | Accelerometer1RMS->Accelerometer2RMS@1, Temperature->Volume Flow RateRMS@1 | 0.8637 | +0.0756 | 0.7240 | +0.0338 |
| 4 | Accelerometer2RMS->Accelerometer1RMS@1, Temperature->Volume Flow RateRMS@1 | 0.8618 | +0.0737 | 0.7555 | +0.0653 |
| 5 | Accelerometer1RMS->Accelerometer2RMS@1, Volume Flow RateRMS->Temperature@1 | 0.8615 | +0.0733 | 0.7504 | +0.0602 |
| 6 | Current->Temperature@2, Accelerometer2RMS->Accelerometer1RMS@1 | 0.8524 | +0.0643 | 0.7397 | +0.0495 |
| 7 | Volume Flow RateRMS->Pressure@1, Accelerometer1RMS->Accelerometer2RMS@1 | 0.8484 | +0.0602 | 0.7224 | +0.0322 |
| 8 | Accelerometer1RMS->Accelerometer2RMS@1 | 0.8473 | +0.0592 | 0.7109 | +0.0208 |
| 9 | Accelerometer2RMS->Accelerometer1RMS@1, Volume Flow RateRMS->Temperature@1 | 0.8321 | +0.0439 | 0.7401 | +0.0499 |
| 10 | Accelerometer2RMS->Accelerometer1RMS@1 | 0.8308 | +0.0427 | 0.7272 | +0.0370 |
