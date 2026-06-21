# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0000
- candidate stability scores: {'baseline': 0.03508771929824561, 'edge_sieve_cover015': 0.017543859649122806, 'edge_sieve_softcover005': 0.03508771929824561, 'edge_sieve_edgecal': 0.07212475633528265, 'edge_overlay': 0.017543859649122806, 'edge_pool_edgecal': 0.017543859649122806}
- require candidate certificate: True
- candidate baseline path Jaccard: {'baseline': 1.0, 'edge_sieve_cover015': 0.07547169811320754, 'edge_sieve_softcover005': 0.12, 'edge_sieve_edgecal': 0.14893617021276595, 'edge_overlay': 0.14, 'edge_pool_edgecal': 0.26666666666666666}
- path disruption penalty weight: 0.0100
- selected candidate counts: {'baseline': 3}
- selected source-family counts: {'baseline': 3}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6361 +/- 0.0051 | 0.6477 +/- 0.0044 | 0.0351 | 0.3437 +/- 0.0161 | 12641.3 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|
| edge_overlay | algorithmic | no | -0.0053 | -0.0151 | -0.0869 | 0.1400 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| edge_pool_edgecal | algorithmic | no | -0.0040 | -0.0139 | -0.0650 | 0.2667 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| edge_sieve_cover015 | algorithmic | no | -0.0050 | -0.0124 | -0.0807 | 0.0755 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| edge_sieve_edgecal | algorithmic | no | -0.0069 | -0.0089 | -0.0737 | 0.1489 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |
| edge_sieve_softcover005 | algorithmic | no | -0.0091 | -0.0209 | -0.1022 | 0.1200 | 3 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.7245 | 0.6398 | 0.6526 | baseline=0.7245 |
| 43 | baseline | 0.7523 | 0.6396 | 0.6486 | baseline=0.7523 |
| 44 | baseline | 0.7412 | 0.6290 | 0.6420 | baseline=0.7412 |
