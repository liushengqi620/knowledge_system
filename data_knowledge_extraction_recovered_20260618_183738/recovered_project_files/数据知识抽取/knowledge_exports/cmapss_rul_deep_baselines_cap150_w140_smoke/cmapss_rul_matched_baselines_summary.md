# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 18.0832 | 0.0000 | 12.3611 | 5741.18 | 4.38 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 14.8913 | 0.0000 | 10.4946 | 470.36 |
| gru_sequence | FD002 | 19.8725 | 0.0000 | 13.4529 | 2629.84 |
| gru_sequence | FD003 | 14.5101 | 0.0000 | 9.5255 | 896.21 |
| gru_sequence | FD004 | 18.5871 | 0.0000 | 13.1169 | 1744.78 |
