# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {}
- stability bonus weight: 0.2000
- candidate stability scores: {'baseline': 0.0, 'alg_k16': 0.0, 'edgecal_reg1_v2': 0.017543859649122806, 'edge_bank_gb4': 0.0}
- selected candidate counts: {'alg_k16': 1, 'baseline': 2}
- selected source-family counts: {'algorithmic': 1, 'baseline': 2}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | 0.0000 | 0.3024 +/- 0.0095 | 11353.8 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | alg_k16 | 0.7664 | 0.6367 | 0.6506 | baseline=0.7213, alg_k16=0.7664, edge_bank_gb4=0.7046, edgecal_reg1_v2=0.7159->adj0.7194 |
| 43 | baseline | 0.7738 | 0.6213 | 0.6402 | baseline=0.7738, alg_k16=0.7607, edge_bank_gb4=0.7194, edgecal_reg1_v2=0.6903->adj0.6938 |
| 44 | baseline | 0.7870 | 0.6426 | 0.6596 | baseline=0.7870, alg_k16=0.7595, edge_bank_gb4=0.7177, edgecal_reg1_v2=0.7234->adj0.7269 |
