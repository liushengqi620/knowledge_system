# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6174 +/- 0.0069 | 0.6250 +/- 0.0089 | n/a | 0.3285 +/- 0.0122 | 8819.3 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | alg_k8 | 0.7082 | 0.6258 | 0.6337 | baseline=0.6804, alg_k16=0.6802, alg_k16_s010=0.6917, alg_k8=0.7082 |
| 43 | alg_k16_s010 | 0.7368 | 0.6174 | 0.6286 | baseline=0.7276, alg_k16=0.7326, alg_k16_s010=0.7368, alg_k8=0.7341 |
| 44 | alg_k16 | 0.7056 | 0.6090 | 0.6128 | baseline=0.7035, alg_k16=0.7056, alg_k16_s010=0.6981, alg_k8=0.6782 |
