# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| lstm_sequence | 1 | 45.3848 | 0.0000 | 36.5488 | 229178.56 | 0.33 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| lstm_sequence | FD001 | 35.5788 | 0.0000 | 30.7673 | 3180.38 |
| lstm_sequence | FD002 | 48.3697 | 0.0000 | 38.5439 | 129261.48 |
| lstm_sequence | FD003 | 33.4097 | 0.0000 | 28.3986 | 2989.99 |
| lstm_sequence | FD004 | 49.6801 | 0.0000 | 40.0828 | 93746.71 |
