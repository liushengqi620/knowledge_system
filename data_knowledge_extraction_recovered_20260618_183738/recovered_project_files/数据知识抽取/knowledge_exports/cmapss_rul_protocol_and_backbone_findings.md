# C-MAPSS RUL Protocol And Backbone Findings

Date: 2026-06-20

## Finding

The previous C-MAPSS RUL result was not a valid paper-level RUL protocol because it evaluated RUL on many intermediate test time points. The original C-MAPSS test protocol evaluates each test engine at its final observed cycle. After switching the C-MAPSS RUL primary metric to terminal test-unit evaluation, the same anchor improved from the old all-row RMSE mean `66.3836` to a terminal-test RMSE mean about `31.26`.

## Formal Results

All results below are under `knowledge_exports/aaai_formal_public_runs` and use seeds `42/43/44`.

| Branch | Protocol | RMSE | Mean RMSE | Notes |
|---|---|---:|---:|---|
| `cmapss_original_rul_anchor` | terminal test-unit RUL, window 48 | `30.4748 / 32.3203 / 30.9711` | `31.2554` | Health-index inverse RUL head only |
| `cmapss_rul_direct_regime_tempmix` | terminal test-unit RUL, window 80 | `23.5643 / 24.0440 / 23.9102` | `23.8395` | Direct capped-RUL head, train-only regime residuals, temporal mixer |
| `cmapss_rul_direct_regime_bitempmix` | terminal test-unit RUL, window 80 | `21.4378 / 21.5389 / 22.0879` | `21.6882` | Adds bidirectional encoding inside the historical window |
| `cmapss_rul_anchorpath_bigru_cls020` | terminal test-unit RUL, window 80 | `20.6429 / 20.3136 / 20.4809` | `20.4792` | Weak derived-class loss, BiGRU temporal anchor, validation-selected path residual fusion |

The strongest formal branch reaches MAE mean `13.2397` and score mean `7185.62`, with low seed-to-seed variance. It improves the previous formal bitempmix branch by about `1.21` RMSE points.

## Matched Baselines

Matched non-deep RUL baselines use the same ready data, grouped validation, terminal test-unit evaluation, capped RUL supervision, train-only regime residuals, and window-summary features.

| Baseline | RMSE Mean | MAE Mean | Score Mean |
|---|---:|---:|---:|
| Ridge summary | `28.2539` | `20.5683` | `29111.88` |
| HistGradientBoosting summary | `23.4635` | `15.3453` | `13625.12` |
| ExtraTrees summary | `23.8914` | `15.8278` | `13690.52` |
| TCN sequence | `25.8894` | `18.3569` | `19477.53` |
| GRU sequence | `20.7559` | `13.3039` | `7531.00` |

The current strongest neural path-fusion branch improves the best matched deep baseline, GRU sequence, by about `0.28` RMSE points and has a lower RUL score.

## Interpretation

The improvement comes from two separate corrections:

1. Protocol correction: terminal test-unit evaluation aligns the task with the original C-MAPSS RUL setting and supersedes the old all-test-row metric.
2. Algorithm correction: direct RUL supervision, train-only operating-regime residualization, longer temporal windows, BiGRU temporal anchoring, weak derived-class supervision, and validation-selected path residual fusion give a consistent reduction from the corrected anchor.

This supports a paper narrative in which the model is not a generic classifier. For RUL, the same path-fusion backbone is adapted through task-valid output supervision, operating-regime residual evidence, and a temporal-anchor residual path gate. The path branch is not allowed to dominate the temporal signal; it acts as a reliability-gated residual challenger and is selected by validation RMSE.

## Remaining Requirements

- Align the final paper table with official FD001-FD004 reporting conventions.
- Add compatible published C-MAPSS literature baselines before claiming literature-wide SOTA.
- Do not use the old all-row C-MAPSS RMSE values in final paper tables.
