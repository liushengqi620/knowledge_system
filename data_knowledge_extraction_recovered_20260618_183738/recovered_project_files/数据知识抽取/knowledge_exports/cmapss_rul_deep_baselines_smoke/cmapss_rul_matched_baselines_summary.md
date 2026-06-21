# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| gru_sequence | 1 | 39.0352 | 0.0000 | 31.4198 | 97951.91 | 0.38 |
| tcn_sequence | 1 | 41.3368 | 0.0000 | 32.9980 | 135713.96 | 0.13 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| gru_sequence | FD001 | 31.3338 | 0.0000 | 27.1076 | 2187.81 |
| gru_sequence | FD002 | 41.9914 | 0.0000 | 33.4174 | 61915.09 |
| gru_sequence | FD003 | 27.7421 | 0.0000 | 22.6913 | 1659.47 |
| gru_sequence | FD004 | 42.3815 | 0.0000 | 34.5920 | 32189.53 |
| tcn_sequence | FD001 | 34.2813 | 0.0000 | 28.9016 | 3308.66 |
| tcn_sequence | FD002 | 44.1859 | 0.0000 | 35.0674 | 73771.86 |
| tcn_sequence | FD003 | 29.6424 | 0.0000 | 24.4059 | 2309.55 |
| tcn_sequence | FD004 | 44.7672 | 0.0000 | 35.9533 | 56323.89 |
