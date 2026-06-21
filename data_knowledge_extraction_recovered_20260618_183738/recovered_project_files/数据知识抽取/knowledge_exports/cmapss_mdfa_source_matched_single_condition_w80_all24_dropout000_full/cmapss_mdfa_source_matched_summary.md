# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=12.9439, MAE=9.1110, Score=1757.16, prediction records=600

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 12.3546 | 8.9977 | 254.19 | all24_pca | none | 12 | 202.71 |
| FD001 | 43 | 12.4138 | 9.2809 | 225.66 | all24_pca | none | 12 | 167.28 |
| FD001 | 44 | 13.9227 | 10.2098 | 270.47 | all24_pca | none | 12 | 195.01 |
| FD003 | 42 | 12.6672 | 8.6592 | 315.81 | all24_pca | none | 10 | 215.79 |
| FD003 | 43 | 13.2160 | 8.5829 | 366.75 | all24_pca | none | 10 | 174.70 |
| FD003 | 44 | 13.0221 | 8.9355 | 324.29 | all24_pca | none | 10 | 245.53 |
