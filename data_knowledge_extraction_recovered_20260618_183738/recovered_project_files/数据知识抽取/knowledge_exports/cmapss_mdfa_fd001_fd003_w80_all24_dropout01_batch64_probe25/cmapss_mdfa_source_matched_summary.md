# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=12.8393, MAE=8.8518, Score=649.10, prediction records=200

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 12.3329 | 8.6562 | 226.86 | all24_pca | none | 12 | 24.93 |
| FD003 | 42 | 13.3265 | 9.0474 | 422.24 | all24_pca | none | 10 | 31.27 |
