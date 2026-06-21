# C-MAPSS Terminal RUL Report

All rows use terminal test-unit evaluation. RMSE/MAE lower is better; score lower is better.

## Overall

| Branch | Seeds | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---:|---:|---:|---:|---:|
| cmapss_original_rul_anchor | 3 | 31.2554 | 0.7798 | 23.5637 | 41469.99 |
| cmapss_rul_direct_regime_tempmix | 3 | 23.8395 | 0.2021 | 16.4639 | 12964.15 |
| cmapss_rul_direct_regime_bitempmix | 3 | 21.6882 | 0.2857 | 14.5936 | 8816.97 |
| cmapss_rul_anchorpath_bigru_cls020 | 3 | 20.4792 | 0.1344 | 13.2397 | 7185.62 |

## Subset Summary

### cmapss_original_rul_anchor

| Subset | Units | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---:|---:|---:|---:|---:|
| FD001 | 100 | 21.0392 | 1.6796 | 15.9603 | 860.55 |
| FD002 | 259 | 31.6828 | 0.5597 | 23.9906 | 16071.26 |
| FD003 | 100 | 22.1018 | 2.4658 | 16.9950 | 2112.16 |
| FD004 | 248 | 36.8597 | 0.5969 | 28.8325 | 22426.02 |

### cmapss_rul_direct_regime_tempmix

| Subset | Units | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---:|---:|---:|---:|---:|
| FD001 | 100 | 15.5404 | 0.2619 | 11.3651 | 378.34 |
| FD002 | 259 | 25.7193 | 0.1628 | 17.4551 | 6876.20 |
| FD003 | 100 | 15.9610 | 0.5159 | 11.6885 | 853.56 |
| FD004 | 248 | 27.0022 | 0.2910 | 19.4103 | 4856.06 |

### cmapss_rul_direct_regime_bitempmix

| Subset | Units | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---:|---:|---:|---:|---:|
| FD001 | 100 | 13.7929 | 0.6363 | 10.6147 | 307.93 |
| FD002 | 259 | 23.8329 | 0.2642 | 15.8414 | 4461.93 |
| FD003 | 100 | 13.5291 | 0.9846 | 9.7128 | 398.40 |
| FD004 | 248 | 24.4281 | 0.3306 | 16.8630 | 3648.70 |

### cmapss_rul_anchorpath_bigru_cls020

| Subset | Units | RMSE mean | RMSE std | MAE mean | Score mean |
|---|---:|---:|---:|---:|---:|
| FD001 | 100 | 12.7491 | 0.1943 | 9.4925 | 266.73 |
| FD002 | 259 | 22.6173 | 0.2108 | 14.6260 | 3470.46 |
| FD003 | 100 | 11.8399 | 0.2553 | 8.2917 | 269.17 |
| FD004 | 248 | 23.2199 | 0.3492 | 15.2981 | 3179.25 |
