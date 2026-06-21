# MS-GSE + RPF Validation Admission

- dataset: hydraulic
- target: valve
- selection metric: validation macro_f1
- min validation gain: 0.0000

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.7570 +/- 0.0614 | 0.7686 +/- 0.0626 | 0.1201 | 0.5384 +/- 0.3817 | 294.8 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | salience_s005 | 0.8487 | 0.8337 | 0.8494 | baseline=0.8364, salience_s005=0.8487 |
| 43 | salience_s005 | 0.8007 | 0.7541 | 0.7596 | baseline=0.6821, salience_s005=0.8007 |
| 44 | baseline | 0.6646 | 0.6834 | 0.6969 | baseline=0.6646, salience_s005=0.6523 |
