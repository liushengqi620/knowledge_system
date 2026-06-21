# SKAB CF/No-CF Subset Formal Summary

- Status: complete_formal
- Seeds: 42, 43, 44
- CF minus no-CF test Macro-F1: -0.0003 +/- 0.0003

| Branch | N | Test Macro-F1 | Test Gain | Val Gain | Kept Edges |
|---|---:|---:|---:|---:|---:|
| cf_standard | 3 | 0.8798 +/- 0.0317 | +0.0049 +/- 0.0246 | +0.0257 +/- 0.0148 | 1.33 +/- 0.47 |
| no_cf | 3 | 0.8801 +/- 0.0317 | +0.0055 +/- 0.0251 | +0.0261 +/- 0.0146 | 1.33 +/- 0.47 |

| Seed | Branch | Test Macro-F1 | Test Gain | Val Gain | Kept | CF Max Drop | Edges |
|---:|---|---:|---:|---:|---:|---:|---|
| 42 | cf_standard | 0.9084 | +0.0193 | +0.0196 | 1 | 0.0473 | Current->Temperature@2 |
| 42 | no_cf | 0.9090 | +0.0197 | +0.0207 | 1 | 0.0000 | Current->Temperature@2 |
| 43 | cf_standard | 0.8356 | +0.0252 | +0.0115 | 1 | 0.1243 | Accelerometer1RMS->Accelerometer2RMS@1 |
| 43 | no_cf | 0.8360 | +0.0265 | +0.0116 | 1 | 0.0000 | Accelerometer1RMS->Accelerometer2RMS@1 |
| 44 | cf_standard | 0.8954 | -0.0297 | +0.0461 | 2 | 0.0279 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 |
| 44 | no_cf | 0.8953 | -0.0298 | +0.0461 | 2 | 0.0000 | Accelerometer1RMS->Accelerometer2RMS@1, Accelerometer2RMS->Accelerometer1RMS@1 |

## Interpretation

Validation-positive edge subsets make the CF/no-CF comparison runnable. If CF and no-CF stay close, the main performance driver is the validation-admitted candidate itself; CF should be described as a reliability/interpretability guard rather than the primary source of accuracy.
