# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=12.6817, MAE=8.8296, Score=642.70, prediction records=200

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 12.4668 | 9.0311 | 253.46 | all24_pca | none | 12 | 52.26 |
| FD003 | 42 | 12.8930 | 8.6282 | 389.23 | all24_pca | none | 10 | 63.00 |
