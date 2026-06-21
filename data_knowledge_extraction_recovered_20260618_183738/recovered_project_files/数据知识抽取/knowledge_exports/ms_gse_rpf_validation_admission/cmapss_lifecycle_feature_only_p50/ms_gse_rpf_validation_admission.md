# MS-GSE + RPF Validation Admission

- dataset: cmapss
- target: degradation_stage_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {'lifecycle': 0.0}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.7001 +/- 0.0066 | 0.6944 +/- 0.0077 | 0.1111 | 0.3144 +/- 0.0176 | 1540.7 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | lifecycle | 0.7720 | 0.7094 | 0.7052 | baseline=0.7706, lifecycle=0.7720 |
| 43 | lifecycle | 0.7769 | 0.6955 | 0.6895 | baseline=0.7698, lifecycle=0.7769 |
| 44 | lifecycle | 0.7863 | 0.6954 | 0.6885 | baseline=0.7787, lifecycle=0.7863 |
