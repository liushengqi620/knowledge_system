# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 17.8654 | 0.0000 | 11.8462 | 6043.31 | 4.30 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 14.8374 | 0.0000 | 10.0007 | 696.88 |
| gru_sequence | FD002 | 20.1329 | 0.0000 | 13.4133 | 3029.52 |
| gru_sequence | FD003 | 13.9446 | 0.0000 | 8.8404 | 887.98 |
| gru_sequence | FD004 | 17.8721 | 0.0000 | 12.1659 | 1428.94 |
