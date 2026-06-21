# MS-GSE + RPF Validation Admission

- dataset: tep
- target: fault
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.0000
- candidate stability scores: {'baseline': 0.0, 'rel_evidence_s010': 0.0}
- require candidate certificate: True
- candidate baseline path Jaccard: {'baseline': 1.0, 'rel_evidence_s010': 1.0}
- path disruption penalty weight: 0.0000
- selected candidate counts: {}
- selected source-family counts: {}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | n/a | 0.0000 +/- 0.0000 | 0.0 |

## Candidate Certificates

| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|
| rel_evidence_s010 | other | no | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0 | no_common_seed |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
