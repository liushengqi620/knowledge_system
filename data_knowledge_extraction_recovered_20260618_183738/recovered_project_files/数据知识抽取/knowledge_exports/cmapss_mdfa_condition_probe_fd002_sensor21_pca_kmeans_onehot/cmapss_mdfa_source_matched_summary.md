# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=17.4615, MAE=12.6250, Score=1847.49, prediction records=259

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD002 | 42 | 17.4615 | 12.6250 | 1847.49 | sensor21_pca | kmeans6_settings+onehot | 18 | 137.96 |
