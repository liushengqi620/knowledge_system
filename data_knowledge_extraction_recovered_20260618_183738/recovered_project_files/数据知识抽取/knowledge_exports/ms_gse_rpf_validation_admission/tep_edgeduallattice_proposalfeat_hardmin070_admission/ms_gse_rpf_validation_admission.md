# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0000
- candidate stability scores: {'baseline': 0.03508771929824561, 'dual_hardmin070': 0.017543859649122806}
- require candidate certificate: False
- candidate baseline path Jaccard: {'baseline': 1.0, 'dual_hardmin070': 0.14}
- path disruption penalty weight: 0.0000
- selected candidate counts: {'dual_hardmin070': 1, 'baseline': 2}
- selected source-family counts: {'other': 1, 'baseline': 2}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6301 +/- 0.0073 | 0.6434 +/- 0.0039 | n/a | 0.3517 +/- 0.0134 | 10870.1 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|
| dual_hardmin070 | other | no | -0.0012 | -0.0153 | -0.0802 | 0.1400 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | dual_hardmin070 | 0.7434 | 0.6217 | 0.6394 | baseline=0.7245, dual_hardmin070=0.7434 |
| 43 | baseline | 0.7523 | 0.6396 | 0.6486 | baseline=0.7523, dual_hardmin070=0.7450 |
| 44 | baseline | 0.7412 | 0.6290 | 0.6420 | baseline=0.7412, dual_hardmin070=0.7259 |
