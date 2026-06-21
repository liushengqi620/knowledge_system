# C-MAPSS RUL Backbone Optimization Audit

- Version: cmapss-rul-backbone-optimization-audit-v1
- Status: `cmapss_rul_backbone_optimization_partial`
- Claim boundary: The current C-MAPSS evidence supports a cap-corrected long-window temporal anchor. Path residual fusion is not admitted for C-MAPSS until it beats the same-window temporal anchor under validation-safe evidence.

## Result Rows

| Name | Role | Seeds | Cap | Window | RMSE | RMSE std | Score | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| gru_w80_cap125 | old matched GRU anchor | 3 | 125 | 80 | 20.7559 | 0.1402 | 7531.00 | materialized |
| gru_w80_cap150 | cap-corrected GRU anchor | 3 | 150 | 80 | 18.4365 | 0.1686 | 6428.78 | materialized |
| gru_w160_cap150 | long-window cap-corrected GRU anchor | 3 | 150 | 160 | 18.0617 | 0.3621 | 6525.46 | materialized |
| anchorpath_w80_cap125 | old AnchorPath-BiGRU path-fusion branch | 3 | 125 | 80 | 20.4792 | 0.1344 | 7185.62 | materialized |
| anchorpath_w80_cap150 | cap-corrected AnchorPath-BiGRU path-fusion branch | 3 | 150 | 80 | 18.6666 | 0.2067 | 6981.54 | materialized |
| anchorpath_w160_cap150_seed42_smoke | long-window path-fusion smoke | 1 | 150 | 160 | 18.8517 | 0.0000 | 7017.04 | materialized |

## Deltas

- cap150_vs_cap125_gru_rmse_reduction: 2.3194
- w160_vs_w80_cap150_gru_rmse_reduction: 0.3747
- anchorpath_w80_cap150_minus_gru_w80_cap150_rmse: 0.2301
- anchorpath_w160_cap150_seed42_minus_gru_w160_cap150_seed42_rmse: 1.2677

## Pseudo-Terminal Validation

- Status: `pseudo_truncation_validation_complete_with_score_tradeoff`
- Selected by pseudo validation: `gru_w160_cap150`
- Best by official test RMSE: `gru_w160_cap150`
- Official PHM-score trade-off: `408.20` (gru_w160_cap150 vs gru_w80_cap150)

## Gates

| Gate | Status |
|---|---|
| cap150_improves_w80_gru | pass |
| long_window_improves_cap150_gru | pass |
| pseudo_terminal_rmse_selection_supports_long_window | pass |
| path_fusion_admitted_for_cmapss | closed |
| long_window_path_smoke_admitted | closed |

## Recommendation

Use C-MAPSS as original-task RUL transfer evidence with a long-window temporal anchor. Do not claim C-MAPSS path-fusion gain unless a future validation-admitted path branch improves this anchor.

## Next Actions

- Use the pseudo-terminal validation audit when reporting C-MAPSS cap/window selection, and disclose the PHM-score trade-off.
- Promote w160/cap150 GRU or an equivalent temporal anchor as the C-MAPSS local matched anchor for RMSE-oriented claims.
- Redesign RUL path fusion as a challenger: deploy it only when the same pseudo-terminal panel improves RMSE and passes a predeclared score trade-off rule.
