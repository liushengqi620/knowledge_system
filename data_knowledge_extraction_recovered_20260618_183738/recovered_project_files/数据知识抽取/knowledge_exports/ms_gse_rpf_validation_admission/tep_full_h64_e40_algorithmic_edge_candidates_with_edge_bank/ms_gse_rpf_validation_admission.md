# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.2000
- candidate stability scores: {'baseline': 0.0, 'alg_k8': 0.0, 'alg_k16': 0.0, 'edge_bank': 0.0, 'focus_valtail6': 0.0}
- selected candidate counts: {'alg_k16': 1, 'baseline': 2}
- selected source-family counts: {'algorithmic': 1, 'baseline': 2}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | 0.0000 | 0.3024 +/- 0.0095 | 11353.8 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | alg_k16 | 0.7664 | 0.6367 | 0.6506 | baseline=0.7213, alg_k16=0.7664, alg_k8=0.7366, edge_bank=0.7183, focus_valtail6=0.7015 |
| 43 | baseline | 0.7738 | 0.6213 | 0.6402 | baseline=0.7738, alg_k16=0.7607, alg_k8=0.7618, edge_bank=0.7181, focus_valtail6=0.7048 |
| 44 | baseline | 0.7870 | 0.6426 | 0.6596 | baseline=0.7870, alg_k16=0.7595, alg_k8=0.7602, edge_bank=0.7154, focus_valtail6=0.6806 |
