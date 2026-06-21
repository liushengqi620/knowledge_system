# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {'static_lag': 0.005, 'static_lag_l1w025': 0.005, 'multihop025': 0.005, 'multihop010': 0.005}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6098 +/- 0.0105 | 0.6199 +/- 0.0108 | n/a | 0.2426 +/- 0.0656 | 7312.7 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.6804 | 0.6228 | 0.6322 | baseline=0.6804, multihop010=0.6677->adj0.6627, multihop025=0.6708->adj0.6658, static_lag=0.6703->adj0.6653, static_lag_l1w025=0.6806->adj0.6756 |
| 43 | static_lag | 0.7474 | 0.6095 | 0.6217 | baseline=0.7276, multihop010=0.7128->adj0.7078, multihop025=0.7279->adj0.7229, static_lag=0.7474->adj0.7424, static_lag_l1w025=0.7215->adj0.7165 |
| 44 | baseline | 0.7035 | 0.5971 | 0.6059 | baseline=0.7035, multihop010=0.6610->adj0.6560, multihop025=0.6497->adj0.6447, static_lag=0.6858->adj0.6808, static_lag_l1w025=0.6934->adj0.6884 |
