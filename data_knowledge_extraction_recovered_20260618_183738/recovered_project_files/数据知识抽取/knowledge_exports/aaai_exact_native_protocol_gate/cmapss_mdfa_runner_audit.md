# C-MAPSS MDFA Runner Audit

- Version: cmapss-mdfa-runner-audit-v1
- Status: `smoke_runner_materialized_full_budget_pending`
- Claim boundary: The MDFA source-matched runner and all-subset smoke prediction archive are materialized. The smoke run is not a published reproduction because it uses a reduced training budget and unresolved PCA/key-sensor policy.

## Gate Status

| Gate | Status |
|---|---|
| runner_code_present | pass |
| smoke_summary_present | pass |
| smoke_seed_archive_present | pass |
| smoke_all_subsets_present | pass |
| smoke_terminal_prediction_records_present | pass |
| terminal_prediction_records_complete_for_present_seeds | pass |
| smoke_claim_safe | pass |
| full_three_seed_archive_present | missing |
| full_source_budget_100epoch_present | missing |
| pca_key_sensor_exact_policy_verified | missing |
| safe_to_promote_mdfa_to_exact_reproduction | missing |

## Smoke Diagnostic Rows

| Subset | Seed | Formulation | Feature policy | Condition policy | LR scheduler | Epochs | Batch | LR | Dropout | Test windows | Prediction records |
|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|
| FD001 | 42 | source_2d | all24_pca | none | none | 1 | 32 | 0.000100 | 0.30 | 100 | 100 |
| FD002 | 42 | source_2d | all24_pca | none | none | 1 | 32 | 0.000100 | 0.30 | 259 | 259 |
| FD003 | 42 | source_2d | all24_pca | none | none | 1 | 32 | 0.000100 | 0.30 | 100 | 100 |
| FD004 | 42 | source_2d | all24_pca | none | none | 1 | 32 | 0.000100 | 0.30 | 248 | 248 |

## Next Actions

- Run the MDFA runner with source_2d formulation, seeds 42/43/44, epochs=100, batch=32, lr=0.0001, dropout=0.3, and full train windows.
- Decide and freeze the PCA/key-sensor policy from the MDFA source: all 24 variables with train-only PCA, Table 4 key sensors, or Table 6 screened variables.
- Compare FD001-FD004 RMSE/Score against MDFA Table 5 only after the full-budget archive exists.
- Keep current smoke metrics out of SOTA tables; use them only as runner and archive readiness evidence.
