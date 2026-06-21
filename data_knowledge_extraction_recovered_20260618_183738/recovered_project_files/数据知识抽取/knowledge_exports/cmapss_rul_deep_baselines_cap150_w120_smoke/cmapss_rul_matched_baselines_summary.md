# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 17.7758 | 0.0000 | 11.6602 | 5189.15 | 4.36 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 14.3364 | 0.0000 | 9.7817 | 559.53 |
| gru_sequence | FD002 | 19.8886 | 0.0000 | 13.0725 | 2457.83 |
| gru_sequence | FD003 | 13.3536 | 0.0000 | 8.6279 | 640.88 |
| gru_sequence | FD004 | 18.2458 | 0.0000 | 12.1655 | 1530.91 |
