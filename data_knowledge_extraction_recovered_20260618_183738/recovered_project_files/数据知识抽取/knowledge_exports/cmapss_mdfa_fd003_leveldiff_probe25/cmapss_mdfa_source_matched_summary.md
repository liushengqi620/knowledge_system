# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=12.3166, MAE=8.6148, Score=279.10, prediction records=100

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Temporal mode | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---|---:|---:|
| FD003 | 42 | 12.3166 | 8.6148 | 279.10 | all24_pca | level_diff | none | 10/20 | 46.89 |
