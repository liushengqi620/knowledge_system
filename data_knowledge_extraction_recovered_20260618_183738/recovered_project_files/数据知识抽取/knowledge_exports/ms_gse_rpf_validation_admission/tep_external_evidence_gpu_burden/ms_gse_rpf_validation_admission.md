# MS-GSE + RPF Validation Admission

- dataset: tep
- target: event_quality_class_id
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {'expert': 0.01, 'expert_llm': 0.015}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.6097 +/- 0.0105 | 0.6195 +/- 0.0108 | n/a | 0.2965 +/- 0.0188 | 7267.6 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | baseline | 0.6804 | 0.6228 | 0.6322 | baseline=0.6804, expert=0.6776->adj0.6676, expert_llm=0.6844->adj0.6694 |
| 43 | expert_llm | 0.7546 | 0.6091 | 0.6204 | baseline=0.7276, expert=0.7397->adj0.7297, expert_llm=0.7546->adj0.7396 |
| 44 | baseline | 0.7035 | 0.5971 | 0.6059 | baseline=0.7035, expert=0.6904->adj0.6804, expert_llm=0.6618->adj0.6468 |
