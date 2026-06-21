# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0000
- candidate stability scores: {'baseline': 0.03508771929824561, 'dual_proposal004': 0.017543859649122806}
- require candidate certificate: False
- candidate baseline path Jaccard: {'baseline': 1.0, 'dual_proposal004': 0.09615384615384616}
- path disruption penalty weight: 0.0000
- selected candidate counts: {'dual_proposal004': 1, 'baseline': 2}
- selected source-family counts: {'other': 1, 'baseline': 2}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6341 +/- 0.0043 | 0.6462 +/- 0.0030 | n/a | 0.3465 +/- 0.0142 | 10529.2 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|
| dual_proposal004 | other | no | 0.0004 | -0.0125 | -0.0789 | 0.0962 | 3 | seed_level_validation_drop, low_tail_class_harm |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | dual_proposal004 | 0.7480 | 0.6336 | 0.6481 | baseline=0.7245, dual_proposal004=0.7480 |
| 43 | baseline | 0.7523 | 0.6396 | 0.6486 | baseline=0.7523, dual_proposal004=0.7424 |
| 44 | baseline | 0.7412 | 0.6290 | 0.6420 | baseline=0.7412, dual_proposal004=0.7287 |
