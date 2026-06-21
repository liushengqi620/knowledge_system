# C-MAPSS Pseudo-Truncation Validation Audit

- Version: cmapss-pseudo-truncation-validation-audit-v1
- Status: `pseudo_truncation_validation_complete_with_score_tradeoff`
- Claim boundary: This audit validates C-MAPSS cap/window selection on train-split pseudo-terminal units. It supports RMSE-oriented temporal-anchor selection only; path-fusion branches still require their own validation-admission proof, and PHM score trade-offs must be reported separately.
- Seeds: 42, 43, 44
- Target pseudo-terminal RULs: 20, 50, 80, 110, 140, 170

## Candidate Summary

| Candidate | Seeds | Cap | Window | Pseudo-val RMSE | Pseudo-val score | Official-test RMSE | Official-test score |
|---|---:|---:|---:|---:|---:|---:|---:|
| gru_w160_cap150 | 3 | 150 | 160 | 16.8290 +/- 0.8296 | 36636.78 | 18.2840 +/- 0.1324 | 6619.39 |
| gru_w80_cap125 | 3 | 125 | 80 | 21.9487 +/- 0.3888 | 54579.22 | 20.6822 +/- 0.1218 | 7403.73 |
| gru_w80_cap150 | 3 | 150 | 80 | 17.2479 +/- 0.4280 | 47585.59 | 18.4782 +/- 0.1958 | 6211.19 |

## Selection

- Selected by pseudo-validation RMSE: `gru_w160_cap150`
- Best by official-test RMSE audit: `gru_w160_cap150`
- Selected by pseudo-validation PHM score: `gru_w160_cap150`
- Best by official-test PHM score audit: `gru_w80_cap150`
- Official-test score trade-off if RMSE-selected branch is deployed: `408.20`

## Gate Status

| Gate | Status |
|---|---|
| pseudo_terminal_validation_train_only | pass |
| all_candidates_materialized | pass |
| selection_declared_without_test_metrics | pass |
| pseudo_rmse_selection_matches_best_test_rmse | pass |
| cap150_preferred_over_cap125_w80_by_pseudo_rmse | pass |
| long_window_preferred_over_w80_cap150_by_pseudo_rmse | pass |
| pseudo_score_selection_matches_best_test_score | closed |
| official_score_tradeoff_disclosed | pass |

## Next Actions

- If pseudo-selection and official-test ranking disagree, keep C-MAPSS as exploratory support and rerun a predeclared wider validation panel.
- Path-fusion variants must be evaluated against the same pseudo-terminal panel before any C-MAPSS path-fusion claim is admitted.
- Published C-MAPSS baselines still require exact cap, subset, score, preprocessing, and budget alignment before literature-wide SOTA wording.
