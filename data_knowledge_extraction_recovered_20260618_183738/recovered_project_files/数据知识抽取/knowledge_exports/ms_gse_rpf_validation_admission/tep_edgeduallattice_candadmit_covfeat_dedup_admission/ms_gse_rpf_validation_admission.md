# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0000
- candidate stability scores: {'baseline': 0.03508771929824561, 'dual_dedup': 0.017543859649122806}
- require candidate certificate: False
- candidate baseline path Jaccard: {'baseline': 1.0, 'dual_dedup': 0.07547169811320754}
- path disruption penalty weight: 0.0000
- selected candidate counts: {'dual_dedup': 1, 'baseline': 2}
- selected source-family counts: {'other': 1, 'baseline': 2}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6352 +/- 0.0045 | 0.6471 +/- 0.0037 | n/a | 0.3495 +/- 0.0133 | 10479.5 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|
| dual_dedup | other | no | -0.0043 | -0.0119 | -0.0619 | 0.0755 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | dual_dedup | 0.7267 | 0.6371 | 0.6506 | baseline=0.7245, dual_dedup=0.7267 |
| 43 | baseline | 0.7523 | 0.6396 | 0.6486 | baseline=0.7523, dual_dedup=0.7404 |
| 44 | baseline | 0.7412 | 0.6290 | 0.6420 | baseline=0.7412, dual_dedup=0.7381 |
