# MS-GSE + RPF Validation Admission

- dataset: skab
- target: anomaly
- selection metric: validation macro_f1
- min validation gain: 0.0000

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.8307 +/- 0.0141 | 0.8281 +/- 0.0164 | 0.2778 | 0.5026 +/- 0.3606 | 3194.6 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.9236 | 0.8507 | 0.8512 | baseline=0.9236, salience_s005=0.7661 |
| 43 | salience_s005 | 0.9348 | 0.8218 | 0.8140 | baseline=0.9315, salience_s005=0.9348 |
| 44 | salience_s005 | 0.9172 | 0.8197 | 0.8193 | baseline=0.9052, salience_s005=0.9172 |
