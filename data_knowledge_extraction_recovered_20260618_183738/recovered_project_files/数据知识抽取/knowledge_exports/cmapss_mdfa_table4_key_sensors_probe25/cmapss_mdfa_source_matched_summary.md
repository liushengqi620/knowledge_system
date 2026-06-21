# C-MAPSS MDFA Source-Matched Candidate

- Status: `source_matched_candidate_not_exact_reproduction`
- Claim boundary: This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains a source-matched candidate until PCA/key-sensor details and matched budget are finalized.

## Overall

- RMSE=26.2145, MAE=19.3032, Score=47917.67, prediction records=707

## Subset/Seed Rows

| Subset | Seed | RMSE | MAE | Score | Feature policy | Condition policy | PCA/Input dim | Train seconds |
|---|---:|---:|---:|---:|---|---|---:|---:|
| FD001 | 42 | 15.7251 | 11.4802 | 622.46 | mdfa_key_sensors_pca | none | 7 | 53.21 |
| FD002 | 42 | 26.4954 | 20.4465 | 10641.34 | mdfa_key_sensors_pca | none | 2 | 138.44 |
| FD003 | 42 | 18.4466 | 12.9363 | 1564.66 | mdfa_key_sensors_pca | none | 6 | 46.78 |
| FD004 | 42 | 31.4487 | 23.8309 | 35089.20 | mdfa_key_sensors_pca | none | 2 | 121.53 |
