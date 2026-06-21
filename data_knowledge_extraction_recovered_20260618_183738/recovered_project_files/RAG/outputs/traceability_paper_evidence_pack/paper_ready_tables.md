# Paper-Ready Traceability Tables

## Controlled Scenario Results

| Scenario | Feature Hit@1 | KG Hit@1 | KG Hit@3 | KG Coverage | KG Path Quality | Proposed Hit@1 | Proposed Coverage | Proposed Path Quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_weak_label_masked_text | 0.9993 | 0.1529 | 0.4253 | 0.8711 | 0.7149 | 0.9993 | 0.4462 | 0.3814 |
| balanced_label_masked_text | 1.0000 | 0.3142 | 0.5142 | 0.8478 | 0.7506 | 1.0000 | 0.5579 | 0.5255 |
| balanced_group_only | 1.0000 | 0.3522 | 0.6761 | 0.3239 | 0.2915 | 1.0000 | 0.1619 | 0.1619 |
| balanced_feature_anonymized | 0.1619 | 0.3522 | 0.8381 | 0.0000 | 0.0000 | 0.3239 | 0.0000 | 0.0000 |

## Balanced-Scenario Ablation

| Method | Hit@1 | Hit@3 | MRR | Macro F1 | Coverage | Path Quality | Faithful Path Rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| label_prior_majority | 0.1619 | 0.4858 | 0.4008 | 0.0348 | 0.0000 | 0.0000 | 0.0000 |
| feature_group_prior | 1.0000 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 0.0000 | 0.0000 |
| feature_name_naive_bayes | 1.0000 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 0.0000 | 0.0000 |
| kg_anchor_reasoning | 0.3700 | 0.8381 | 0.5818 | 0.2987 | 0.0000 | 0.0000 | 0.0000 |
| kg_path_reasoning | 0.3142 | 0.5142 | 0.5143 | 0.2348 | 0.8478 | 0.7506 | 0.6858 |
| proposed_score_fusion | 1.0000 | 1.0000 | 1.0000 | 0.8750 | 0.5239 | 0.4915 | 0.5239 |
| proposed_explainable_rerank | 1.0000 | 1.0000 | 1.0000 | 0.8750 | 0.5579 | 0.5255 | 0.5579 |

## Expert Audit Status

- Status: `audit_pending`
- Audit rows: `80`
- Total scored cells: `0`
- No expert-score cells are filled yet. Use the blinded audit CSV before claiming expert-validated traceability performance.
