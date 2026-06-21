# MS-GSE + RPF Validation Admission

- dataset: skab
- target: anomaly
- selection metric: validation macro_f1
- min validation gain: 0.0000

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.8287 +/- 0.0156 | 0.8267 +/- 0.0177 | n/a | 0.2263 +/- 0.3200 | 3202.6 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.9236 | 0.8507 | 0.8512 | baseline=0.9236, expert_prior0=0.9081, salience_s005=0.7661 |
| 43 | expert_prior0 | 0.9372 | 0.8157 | 0.8097 | baseline=0.9315, expert_prior0=0.9372, salience_s005=0.9348 |
| 44 | salience_s005 | 0.9172 | 0.8197 | 0.8193 | baseline=0.9052, expert_prior0=0.9056, salience_s005=0.9172 |
