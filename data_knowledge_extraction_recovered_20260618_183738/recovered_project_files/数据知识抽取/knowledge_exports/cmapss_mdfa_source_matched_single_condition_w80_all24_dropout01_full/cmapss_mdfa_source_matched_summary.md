# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=13.0866, MAE=9.0909, Score=2158.11, prediction records=600

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 12.4170 | 8.9028 | 248.70 | all24_pca | none | 12 | 210.15 |
| FD001 | 43 | 12.3401 | 9.1217 | 233.65 | all24_pca | none | 12 | 211.84 |
| FD001 | 44 | 12.8923 | 9.4685 | 254.09 | all24_pca | none | 12 | 208.72 |
| FD003 | 42 | 13.0125 | 8.6795 | 390.13 | all24_pca | none | 10 | 257.16 |
| FD003 | 43 | 13.3404 | 8.9951 | 493.41 | all24_pca | none | 10 | 254.89 |
| FD003 | 44 | 14.4078 | 9.3777 | 538.13 | all24_pca | none | 10 | 249.99 |
