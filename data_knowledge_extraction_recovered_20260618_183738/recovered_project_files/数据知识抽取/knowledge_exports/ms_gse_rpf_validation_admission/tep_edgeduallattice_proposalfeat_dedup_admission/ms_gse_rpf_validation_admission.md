# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0000
- candidate stability scores: {'baseline': 0.03508771929824561, 'dual_proposal': 0.03508771929824561}
- require candidate certificate: False
- candidate baseline path Jaccard: {'baseline': 1.0, 'dual_proposal': 0.09803921568627451}
- path disruption penalty weight: 0.0000
- selected candidate counts: {'dual_proposal': 1, 'baseline': 2}
- selected source-family counts: {'other': 1, 'baseline': 2}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6343 +/- 0.0043 | 0.6462 +/- 0.0030 | n/a | 0.3521 +/- 0.0135 | 10497.3 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|
| dual_proposal | other | no | -0.0023 | -0.0137 | -0.0638 | 0.0980 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | dual_proposal | 0.7398 | 0.6345 | 0.6479 | baseline=0.7245, dual_proposal=0.7398 |
| 43 | baseline | 0.7523 | 0.6396 | 0.6486 | baseline=0.7523, dual_proposal=0.7439 |
| 44 | baseline | 0.7412 | 0.6290 | 0.6420 | baseline=0.7412, dual_proposal=0.7275 |
