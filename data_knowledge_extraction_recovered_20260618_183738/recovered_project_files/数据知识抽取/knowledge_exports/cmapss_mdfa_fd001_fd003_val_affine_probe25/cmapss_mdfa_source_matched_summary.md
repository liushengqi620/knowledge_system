# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=12.4957, MAE=8.8282, Score=565.98, prediction records=200

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 12.3489 | 8.9999 | 253.57 | all24_pca | none | 12 | 47.85 |
| FD003 | 42 | 12.6409 | 8.6565 | 312.42 | all24_pca | none | 10 | 62.40 |
