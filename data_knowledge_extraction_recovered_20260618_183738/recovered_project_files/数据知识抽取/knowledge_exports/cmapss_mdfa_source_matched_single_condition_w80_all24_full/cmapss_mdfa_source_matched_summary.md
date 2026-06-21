# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=14.1518, MAE=9.8657, Score=2991.44, prediction records=600

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 13.4483 | 9.7935 | 281.78 | all24_pca | none | 12 | 210.47 |
| FD001 | 43 | 12.6137 | 9.1177 | 251.88 | all24_pca | none | 12 | 204.03 |
| FD001 | 44 | 13.1752 | 9.7491 | 257.85 | all24_pca | none | 12 | 203.58 |
| FD003 | 42 | 13.7867 | 9.5652 | 455.04 | all24_pca | none | 10 | 249.57 |
| FD003 | 43 | 16.5620 | 11.1455 | 1105.53 | all24_pca | none | 10 | 246.51 |
| FD003 | 44 | 14.9572 | 9.8230 | 639.35 | all24_pca | none | 10 | 239.91 |
