# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 18.1164 | 0.0000 | 12.2284 | 5646.39 | 4.56 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 15.1991 | 0.0000 | 10.5795 | 580.57 |
| gru_sequence | FD002 | 19.1713 | 0.0000 | 12.5937 | 2409.69 |
| gru_sequence | FD003 | 16.2660 | 0.0000 | 11.0679 | 905.15 |
| gru_sequence | FD004 | 18.7608 | 0.0000 | 12.9798 | 1750.98 |
