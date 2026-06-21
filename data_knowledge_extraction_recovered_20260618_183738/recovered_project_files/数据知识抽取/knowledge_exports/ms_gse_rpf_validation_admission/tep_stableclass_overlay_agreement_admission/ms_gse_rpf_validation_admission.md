# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0100
- candidate stability scores: {'baseline': 0.03508771929824561, 'stableclass_overlay': 0.017543859649122806, 'stableclass_overlay_agree': 0.017543859649122806}
- require candidate certificate: True
- candidate baseline path Jaccard: {'baseline': 1.0, 'stableclass_overlay': 0.1875, 'stableclass_overlay_agree': 0.16326530612244897}
- path disruption penalty weight: 0.0100
- selected candidate counts: {'baseline': 3}
- selected source-family counts: {'baseline': 3}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6361 +/- 0.0051 | 0.6477 +/- 0.0044 | 0.0351 | 0.3437 +/- 0.0161 | 12641.3 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|
| stableclass_overlay | algorithmic | no | -0.0038 | -0.0230 | -0.0821 | 0.1875 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| stableclass_overlay_agree | algorithmic | no | -0.0048 | -0.0120 | -0.0893 | 0.1633 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.7245 | 0.6398 | 0.6526 | baseline=0.7245->adj0.7249 |
| 43 | baseline | 0.7523 | 0.6396 | 0.6486 | baseline=0.7523->adj0.7526 |
| 44 | baseline | 0.7412 | 0.6290 | 0.6420 | baseline=0.7412->adj0.7415 |
