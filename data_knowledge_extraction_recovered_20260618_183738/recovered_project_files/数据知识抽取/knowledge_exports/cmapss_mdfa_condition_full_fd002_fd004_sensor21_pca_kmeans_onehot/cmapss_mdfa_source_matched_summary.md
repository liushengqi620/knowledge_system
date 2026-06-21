# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=15.9012, MAE=11.3222, Score=10523.04, prediction records=1521

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD002 | 42 | 15.9937 | 11.7350 | 1489.52 | sensor21_pca | kmeans6_settings+onehot | 18 | 543.25 |
| FD002 | 43 | 15.9896 | 11.6835 | 1419.79 | sensor21_pca | kmeans6_settings+onehot | 18 | 557.62 |
| FD002 | 44 | 15.5398 | 11.4631 | 1189.43 | sensor21_pca | kmeans6_settings+onehot | 18 | 543.07 |
| FD004 | 42 | 16.2751 | 11.3778 | 2033.45 | sensor21_pca | kmeans6_settings+onehot | 17 | 617.91 |
| FD004 | 43 | 16.0349 | 11.0516 | 2446.25 | sensor21_pca | kmeans6_settings+onehot | 17 | 624.09 |
| FD004 | 44 | 15.5689 | 10.5818 | 1944.60 | sensor21_pca | kmeans6_settings+onehot | 17 | 604.80 |
