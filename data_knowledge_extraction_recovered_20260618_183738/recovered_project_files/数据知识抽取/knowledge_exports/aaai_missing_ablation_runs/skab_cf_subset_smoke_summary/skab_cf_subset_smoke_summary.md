# SKAB CF/No-CF Subset Smoke Summary

- Status: complete_smoke
- Seeds: 42, 43, 44
- CF minus no-CF test Macro-F1: -0.0008 +/- 0.0008

| Branch | N | Test Macro-F1 | Test Gain | Val Gain | Kept Edges |
|---|---:|---:|---:|---:|---:|
| cf_standard | 3 | 0.8136 +/- 0.0657 | +0.0560 +/- 0.0293 | +0.0785 +/- 0.0348 | 1.67 +/- 0.47 |
| no_cf | 3 | 0.8145 +/- 0.0650 | +0.0569 +/- 0.0290 | +0.0786 +/- 0.0348 | 1.67 +/- 0.47 |
| cf_consistency | 3 | 0.7961 +/- 0.0862 | +0.0382 +/- 0.0398 | +0.0786 +/- 0.0349 | 1.00 +/- 0.82 |

| Seed | Branch | Test Macro-F1 | Test Gain | Val Gain | Kept | CF Max Drop | Edges |
|---:|---|---:|---:|---:|---:|---:|---|
| 42 | cf_standard | 0.7961 | +0.0215 | +0.0326 | 1 | 0.0823 | Accelerometer1RMS->Accelerometer2RMS@1 |
| 42 | no_cf | 0.7967 | +0.0223 | +0.0325 | 1 | 0.0000 | Accelerometer1RMS->Accelerometer2RMS@1 |
| 42 | cf_consistency | 0.7969 | +0.0216 | +0.0325 | 1 | 0.0825 | Accelerometer1RMS->Accelerometer2RMS@1 |
| 43 | cf_standard | 0.7434 | +0.0532 | +0.0860 | 2 | 0.0667 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 |
| 43 | no_cf | 0.7453 | +0.0551 | +0.0866 | 2 | 0.0000 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 |
| 43 | cf_consistency | 0.6902 | +0.0000 | +0.0864 | 0 | 0.0676 |  |
| 44 | cf_standard | 0.9014 | +0.0932 | +0.1167 | 2 | 0.1812 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 |
| 44 | no_cf | 0.9014 | +0.0932 | +0.1168 | 2 | 0.0000 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 |
| 44 | cf_consistency | 0.9013 | +0.0931 | +0.1169 | 2 | 0.1814 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 |

## Interpretation

Validation-positive edge subsets make the CF/no-CF comparison runnable. Standard CF confirms counterfactual sensitivity while preserving the validation-admitted candidates; stricter multi-mode CF is a safety stress test and may reject beneficial but less consistently perturbed candidates.
