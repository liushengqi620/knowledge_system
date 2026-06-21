# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=17.6398, MAE=12.5815, Score=1993.09, prediction records=200

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 17.8423 | 12.7019 | 900.09 | all24_pca | none | 12 | 43.25 |
| FD003 | 42 | 17.4350 | 12.4610 | 1093.00 | all24_pca | none | 10 | 48.74 |
