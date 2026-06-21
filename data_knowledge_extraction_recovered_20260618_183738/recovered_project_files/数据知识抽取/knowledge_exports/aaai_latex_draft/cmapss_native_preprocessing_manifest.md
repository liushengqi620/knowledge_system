# C-MAPSS Native Preprocessing Manifest

- Version: cmapss-native-preprocessing-manifest-v1
- Status: `native_preprocessing_manifest_complete`
- Claim boundary: This manifest verifies the current C-MAPSS native preprocessing evidence. It does not authorize literature-wide SOTA wording until published-compatible baselines are reproduced and matched budget is aligned.
- Expected subsets: FD001, FD002, FD003, FD004

## Gate Status

| Gate | Status |
|---|---|
| native_fd001_fd004_split_present | pass |
| terminal_test_unit_records_present | pass |
| rul_cap_declared | pass |
| subset_rmse_score_present | pass |
| primary_task_is_continuous_rul | pass |
| train_only_preprocessing_declared | pass |
| published_baseline_alignment_present | pass |

## Branch Summary

| Branch | Seeds | RUL cap | Windows | Subsets | RMSE | Score | Records/seed min |
|---|---:|---|---|---|---:|---:|---:|
| cmapss_original_rul_terminal_anchor_w48_e20 | 3 | 125.0 | 48 | FD001, FD002, FD003, FD004 | 31.2554 | 41469.99 | 707 |
| cmapss_rul_anchorpath_bigru_cls020_cap150_w80_e20 | 3 | 150.0 | 80 | FD001, FD002, FD003, FD004 | 18.6666 | 6981.54 | 707 |
| cmapss_rul_anchorpath_bigru_cls020_w80_e20 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 20.4792 | 7185.62 | 707 |
| cmapss_rul_direct_regime_bitempmix_w80_e20 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 21.6882 | 8816.97 | 707 |
| cmapss_rul_direct_regime_tempmix_w80_e20 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 23.8395 | 12964.15 | 707 |
| gru_sequence_w80_cap125 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 20.7559 | 7531.00 | 707 |
| gru_sequence_w80_cap150 | 3 | 150.0 | 80 | FD001, FD002, FD003, FD004 | 18.4365 | 6428.78 | 707 |
| gru_sequence_w160_cap150 | 3 | 150.0 | 160 | FD001, FD002, FD003, FD004 | 18.0617 | 6525.46 | 707 |
| lstm_sequence | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 21.6521 | 9679.97 | 707 |
| tcn_sequence_w80_cap125 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 25.8894 | 19477.53 | 707 |
| tcn_sequence_w80_cap150 | 3 | 150.0 | 80 | FD001, FD002, FD003, FD004 | 25.6942 | 25817.31 | 707 |

## Next Actions

- Use the published-baseline alignment table to select exact baselines for reproduction.
- Archive the exact preprocessing configuration: selected sensors, scaler fit scope, RUL cap, regime prototype fit scope, and validation unit split.
- Use subset-specific FD001-FD004 RMSE and RUL score as the primary C-MAPSS table; pooled metrics remain secondary.
