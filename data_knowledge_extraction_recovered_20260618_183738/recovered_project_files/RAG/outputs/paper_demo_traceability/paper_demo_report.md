# Paper-Demo KG-Enhanced Anomaly Traceability Experiment

## Scope

This package upgrades the weak-label pilot into a paper-style demonstration by adding leakage-controlled scenarios, balanced subsets, path-quality proxies, ablations, and an expert-audit template.

It is still not a final publication benchmark until experts review root causes, trace paths, and recommended actions.

## Inputs

- Train records: 83568
- Full test records: 10430
- Balanced demonstration records: 1235
- Mechanism KG: `C:\Users\CPILAB\Documents\xwechat_files\wxid_fn3terjpgaio22_c340\msg\file\2026-06\codex_recovery\data_knowledge_extraction_recovered_20260618_183738\recovered_project_files\RAG\data\quality_traceability_large_kg\quality_traceability_large_kg_seed.json`

## Scenario Definitions

- `full_weak_label_masked_text`: full test set; label text masked from record text, feature names/groups retained.
- `balanced_label_masked_text`: balanced subset; label text masked, feature names/groups retained.
- `balanced_group_only`: balanced subset; feature names masked, feature groups retained.
- `balanced_feature_anonymized`: balanced subset; both feature names and groups masked.

## Metrics

| Scenario | Method | Hit@1 | Hit@3 | MRR | Macro F1 | Coverage | Path Quality | Faithful Path Rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| full_weak_label_masked_text | `label_prior_majority` | 0.3244 | 0.7918 | 0.5686 | 0.0612 | 0.0 | 0.0 | 0.0 |
| full_weak_label_masked_text | `feature_group_prior` | 0.9993 | 0.9993 | 0.9994 | 0.8748 | 0.0 | 0.0 | 0.0 |
| full_weak_label_masked_text | `feature_name_naive_bayes` | 0.9993 | 0.9993 | 0.9994 | 0.8748 | 0.0 | 0.0 | 0.0 |
| full_weak_label_masked_text | `kg_anchor_reasoning` | 0.3652 | 0.6751 | 0.5261 | 0.3041 | 0.0 | 0.0 | 0.0 |
| full_weak_label_masked_text | `kg_path_reasoning` | 0.1529 | 0.4253 | 0.3975 | 0.181 | 0.8711 | 0.7149 | 0.6428 |
| full_weak_label_masked_text | `proposed_score_fusion` | 0.9993 | 0.9994 | 0.9994 | 0.8748 | 0.4037 | 0.3389 | 0.4037 |
| full_weak_label_masked_text | `proposed_explainable_rerank` | 0.9993 | 0.9994 | 0.9994 | 0.8748 | 0.4462 | 0.3814 | 0.4462 |
| balanced_label_masked_text | `label_prior_majority` | 0.1619 | 0.4858 | 0.4008 | 0.0348 | 0.0 | 0.0 | 0.0 |
| balanced_label_masked_text | `feature_group_prior` | 1.0 | 1.0 | 1.0 | 0.875 | 0.0 | 0.0 | 0.0 |
| balanced_label_masked_text | `feature_name_naive_bayes` | 1.0 | 1.0 | 1.0 | 0.875 | 0.0 | 0.0 | 0.0 |
| balanced_label_masked_text | `kg_anchor_reasoning` | 0.37 | 0.8381 | 0.5818 | 0.2987 | 0.0 | 0.0 | 0.0 |
| balanced_label_masked_text | `kg_path_reasoning` | 0.3142 | 0.5142 | 0.5143 | 0.2348 | 0.8478 | 0.7506 | 0.6858 |
| balanced_label_masked_text | `proposed_score_fusion` | 1.0 | 1.0 | 1.0 | 0.875 | 0.5239 | 0.4915 | 0.5239 |
| balanced_label_masked_text | `proposed_explainable_rerank` | 1.0 | 1.0 | 1.0 | 0.875 | 0.5579 | 0.5255 | 0.5579 |
| balanced_group_only | `label_prior_majority` | 0.1619 | 0.4858 | 0.4008 | 0.0348 | 0.0 | 0.0 | 0.0 |
| balanced_group_only | `feature_group_prior` | 1.0 | 1.0 | 1.0 | 0.875 | 0.0 | 0.0 | 0.0 |
| balanced_group_only | `feature_name_naive_bayes` | 0.1619 | 0.4858 | 0.4008 | 0.0348 | 0.0 | 0.0 | 0.0 |
| balanced_group_only | `kg_anchor_reasoning` | 0.566 | 0.8381 | 0.7425 | 0.489 | 0.0 | 0.0 | 0.0 |
| balanced_group_only | `kg_path_reasoning` | 0.3522 | 0.6761 | 0.5951 | 0.3125 | 0.3239 | 0.2915 | 0.3239 |
| balanced_group_only | `proposed_score_fusion` | 1.0 | 1.0 | 1.0 | 0.875 | 0.1619 | 0.1619 | 0.1619 |
| balanced_group_only | `proposed_explainable_rerank` | 1.0 | 1.0 | 1.0 | 0.875 | 0.1619 | 0.1619 | 0.1619 |
| balanced_feature_anonymized | `label_prior_majority` | 0.1619 | 0.4858 | 0.4008 | 0.0348 | 0.0 | 0.0 | 0.0 |
| balanced_feature_anonymized | `feature_group_prior` | 0.1619 | 0.4858 | 0.4008 | 0.0348 | 0.0 | 0.0 | 0.0 |
| balanced_feature_anonymized | `feature_name_naive_bayes` | 0.1619 | 0.4858 | 0.4008 | 0.0348 | 0.0 | 0.0 | 0.0 |
| balanced_feature_anonymized | `kg_anchor_reasoning` | 0.3522 | 0.8381 | 0.6356 | 0.2917 | 0.0 | 0.0 | 0.0 |
| balanced_feature_anonymized | `kg_path_reasoning` | 0.3522 | 0.8381 | 0.6356 | 0.2917 | 0.0 | 0.0 | 0.0 |
| balanced_feature_anonymized | `proposed_score_fusion` | 0.4858 | 0.5781 | 0.6104 | 0.2983 | 0.0 | 0.0 | 0.0 |
| balanced_feature_anonymized | `proposed_explainable_rerank` | 0.3239 | 0.6478 | 0.5435 | 0.2083 | 0.0 | 0.0 | 0.0 |

