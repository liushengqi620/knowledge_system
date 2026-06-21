# SKAB Official Repository Baseline Audit

- Version: skab-official-repository-baseline-audit-v1
- Status: official_skab_precomputed_baseline_audit_partial
- Claim boundary: This audit recomputes SKAB official outlier leaderboard rows from official repository result pickles and materializes frozen prediction records. It does not prove that notebooks were rerun from source.
- Notebook count: 10
- Core module count: 11
- Result pickle count: 10

## Gates

| Gate | Status |
|---|---:|
| official_skab_repository_extracted | pass |
| official_notebooks_present | pass |
| official_core_modules_present | pass |
| official_result_pickles_present | pass |
| official_result_pickles_align_to_raw_data | pass |
| official_outlier_leaderboard_recomputed | pass |
| official_frozen_prediction_records_materialized | pass |
| official_notebooks_rerun_from_source | blocked |

## Official Outlier Rows

| Method | Records | F1 | FAR | MAR | README match | Frozen record file |
|---|---:|---:|---:|---:|---:|---|
| Arima_anomaly_detection | 23801 | 0.0000 | 0.01 | 100.00 | n/a | `skab_official_repository_baseline_records\Arima_anomaly_detection.jsonl` |
| Conv_AE | 23801 | 0.7838 | 13.55 | 28.02 | yes | `skab_official_repository_baseline_records\Conv_AE.jsonl` |
| Isolation_Forest | 23801 | 0.2868 | 2.56 | 82.89 | yes | `skab_official_repository_baseline_records\Isolation_Forest.jsonl` |
| LSTM_AE | 23801 | 0.7410 | 29.96 | 25.92 | yes | `skab_official_repository_baseline_records\LSTM_AE.jsonl` |
| MSCRED | 22475 | 0.3567 | 49.72 | 70.04 | yes | `skab_official_repository_baseline_records\MSCRED.jsonl` |
| MSET | 23801 | 0.7800 | 39.73 | 14.13 | yes | `skab_official_repository_baseline_records\MSET.jsonl` |
| T2-q | 23801 | 0.7581 | 26.62 | 24.92 | yes | `skab_official_repository_baseline_records\T2-q.jsonl` |
| T2 | 23801 | 0.6598 | 19.21 | 42.60 | yes | `skab_official_repository_baseline_records\T2.jsonl` |
| Vanilla_AE | 23801 | 0.3910 | 2.59 | 75.15 | yes | `skab_official_repository_baseline_records\Vanilla_AE.jsonl` |
| Vanilla_LSTM | 23631 | 0.5356 | 12.54 | 59.53 | yes | `skab_official_repository_baseline_records\Vanilla_LSTM.jsonl` |

## Next Actions

- Rerun the official notebooks or core modules in a pinned environment to close the source-rerun gate.
- Decide whether the paper compares against official precomputed SKAB leaderboard rows or the project train/validation/test split; do not mix them as one protocol.
- If using the project split, port the official notebook methods into the same split/preprocessing/budget contract and archive seed-level frozen predictions.
