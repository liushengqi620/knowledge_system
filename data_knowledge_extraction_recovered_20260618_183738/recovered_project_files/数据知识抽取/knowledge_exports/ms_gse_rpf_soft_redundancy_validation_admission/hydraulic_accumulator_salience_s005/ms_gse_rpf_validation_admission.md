# MS-GSE + RPF Validation Admission

- dataset: hydraulic
- target: hydraulic_accumulator
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.9327 +/- 0.0078 | 0.9339 +/- 0.0052 | 0.0185 | 0.0000 +/- 0.0000 | 225.3 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.9492 | 0.9218 | 0.9268 | baseline=0.9492, salience_s005=0.9050 |
| 43 | baseline | 0.9296 | 0.9392 | 0.9363 | baseline=0.9296, salience_s005=0.8850 |
| 44 | baseline | 0.9192 | 0.9372 | 0.9388 | baseline=0.9192, salience_s005=0.9182 |
