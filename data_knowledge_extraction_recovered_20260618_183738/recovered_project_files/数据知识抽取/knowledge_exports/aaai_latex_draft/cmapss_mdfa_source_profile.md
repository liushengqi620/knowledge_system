# C-MAPSS MDFA Source Profile

- Version: cmapss-mdfa-source-profile-v1
- Status: `source_profile_count_reconciled_runner_pending`
- Claim boundary: MDFA 2025 is now a concrete open-source-profile target for C-MAPSS. The local raw files match the MDFA FD001-FD004 unit-count table, while the bundled readme has an FD004 count inconsistency. This profile does not prove an exact reproduction until PCA/key-sensor preprocessing, the runner, matched budget, and seed-level predictions are materialized.
- Source: [Remaining Useful Life Prediction for Aero-Engines Based on Multi-Scale Dilated Fusion Attention Model](https://www.mdpi.com/2076-3417/15/17/9813)

## Gate Status

| Gate | Status |
|---|---|
| open_fulltext_protocol_available | pass |
| mdfa_hyperparameters_extracted | pass |
| mdfa_architecture_fields_extracted | pass |
| mdfa_piecewise_rul_cap_machine_readable | pass |
| mdfa_table4_key_sensors_machine_readable | pass |
| local_raw_files_present | pass |
| local_unit_counts_match_mdfa_table | pass |
| local_rul_rows_match_test_units | pass |
| readme_counts_match_local_files | missing |
| exact_pca_preprocessing_machine_readable | missing |
| exact_test_label_policy_machine_readable | missing |
| source_matched_runner_code_present | pass |
| full_source_matched_prediction_archive_present | missing |
| safe_to_promote_mdfa_to_exact_reproduction | missing |

## Count Reconciliation

| Subset | Local train units | Local test units | RUL rows | MDFA train/test | Readme train/test | Match MDFA | Match readme |
|---|---:|---:|---:|---|---|---|---|
| FD001 | 100 | 100 | 100 | 100/100 | 100/100 | yes | yes |
| FD002 | 260 | 259 | 259 | 260/259 | 260/259 | yes | yes |
| FD003 | 100 | 100 | 100 | 100/100 | 100/100 | yes | yes |
| FD004 | 249 | 248 | 248 | 249/248 | 248/249 | yes | no |

## Table 4 Key Sensor Mapping

| Source code | Local channel | Sensor id | Description |
|---|---|---:|---|
| Ps30 | s11 | 11 | Static pressure at HPC outlet |
| T24 | s2 | 2 | Total temperature at LPC outlet |
| T30 | s3 | 3 | Total temperature at HPC outlet |
| P30 | s7 | 7 | Total pressure at HPC outlet |
| Phi | s12 | 12 | Fuel flow to high-pressure compressor static pressure ratio |
| Nf | s8 | 8 | Physical fan speed |
| Nc | s9 | 9 | Physical core speed |
| W31 | s20 | 20 | HPT coolant bleed |
| W32 | s21 | 21 | LPT coolant bleed |

## Extracted Protocol Fields

- Window/budget: window=30, batch=32, epochs=100, optimizer=Adam, lr=0.0001, dropout=0.3.
- Architecture: multi-scale dilated fusion attention with source_2d_time_feature, dilation rates 1, 2, 4, kernel=3x3, attention=channel_attention, spatial_attention.
- Metrics: RMSE, Score.

## Next Actions

- Keep the source-matched MDFA runner fixed with source_2d time-feature input, window=30, batch=32, epochs=100, Adam, lr=0.0001, dropout=0.3, and dilation rates 1/2/4.
- Treat the source PCA cumulative-contribution threshold and test-label scoring policy as non-machine-readable until the original authors or supplementary code specify the exact values.
- Retain the machine-readable Table-4 feature policy (`mdfa_key_sensors_pca`) as a source-aligned negative/control branch, not as an exact reproduction proof.
- Run exact-source three-seed FD001-FD004 terminal RUL only if the missing PCA threshold and preprocessing policy are resolved.
- Report the bundled readme FD004 train/test count inconsistency, but use the raw file unique-unit counts because they match the MDFA published table and RUL line counts.
