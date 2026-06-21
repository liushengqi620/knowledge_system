# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=13.2581, MAE=9.2427, Score=266.89, prediction records=100

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Temporal mode | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---|---:|---:|
| FD001 | 42 | 13.2581 | 9.2427 | 266.89 | all24_pca | level_diff | none | 12/24 | 40.71 |
