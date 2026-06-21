# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 17.5840 | 0.0000 | 11.8471 | 5499.28 | 4.43 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 15.7438 | 0.0000 | 10.8933 | 910.07 |
| gru_sequence | FD002 | 19.2004 | 0.0000 | 13.0271 | 2109.91 |
| gru_sequence | FD003 | 14.6757 | 0.0000 | 9.3543 | 1050.52 |
| gru_sequence | FD004 | 17.5972 | 0.0000 | 12.0044 | 1428.78 |
