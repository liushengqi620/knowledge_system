# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 3 | 20.7559 | 0.1402 | 13.3039 | 7531.00 | 4.24 |
| tcn_sequence | 3 | 25.8894 | 0.2915 | 18.3569 | 19477.53 | 4.60 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 12.6296 | 0.2247 | 9.2710 | 252.56 |
| gru_sequence | FD002 | 23.1124 | 0.2322 | 14.8695 | 3786.03 |
| gru_sequence | FD003 | 11.2860 | 0.2121 | 7.9696 | 240.39 |
| gru_sequence | FD004 | 23.5480 | 0.2205 | 15.4459 | 3252.02 |
| tcn_sequence | FD001 | 19.0395 | 0.2239 | 14.2239 | 669.89 |
| tcn_sequence | FD002 | 27.2182 | 0.3969 | 19.1232 | 8116.54 |
| tcn_sequence | FD003 | 19.0273 | 0.7116 | 14.0005 | 1410.31 |
| tcn_sequence | FD004 | 29.0642 | 0.2584 | 20.9796 | 9280.79 |
