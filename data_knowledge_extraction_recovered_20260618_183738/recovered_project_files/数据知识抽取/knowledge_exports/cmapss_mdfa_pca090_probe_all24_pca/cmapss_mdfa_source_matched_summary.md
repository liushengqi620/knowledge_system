# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=34.5762, MAE=25.1348, Score=474457.60, prediction records=707

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 15.0374 | 10.5131 | 645.35 | all24_pca | none | 9 | 55.32 |
| FD002 | 42 | 40.2631 | 32.9614 | 116884.78 | all24_pca | none | 2 | 141.65 |
| FD003 | 42 | 17.7956 | 11.9347 | 1758.33 | all24_pca | none | 7 | 57.00 |
| FD004 | 42 | 38.6818 | 28.1796 | 355169.12 | all24_pca | none | 2 | 135.68 |