## Case Study Samples

### full_weak_label_masked_text / baosteel-structured-79

- Gold label: `mold_level_slag_risk`
- Proposed top3: `mold_level_slag_risk, process_fluctuation, speed_stopper_flow`
- Path quality proxy: `1.0`
- Trace path: High casting speed [affect] mold heat transfer stability

### full_weak_label_masked_text / baosteel-structured-82

- Gold label: `other_quality_abnormal`
- Proposed top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Path quality proxy: `0.8`
- Trace path: Low superheat [affect] mold flux melting

### full_weak_label_masked_text / baosteel-structured-83

- Gold label: `other_quality_abnormal`
- Proposed top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Path quality proxy: `0.8`
- Trace path: Low superheat [affect] mold flux melting

### full_weak_label_masked_text / baosteel-structured-85

- Gold label: `other_quality_abnormal`
- Proposed top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Path quality proxy: `0.8`
- Trace path: Low superheat [affect] mold flux melting

### full_weak_label_masked_text / baosteel-structured-86

- Gold label: `other_quality_abnormal`
- Proposed top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Path quality proxy: `0.8`
- Trace path: Low superheat [affect] mold flux melting

### full_weak_label_masked_text / baosteel-structured-87

- Gold label: `transition_tundish`
- Proposed top3: `transition_tundish, process_fluctuation, speed_stopper_flow`
- Path quality proxy: `0.0`
- Trace path: none

### full_weak_label_masked_text / baosteel-structured-89

- Gold label: `other_quality_abnormal`
- Proposed top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Path quality proxy: `0.8`
- Trace path: Low superheat [affect] mold flux melting

### full_weak_label_masked_text / baosteel-structured-90

- Gold label: `other_quality_abnormal`
- Proposed top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Path quality proxy: `0.8`
- Trace path: Low superheat [affect] mold flux melting

### full_weak_label_masked_text / baosteel-structured-93

- Gold label: `other_quality_abnormal`
- Proposed top3: `other_quality_abnormal, mold_level_slag_risk, process_fluctuation`
- Path quality proxy: `0.8`
- Trace path: Low superheat [affect] mold flux melting

### full_weak_label_masked_text / baosteel-structured-95

- Gold label: `temperature_flux`
- Proposed top3: `temperature_flux, other_quality_abnormal, heat_transfer_imbalance`
- Path quality proxy: `0.0`
- Trace path: none

### full_weak_label_masked_text / baosteel-structured-97

- Gold label: `transition_tundish`
- Proposed top3: `transition_tundish, process_fluctuation, speed_stopper_flow`
- Path quality proxy: `0.0`
- Trace path: none

### full_weak_label_masked_text / baosteel-structured-99

- Gold label: `process_fluctuation`
- Proposed top3: `process_fluctuation, speed_stopper_flow, heat_transfer_imbalance`
- Path quality proxy: `1.0`
- Trace path: High casting speed [affect] mold heat transfer stability

## How To Use In A Paper Demo

1. Use the full weak-label scenario only to show the current downstream data is not a gold benchmark.
2. Use balanced and masked scenarios to demonstrate leakage awareness and robustness checks.
3. Use path quality, faithful path rate, and expert audit results as the main traceability evidence.
4. Do not claim production root-cause accuracy until `expert_audit_template.csv` is reviewed.
