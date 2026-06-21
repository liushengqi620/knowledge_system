# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| lstm_sequence | 3 | 21.6521 | 0.2169 | 14.1923 | 9679.97 | 4.00 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| lstm_sequence | FD001 | 14.3445 | 0.5365 | 10.6071 | 344.41 |
| lstm_sequence | FD002 | 23.7903 | 0.3547 | 15.5007 | 5070.36 |
| lstm_sequence | FD003 | 13.7899 | 1.0112 | 9.8255 | 455.15 |
| lstm_sequence | FD004 | 24.1913 | 0.1359 | 16.0323 | 3810.05 |
