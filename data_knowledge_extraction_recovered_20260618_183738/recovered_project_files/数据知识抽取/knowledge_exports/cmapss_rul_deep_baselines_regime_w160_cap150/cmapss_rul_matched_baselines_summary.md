# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 3 | 18.0617 | 0.3621 | 12.0648 | 6525.46 | 4.34 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 15.1657 | 0.9203 | 10.4253 | 656.31 |
| gru_sequence | FD002 | 19.7550 | 0.3982 | 12.9355 | 3173.43 |
| gru_sequence | FD003 | 15.2237 | 0.6163 | 9.9542 | 1095.63 |
| gru_sequence | FD004 | 18.3215 | 0.5306 | 12.6677 | 1600.10 |
