# MS-GSE + RPF Validation Admission

- dataset: hydraulic
- target: valve
- selection metric: validation macro_f1
- min validation gain: 0.0000

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.7564 +/- 0.0446 | 0.7601 +/- 0.0499 | 0.0417 | 0.5381 +/- 0.3816 | 290.1 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | salience_s005 | 0.8161 | 0.8085 | 0.8181 | baseline=0.6993, salience_s005=0.8161 |
| 43 | salience_s005 | 0.8001 | 0.7611 | 0.7661 | baseline=0.7458, salience_s005=0.8001 |
| 44 | baseline | 0.6738 | 0.6996 | 0.6963 | baseline=0.6738, salience_s005=0.6486 |
