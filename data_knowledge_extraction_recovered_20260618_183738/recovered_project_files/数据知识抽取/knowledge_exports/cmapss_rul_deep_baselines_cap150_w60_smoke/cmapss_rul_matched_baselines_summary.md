# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 19.0667 | 0.0000 | 12.6816 | 6969.15 | 4.13 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 15.0143 | 0.0000 | 10.0674 | 608.97 |
| gru_sequence | FD002 | 21.4707 | 0.0000 | 14.3386 | 3531.99 |
| gru_sequence | FD003 | 13.7894 | 0.0000 | 9.4203 | 547.73 |
| gru_sequence | FD004 | 19.6818 | 0.0000 | 13.3204 | 2280.45 |
