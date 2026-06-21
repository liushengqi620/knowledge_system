# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 18.3939 | 0.0000 | 12.3358 | 8789.26 | 9.82 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 17.1420 | 0.0000 | 11.1388 | 1244.00 |
| gru_sequence | FD002 | 20.2645 | 0.0000 | 13.7104 | 4547.77 |
| gru_sequence | FD003 | 15.8095 | 0.0000 | 10.0993 | 1230.81 |
| gru_sequence | FD004 | 17.7876 | 0.0000 | 12.2847 | 1766.68 |
