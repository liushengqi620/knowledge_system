# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 17.9368 | 0.0000 | 12.1169 | 5492.67 | 4.48 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 14.7538 | 0.0000 | 10.2983 | 518.02 |
| gru_sequence | FD002 | 19.1712 | 0.0000 | 12.6619 | 2335.24 |
| gru_sequence | FD003 | 16.1025 | 0.0000 | 10.8996 | 927.32 |
| gru_sequence | FD004 | 18.4669 | 0.0000 | 12.7720 | 1712.09 |
