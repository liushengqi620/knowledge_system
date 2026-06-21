# C-MAPSS Matched RUL Baselines

All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.

## Overall

| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| extra_trees_summary | 3 | 23.8914 | 0.1563 | 15.8278 | 13690.52 | 0.62 |
| histgb_summary | 3 | 23.4635 | 0.1624 | 15.3453 | 13625.12 | 3.00 |
| ridge_summary | 3 | 28.2539 | 0.1500 | 20.5683 | 29111.88 | 0.03 |

## Subset Summary

| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---|---:|---:|---:|---:|
| extra_trees_summary | FD001 | 14.7066 | 0.1877 | 10.7463 | 299.28 |
| extra_trees_summary | FD002 | 26.4020 | 0.2214 | 17.2609 | 8022.19 |
| extra_trees_summary | FD003 | 14.8692 | 0.0714 | 10.4880 | 453.43 |
| extra_trees_summary | FD004 | 26.8863 | 0.1733 | 18.5332 | 4915.62 |
| histgb_summary | FD001 | 14.5668 | 0.0616 | 10.7256 | 312.85 |
| histgb_summary | FD002 | 26.0815 | 0.2653 | 17.0492 | 8151.37 |
| histgb_summary | FD003 | 14.8592 | 0.1334 | 10.1987 | 554.78 |
| histgb_summary | FD004 | 26.1618 | 0.1121 | 17.5038 | 4606.12 |
| ridge_summary | FD001 | 18.6254 | 0.1348 | 15.1192 | 491.77 |
| ridge_summary | FD002 | 30.5393 | 0.2186 | 21.7093 | 16742.67 |
| ridge_summary | FD003 | 18.1999 | 0.0543 | 14.2004 | 602.22 |
| ridge_summary | FD004 | 32.0659 | 0.2659 | 24.1416 | 11275.22 |
