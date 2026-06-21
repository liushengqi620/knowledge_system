# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0000
- candidate stability scores: {'baseline': 0.03508771929824561, 'edge_universe': 0.017543859649122806, 'path_prior_consistency': 0.0, 'class_blend': 0.05263157894736842, 'edgepool_minscore010': 0.0, 'class_staticlag_l3w025': 0.017543859649122806}
- require candidate certificate: True
- candidate baseline path Jaccard: {'baseline': 1.0, 'edge_universe': 0.03636363636363636, 'path_prior_consistency': 0.11538461538461539, 'class_blend': 0.07692307692307693, 'edgepool_minscore010': 0.09433962264150944, 'class_staticlag_l3w025': 0.07547169811320754}
- path disruption penalty weight: 0.0100
- selected candidate counts: {'baseline': 3}
- selected source-family counts: {'baseline': 3}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6361 +/- 0.0051 | 0.6477 +/- 0.0044 | 0.0351 | 0.3437 +/- 0.0161 | 12641.3 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|
| class_blend | algorithmic | no | -0.0112 | -0.0162 | -0.0629 | 0.0769 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| class_staticlag_l3w025 | algorithmic | no | -0.0086 | -0.0222 | -0.0740 | 0.0755 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| edge_universe | algorithmic | no | -0.0008 | -0.0293 | -0.1065 | 0.0364 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm, baseline_path_overlap_below_threshold |
| edgepool_minscore010 | algorithmic | no | -0.0148 | -0.0234 | -0.1091 | 0.0943 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| path_prior_consistency | algorithmic | no | -0.0052 | -0.0182 | -0.0643 | 0.1154 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.7245 | 0.6398 | 0.6526 | baseline=0.7245 |
| 43 | baseline | 0.7523 | 0.6396 | 0.6486 | baseline=0.7523 |
| 44 | baseline | 0.7412 | 0.6290 | 0.6420 | baseline=0.7412 |
