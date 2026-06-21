# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 3 | 18.4365 | 0.1686 | 12.5441 | 6428.78 | 4.04 |
| tcn_sequence | 3 | 25.6942 | 0.7432 | 18.6247 | 25817.31 | 4.58 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 15.2630 | 0.5262 | 10.7713 | 539.65 |
| gru_sequence | FD002 | 20.6299 | 0.0409 | 13.9538 | 3312.50 |
| gru_sequence | FD003 | 14.6431 | 0.8228 | 9.6006 | 847.14 |
| gru_sequence | FD004 | 18.5423 | 0.1003 | 12.9736 | 1729.51 |
| tcn_sequence | FD001 | 22.1942 | 0.9733 | 16.7472 | 1285.93 |
| tcn_sequence | FD002 | 26.6675 | 0.7577 | 18.9817 | 9757.55 |
| tcn_sequence | FD003 | 22.7363 | 1.4042 | 16.2703 | 5055.49 |
| tcn_sequence | FD004 | 27.0523 | 0.5325 | 19.9582 | 9718.34 |
