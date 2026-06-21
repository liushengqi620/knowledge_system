# Advanced Traceability Pilot Experiment

## Scope

This pilot evaluates downstream anomaly traceability on weak-labeled Baosteel records after mechanism KG extraction. It is engineering evidence, not paper-scale expert-reviewed evidence.

## Inputs

- Train records: 83568
- Test records: 10430
- Mechanism/traceability KG: `C:\Users\CPILAB\Documents\xwechat_files\wxid_fn3terjpgaio22_c340\msg\file\2026-06\codex_recovery\data_knowledge_extraction_recovered_20260618_183738\recovered_project_files\RAG\data\quality_traceability_large_kg\quality_traceability_large_kg_seed.json`

## Metrics

| Method | Hit@1 | Hit@3 | Any-label Hit@3 | MRR | Macro F1 | Explanation Coverage | Avg Trace Paths |
|---|---:|---:|---:|---:|---:|---:|---:|
| `label_prior_majority` | 0.3244 | 0.7918 | 0.9931 | 0.5686 | 0.0612 | 0.0 | 0.0 |
| `feature_group_prior` | 0.9993 | 0.9993 | 0.9993 | 0.9994 | 0.8748 | 0.0 | 0.0 |
| `feature_name_naive_bayes` | 0.9993 | 0.9993 | 0.9993 | 0.9994 | 0.8748 | 0.0 | 0.0 |
| `kg_anchor_reasoning` | 0.3652 | 0.6752 | 0.6752 | 0.5642 | 0.3042 | 0.0 | 0.0 |
| `kg_path_reasoning` | 0.1529 | 0.6538 | 0.6638 | 0.4165 | 0.181 | 0.8711 | 0.8925 |
| `proposed_plm_llm_kg_fusion` | 0.9993 | 0.9994 | 0.9994 | 0.9994 | 0.8748 | 0.4037 | 0.4251 |

## Proposed Examples

### baosteel-structured-79

- Gold primary label: `mold_level_slag_risk`
- Predicted top3: `mold_level_slag_risk, speed_stopper_flow, process_fluctuation`
- Top features: mold_level_range, mold_level_mean, mold_level_ge7, mold_level_ge10, 液面波动极差/mm
- Example KG path: High casting speed [affect] mold heat transfer stability

### baosteel-structured-82

- Gold primary label: `other_quality_abnormal`
- Predicted top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Top features: TD_weight_mean, TD_avg_temp, cast_speed_mean, mold_level_range, heat_exchange_mean
- Example KG path: Low superheat [affect] mold flux melting

### baosteel-structured-83

- Gold primary label: `other_quality_abnormal`
- Predicted top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Top features: TD_weight_mean, TD_avg_temp, cast_speed_mean, mold_level_range, heat_exchange_mean
- Example KG path: Low superheat [affect] mold flux melting

### baosteel-structured-85

- Gold primary label: `other_quality_abnormal`
- Predicted top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Top features: TD_weight_mean, TD_avg_temp, cast_speed_mean, mold_level_range, heat_exchange_mean
- Example KG path: Low superheat [affect] mold flux melting

### baosteel-structured-86

- Gold primary label: `other_quality_abnormal`
- Predicted top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Top features: TD_weight_mean, TD_avg_temp, cast_speed_mean, mold_level_range, heat_exchange_mean
- Example KG path: Low superheat [affect] mold flux melting

### baosteel-structured-87

- Gold primary label: `transition_tundish`
- Predicted top3: `transition_tundish, process_fluctuation, speed_stopper_flow`
- Top features: tundish_sequence_count, 交接部开始位置/mm, 交接部长度/mm, TD_weight_range, 中间包吨位波动/t
- Example KG path: none

### baosteel-structured-89

- Gold primary label: `other_quality_abnormal`
- Predicted top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Top features: TD_weight_mean, TD_avg_temp, cast_speed_mean, mold_level_range, heat_exchange_mean
- Example KG path: Low superheat [affect] mold flux melting

### baosteel-structured-90

- Gold primary label: `other_quality_abnormal`
- Predicted top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Top features: TD_weight_mean, TD_avg_temp, cast_speed_mean, mold_level_range, heat_exchange_mean
- Example KG path: Low superheat [affect] mold flux melting

## Interpretation

- `feature_name_naive_bayes` is the strongest non-LLM lexical baseline because the weak labels are built from feature names and groups.
- If feature-only baselines approach 1.0, treat this as weak-label leakage evidence rather than true expert-level traceability performance.
- `kg_path_reasoning` measures whether the mechanism graph can provide evidence-backed trace paths, not only label prediction.
- `proposed_plm_llm_kg_fusion` combines feature-level evidence, KG anchors, and trace paths as a pilot proxy for the planned PLM-LLM-KG system.
- Expert-reviewed cases are still required for publication-level trace path and action recommendation claims.
