# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=15.9161, MAE=10.8444, Score=2088.12, prediction records=200

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 14.1308 | 9.7697 | 522.61 | all24_pca | none | 12 | 210.78 |
| FD003 | 42 | 17.5203 | 11.9190 | 1565.51 | all24_pca | none | 10 | 250.73 |
