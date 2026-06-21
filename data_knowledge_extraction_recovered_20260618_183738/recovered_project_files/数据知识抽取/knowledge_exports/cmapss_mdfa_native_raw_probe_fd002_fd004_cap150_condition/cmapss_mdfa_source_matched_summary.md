# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=26.4049, MAE=19.7242, Score=17839.07, prediction records=507

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD002 | 42 | 26.8362 | 19.1781 | 9852.94 | sensor21_pca | kmeans6_settings+onehot | 18 | 105.58 |
| FD004 | 42 | 25.9469 | 20.2946 | 7986.14 | sensor21_pca | kmeans6_settings+onehot | 17 | 139.06 |
