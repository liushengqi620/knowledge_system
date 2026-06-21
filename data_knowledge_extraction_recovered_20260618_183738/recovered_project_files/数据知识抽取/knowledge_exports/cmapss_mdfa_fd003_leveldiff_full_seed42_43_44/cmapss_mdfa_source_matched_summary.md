# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=12.9271, MAE=9.0524, Score=990.58, prediction records=300

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Temporal mode | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---|---:|---:|
| FD003 | 42 | 12.9032 | 9.2798 | 302.91 | all24_pca | level_diff | none | 10/20 | 182.75 |
| FD003 | 43 | 12.7379 | 9.1553 | 304.12 | all24_pca | level_diff | none | 10/20 | 255.64 |
| FD003 | 44 | 13.1370 | 8.7221 | 383.55 | all24_pca | level_diff | none | 10/20 | 243.63 |
