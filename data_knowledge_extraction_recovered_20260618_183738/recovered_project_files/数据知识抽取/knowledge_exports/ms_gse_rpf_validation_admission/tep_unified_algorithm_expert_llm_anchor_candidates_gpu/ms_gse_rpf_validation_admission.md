# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {'alg_k16_s010': 0.005, 'expert_cal': 0.01, 'expert_llm_cal': 0.025, 'expert_llm_corrob': 0.025, 'expert_llm_anchor': 0.025}
- stability bonus weight: 0.2000
- candidate stability scores: {'baseline': 0.0, 'alg_k8': 0.0, 'alg_k16': 0.017543859649122806, 'alg_k16_s010': 0.017543859649122806, 'expert_cal': 0.0, 'expert_llm_cal': 0.0, 'expert_llm_corrob': 0.017543859649122806, 'expert_llm_anchor': 0.03508771929824561}
- selected candidate counts: {'alg_k8': 1, 'alg_k16': 2}
- selected source-family counts: {'algorithmic': 3}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | 0.0526 | 0.3279 +/- 0.0114 | 9591.9 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | alg_k8 | 0.7082 | 0.6258 | 0.6337 | baseline=0.6804, alg_k16=0.6802->adj0.6837, alg_k16_s010=0.6917->adj0.6903, alg_k8=0.7082, expert_cal=0.6776->adj0.6676, expert_llm_anchor=0.6881->adj0.6701, expert_llm_cal=0.6844->adj0.6594, expert_llm_corrob=0.6808->adj0.6593 |
| 43 | alg_k16 | 0.7326 | 0.6224 | 0.6342 | baseline=0.7276, alg_k16=0.7326->adj0.7361, alg_k16_s010=0.7368->adj0.7353, alg_k8=0.7341, expert_cal=0.7397->adj0.7297, expert_llm_anchor=0.7363->adj0.7183, expert_llm_cal=0.7546->adj0.7296, expert_llm_corrob=0.7293->adj0.7078 |
| 44 | alg_k16 | 0.7056 | 0.6090 | 0.6128 | baseline=0.7035, alg_k16=0.7056->adj0.7091, alg_k16_s010=0.6981->adj0.6966, alg_k8=0.6782, expert_cal=0.6904->adj0.6804, expert_llm_anchor=0.6837->adj0.6657, expert_llm_cal=0.6618->adj0.6368, expert_llm_corrob=0.7027->adj0.6812 |
