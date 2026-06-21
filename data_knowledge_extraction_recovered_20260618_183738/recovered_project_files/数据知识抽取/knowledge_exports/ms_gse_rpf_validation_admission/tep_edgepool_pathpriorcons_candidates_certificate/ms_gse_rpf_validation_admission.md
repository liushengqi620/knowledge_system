# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0000
- candidate stability scores: {'baseline': 0.03508771929824561, 'path_prior_consistency_s025': 0.017543859649122806, 'path_prior_consistency_s015': 0.017543859649122806}
- require candidate certificate: True
- selected candidate counts: {'baseline': 3}
- selected source-family counts: {'baseline': 3}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6361 +/- 0.0051 | 0.6477 +/- 0.0044 | 0.0351 | 0.3437 +/- 0.0161 | 12641.3 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---|
| path_prior_consistency_s015 | algorithmic | no | -0.0062 | -0.0332 | -0.1128 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| path_prior_consistency_s025 | algorithmic | no | 0.0033 | -0.0135 | -0.1009 | 3 | seed_level_validation_drop, low_tail_class_harm |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.7245 | 0.6398 | 0.6526 | baseline=0.7245 |
| 43 | baseline | 0.7523 | 0.6396 | 0.6486 | baseline=0.7523 |
| 44 | baseline | 0.7412 | 0.6290 | 0.6420 | baseline=0.7412 |
