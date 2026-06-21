# C-MAPSS MDFA Strategy Probe Audit

- Version: cmapss-mdfa-strategy-probe-audit-v1
- Status: `full_branch_archive_materialized_reproduction_pending`
- Claim boundary: These rows are seed-42 strategy-selection and source-fidelity diagnostics. FD001 probes calibrate the single-condition route, and FD002 probes show that multi-condition C-MAPSS requires condition-aware preprocessing. They justify the next full-budget route. The current four-subset local branch archive is source-matched candidate evidence, not a published MDFA reproduction or C-MAPSS SOTA proof. Capped-test and raw-test RUL metrics are both audited because the source-style cap policy is not yet exact-native.

## Gate Status

| Gate | Status |
|---|---|
| all_probe_summaries_present | pass |
| source2d_full_fd001_present | pass |
| fd001_long_window_full_present | pass |
| fd002_multicondition_failure_observed | pass |
| fd002_condition_aware_full_present | pass |
| fd003_short_window_failure_observed | pass |
| fd003_trajectory_cluster_negative_observed | pass |
| fd003_long_window_full_present | pass |
| fd004_condition_aware_full_present | pass |
| fd001_fd003_low_dropout_archive_present | pass |
| fd003_zero_dropout_full_archive_present | pass |
| dropout_sensitivity_probe_present | pass |
| batch_sensitivity_probe_present | pass |
| table4_key_sensor_probe_present | pass |
| pca_threshold_sensitivity_probe_present | pass |
| native_raw_rul_probe_present | pass |
| validation_output_calibration_probe_present | pass |
| validation_snapshot_ensemble_probe_present | pass |
| temporal_velocity_feature_probe_present | pass |
| feature_policy_probe_complete | pass |
| best_full_candidate_identified | pass |
| full_fd001_fd004_three_seed_archive_present | pass |
| safe_to_promote_strategy_to_published_reproduction | missing |

## Probe Rows

| Name | Subset | Role | Window | Epochs | Conv | Temporal mode | Feature policy | PCA/Input dim | Condition policy | Scheduler | Output calibration | Snapshot ensemble | Val frac | Capped RMSE | Capped Score | Raw RMSE | Raw Score | Gap to MDFA |
|---|---|---|---:|---:|---|---|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|
| legacy_temporal_1d_full_fd001 | FD001 | legacy_pre_source2d_calibration | 30 | 100 | temporal_1d | level | legacy_or_unknown | 12/12 | none | none | none | none | 0.2 | 18.3852 | 1125.32 | - | - | 6.6052 |
| source2d_all24_pca_full_fd001 | FD001 | current_full_budget_candidate | 30 | 100 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 14.1324 | 523.35 | 15.3531 | 559.42 | 2.3524 |
| source2d_all24_pca_full_fd002_failed_multicondition | FD002 | multicondition_failure_diagnostic | 30 | 100 | source_2d | level | all24_pca | 2/2 | none | none | none | none | 0.2 | 40.2631 | 116884.78 | 49.6597 | 148979.71 | 23.8831 |
| source2d_all24_pca_window80_fd001_full | FD001 | single_condition_long_window_candidate | 80 | 100 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 12.6122 | 242.46 | 13.7530 | 270.39 | 0.8322 |
| source2d_all24_pca_window80_dropout01_fd001_probe25 | FD001 | single_condition_low_dropout_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 12.4054 | 248.22 | 13.5614 | 275.47 | 0.6254 |
| source2d_all24_pca_window80_dropout01_fd001_full | FD001 | single_condition_long_window_candidate | 80 | 100 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 12.4170 | 248.70 | 13.5734 | 276.00 | 0.6370 |
| source2d_all24_pca_window30_fd003_failure | FD003 | two_fault_mode_short_window_failure_diagnostic | 30 | 100 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 17.5203 | 1565.51 | 18.4754 | 1597.48 | 5.6303 |
| source2d_common_sensors_pca_kmeans4_trajectory_fd003_negative | FD003 | two_fault_mode_trajectory_cluster_negative | 30 | 25 | source_2d | level | common_sensors_pca | 13/13 | kmeans4_trajectory+onehot | none | none | none | 0.2 | 33.8245 | 10442.07 | 34.3774 | 10509.85 | 21.9345 |
| source2d_common_sensors_pca_window80_fd003_full | FD003 | two_fault_mode_long_window_candidate | 80 | 100 | source_2d | level | common_sensors_pca | 7/7 | none | none | none | none | 0.2 | 13.8741 | 768.68 | 15.1552 | 803.29 | 1.9841 |
| source2d_all24_pca_window80_fd003_full | FD003 | two_fault_mode_long_window_candidate | 80 | 100 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 13.7865 | 456.30 | 15.2485 | 497.54 | 1.8965 |
| source2d_all24_pca_window80_dropout01_fd003_probe25 | FD003 | two_fault_mode_low_dropout_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 12.9973 | 382.00 | 14.3421 | 416.16 | 1.1073 |
| source2d_all24_pca_window80_dropout01_fd003_full | FD003 | two_fault_mode_long_window_candidate | 80 | 100 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 13.0125 | 390.13 | 14.3896 | 425.59 | 1.1225 |
| source2d_all24_pca_window80_dropout005_fd001_probe25 | FD001 | single_condition_dropout_sensitivity_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 12.4668 | 253.46 | 13.5974 | 279.97 | 0.6868 |
| source2d_all24_pca_window80_dropout005_fd003_probe25 | FD003 | two_fault_mode_dropout_sensitivity_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 12.8930 | 389.23 | 14.2540 | 423.83 | 1.0030 |
| source2d_all24_pca_window80_dropout000_fd001_probe25 | FD001 | single_condition_dropout_sensitivity_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 12.3557 | 254.58 | 13.4716 | 280.42 | 0.5757 |
| source2d_all24_pca_window80_dropout000_fd003_probe25 | FD003 | two_fault_mode_dropout_sensitivity_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 12.6412 | 312.61 | 14.0016 | 346.10 | 0.7512 |
| source2d_all24_pca_window80_dropout01_batch64_fd001_probe25 | FD001 | single_condition_batch_sensitivity_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 12.3329 | 226.86 | 13.5886 | 257.65 | 0.5529 |
| source2d_all24_pca_window80_dropout01_batch64_fd003_probe25 | FD003 | two_fault_mode_batch_sensitivity_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 13.3265 | 422.24 | 14.6725 | 457.32 | 1.4365 |
| source2d_all24_pca_window80_dropout000_fd001_full | FD001 | single_condition_zero_dropout_full_challenger | 80 | 100 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 12.3546 | 254.19 | 13.4720 | 280.07 | 0.5746 |
| source2d_all24_pca_window80_dropout000_fd003_full | FD003 | two_fault_mode_long_window_candidate | 80 | 100 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 12.6672 | 315.81 | 14.0238 | 349.29 | 0.7772 |
| source2d_all24_pca_window80_dropout01_leveldiff_fd001_probe25 | FD001 | temporal_velocity_probe_25epoch | 80 | 25 | source_2d | level_diff | all24_pca | 12/24 | none | none | none | none | 0.2 | 13.2581 | 266.89 | 14.4836 | 301.13 | 1.4781 |
| source2d_all24_pca_window80_dropout000_leveldiff_fd003_probe25 | FD003 | temporal_velocity_probe_25epoch | 80 | 25 | source_2d | level_diff | all24_pca | 10/20 | none | none | none | none | 0.2 | 12.3166 | 279.10 | 13.6278 | 310.09 | 0.4266 |
| source2d_all24_pca_window80_dropout000_leveldiff_fd003_full | FD003 | two_fault_mode_long_window_candidate | 80 | 100 | source_2d | level_diff | all24_pca | 10/20 | none | none | none | none | 0.2 | 12.9032 | 302.91 | 14.1125 | 332.46 | 1.0132 |
| source2d_sensor21_pca_kmeans_onehot_fd002_probe25 | FD002 | multicondition_condition_probe_25epoch | 30 | 25 | source_2d | level | sensor21_pca | 18/18 | kmeans6_settings+onehot | none | none | none | 0.2 | 17.4615 | 1847.49 | 29.5888 | 13905.08 | 1.0815 |
| source2d_sensor21_pca_kmeans_onehot_fd002_full | FD002 | multicondition_full_budget_candidate | 30 | 100 | source_2d | level | sensor21_pca | 18/18 | kmeans6_settings+onehot | none | none | none | 0.2 | 16.1301 | 1567.50 | 27.9509 | 11783.67 | -0.2499 |
| source2d_sensor21_pca_kmeans_onehot_fd004_probe25 | FD004 | multicondition_condition_probe_25epoch | 30 | 25 | source_2d | level | sensor21_pca | 17/17 | kmeans6_settings+onehot | none | none | none | 0.2 | 17.3559 | 2726.82 | 28.4424 | 7300.69 | -1.8741 |
| source2d_sensor21_pca_kmeans_onehot_fd004_full | FD004 | multicondition_full_budget_candidate | 30 | 100 | source_2d | level | sensor21_pca | 17/17 | kmeans6_settings+onehot | none | none | none | 0.2 | 15.9818 | 1857.96 | 27.1902 | 6023.96 | -3.2482 |
| source2d_settings_common_sensors_pca_full_fd001 | FD001 | feature_policy_full_budget_candidate | 30 | 100 | source_2d | level | settings_common_sensors_pca | 11/11 | none | none | none | none | 0.2 | 14.1993 | 581.81 | 15.3275 | 612.02 | 2.4193 |
| source2d_all24_pca_probe25 | FD001 | feature_policy_probe_25epoch | 30 | 25 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 14.8720 | 637.59 | 15.8685 | 665.10 | 3.0920 |
| source2d_all24_pca_pca090_fd001_probe25 | FD001 | pca_threshold_probe_25epoch | 30 | 25 | source_2d | level | all24_pca | 9/9 | none | none | none | none | 0.2 | 15.0374 | 645.35 | 16.1249 | 678.03 | 3.2574 |
| source2d_all24_pca_pca090_fd002_probe25 | FD002 | pca_threshold_probe_25epoch | 30 | 25 | source_2d | level | all24_pca | 2/2 | none | none | none | none | 0.2 | 40.2631 | 116884.78 | 49.6597 | 148979.71 | 23.8831 |
| source2d_all24_pca_pca090_fd003_probe25 | FD003 | pca_threshold_probe_25epoch | 30 | 25 | source_2d | level | all24_pca | 7/7 | none | none | none | none | 0.2 | 17.7956 | 1758.33 | 18.7966 | 1792.64 | 5.9056 |
| source2d_all24_pca_pca090_fd004_probe25 | FD004 | pca_threshold_probe_25epoch | 30 | 25 | source_2d | level | all24_pca | 2/2 | none | none | none | none | 0.2 | 38.6818 | 355169.12 | 47.8342 | 373377.29 | 19.4518 |
| source2d_all24_pca_cap150_raw_fd001_probe25 | FD001 | native_raw_rul_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.2 | 17.8423 | 900.09 | 17.8423 | 900.09 | 6.0623 |
| source2d_all24_pca_cap150_raw_fd003_probe25 | FD003 | native_raw_rul_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 10/10 | none | none | none | none | 0.2 | 17.4350 | 1093.00 | 17.4350 | 1093.00 | 5.5450 |
| source2d_sensor21_pca_kmeans_onehot_cap150_raw_fd002_probe25 | FD002 | native_raw_rul_probe_25epoch | 30 | 25 | source_2d | level | sensor21_pca | 18/18 | kmeans6_settings+onehot | none | none | none | 0.2 | 26.8362 | 9852.94 | 26.8362 | 9852.94 | 10.4562 |
| source2d_sensor21_pca_kmeans_onehot_cap150_raw_fd004_probe25 | FD004 | native_raw_rul_probe_25epoch | 30 | 25 | source_2d | level | sensor21_pca | 17/17 | kmeans6_settings+onehot | none | none | none | 0.2 | 25.9469 | 7986.14 | 25.9469 | 7986.14 | 6.7169 |
| source2d_mdfa_key_sensors_pca_fd001_probe25 | FD001 | table4_key_sensor_probe_25epoch | 30 | 25 | source_2d | level | mdfa_key_sensors_pca | 7/7 | none | none | none | none | 0.2 | 15.7251 | 622.46 | 16.8014 | 655.85 | 3.9451 |
| source2d_mdfa_key_sensors_pca_fd002_probe25 | FD002 | table4_key_sensor_probe_25epoch | 30 | 25 | source_2d | level | mdfa_key_sensors_pca | 2/2 | none | none | none | none | 0.2 | 26.4954 | 10641.34 | 36.9273 | 46227.19 | 10.1154 |
| source2d_mdfa_key_sensors_pca_fd003_probe25 | FD003 | table4_key_sensor_probe_25epoch | 30 | 25 | source_2d | level | mdfa_key_sensors_pca | 6/6 | none | none | none | none | 0.2 | 18.4466 | 1564.66 | 19.3909 | 1597.71 | 6.5566 |
| source2d_mdfa_key_sensors_pca_fd004_probe25 | FD004 | table4_key_sensor_probe_25epoch | 30 | 25 | source_2d | level | mdfa_key_sensors_pca | 2/2 | none | none | none | none | 0.2 | 31.4487 | 35089.20 | 40.1256 | 44797.05 | 12.2187 |
| source2d_sensor21_pca_probe25 | FD001 | feature_policy_probe_25epoch | 30 | 25 | source_2d | level | sensor21_pca | 10/10 | none | none | none | none | 0.2 | 14.9545 | 665.93 | 16.0003 | 695.53 | 3.1745 |
| source2d_common_sensors_raw_probe25 | FD001 | feature_policy_probe_25epoch | 30 | 25 | source_2d | level | common_sensors_raw | 14/14 | none | none | none | none | 0.2 | 15.8935 | 700.83 | 17.1949 | 749.98 | 4.1135 |
| source2d_common_sensors_pca_probe25 | FD001 | feature_policy_probe_25epoch | 30 | 25 | source_2d | level | common_sensors_pca | 10/10 | none | none | none | none | 0.2 | 14.8466 | 609.70 | 15.9755 | 641.55 | 3.0666 |
| source2d_settings_common_sensors_raw_probe25 | FD001 | feature_policy_probe_25epoch | 30 | 25 | source_2d | level | settings_common_sensors_raw | 17/17 | none | none | none | none | 0.2 | 16.4463 | 851.52 | 17.6146 | 893.05 | 4.6663 |
| source2d_settings_common_sensors_pca_probe25 | FD001 | feature_policy_probe_25epoch | 30 | 25 | source_2d | level | settings_common_sensors_pca | 11/11 | none | none | none | none | 0.2 | 14.2063 | 582.56 | 15.3360 | 612.87 | 2.4263 |
| source2d_reduce_on_plateau_probe25 | FD001 | lr_scheduler_probe_25epoch | 30 | 25 | source_2d | level | all24_pca | 12/12 | none | reduce_on_plateau | none | none | 0.2 | 14.8715 | 637.88 | 15.8685 | 665.43 | 3.0915 |
| source2d_val0_probe25 | FD001 | validation_split_probe_25epoch | 30 | 25 | source_2d | level | all24_pca | 12/12 | none | none | none | none | 0.0 | 15.2640 | 715.28 | 16.2483 | 743.20 | 3.4840 |
| source2d_all24_pca_window80_dropout000_affine_cal_fd001_probe25 | FD001 | validation_output_calibration_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 12/12 | none | none | affine_val:blocked | none | 0.2 | 12.3489 | 253.57 | 13.4685 | 279.50 | 0.5689 |
| source2d_all24_pca_window80_dropout000_affine_cal_fd003_probe25 | FD003 | validation_output_calibration_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 10/10 | none | none | affine_val:blocked | none | 0.2 | 12.6409 | 312.42 | 14.0015 | 345.92 | 0.7509 |
| source2d_all24_pca_window80_dropout01_snapshot_fd001_probe25 | FD001 | validation_snapshot_ensemble_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 12/12 | none | none | none | k5:blocked | 0.2 | 12.4111 | 248.77 | 13.5680 | 276.07 | 0.6311 |
| source2d_all24_pca_window80_dropout000_snapshot_fd003_probe25 | FD003 | validation_snapshot_ensemble_probe_25epoch | 80 | 25 | source_2d | level | all24_pca | 10/10 | none | none | none | k5:blocked | 0.2 | 12.6454 | 313.49 | 14.0053 | 347.00 | 0.7554 |

## Full Archive Stats

| Archive | Complete | Records | Subset | Seeds | Capped RMSE mean | RMSE range | Capped Score mean | Raw RMSE mean | Raw Score mean |
|---|---|---:|---|---|---:|---|---:|---:|---:|
| Previous single-condition archive | True | 600 | FD001 | 42,43,44 | 13.0791 | 12.6137-13.4483 | 263.84 | 14.2102 | 297.23 |
| Previous single-condition archive | True | 600 | FD003 | 42,43,44 | 15.1020 | 13.7867-16.5620 | 733.31 | 16.2969 | 768.33 |
| Selected single-condition archive | True | 600 | FD001 | 42,43,44 | 12.5498 | 12.3401-12.8923 | 245.48 | 13.6994 | 273.73 |
| Selected single-condition archive | True | 600 | FD003 | 42,43,44 | 13.5869 | 13.0125-14.4078 | 473.89 | 14.8428 | 507.03 |
| Zero-dropout single-condition challenger | True | 600 | FD001 | 42,43,44 | 12.8970 | 12.3546-13.9227 | 250.11 | 14.0829 | 280.66 |
| Zero-dropout single-condition challenger | True | 600 | FD003 | 42,43,44 | 12.9684 | 12.6672-13.2160 | 335.61 | 14.3039 | 369.79 |
| Temporal level+diff FD003 challenger | True | 300 | FD003 | 42,43,44 | 12.9260 | 12.7379-13.1370 | 330.19 | 14.1774 | 361.69 |
| Multi-condition archive | True | 1521 | FD002 | 42,43,44 | 15.8410 | 15.5398-15.9937 | 1366.25 | 27.9247 | 10307.49 |
| Multi-condition archive | True | 1521 | FD004 | 42,43,44 | 15.9596 | 15.5689-16.2751 | 2141.43 | 27.4298 | 7992.75 |

## Decision

- Current FD001 full candidate: `source2d_all24_pca_window80_dropout01_fd001_full`
- Feature policy: `all24_pca`
- Conv formulation: `source_2d`
- Current FD003 two-fault candidate: `source2d_all24_pca_window80_dropout000_leveldiff_fd003_full`
- FD003 window size: `80`
- FD003 temporal mode: `level_diff`
- FD003 three-seed RMSE: `12.926042071119616`
- Current FD002 multi-condition candidate: `source2d_sensor21_pca_kmeans_onehot_fd002_full`
- FD002 condition policy: `kmeans6_settings`
- Current FD004 multi-condition candidate: `source2d_sensor21_pca_kmeans_onehot_fd004_full`
- FD004 condition policy: `kmeans6_settings`
- Rationale: Use source_2d/all24_pca as the single-condition branch, with window80 and lower dropout selected by FD001/FD003 validation probes to stabilize the two-fault FD003 subset. Do not extend this policy blindly to every subset: the FD002 failure diagnostic shows all24_pca collapses multi-condition structure, while sensor21_pca with kmeans6 setting normalization and condition one-hot materially improves the multi-condition route. A Table-4 key-sensor probe is retained as source-aligned negative control because the key-sensor PCA branch collapses multi-condition subsets. The PCA=0.90 sensitivity probe is also retained as negative evidence: lowering the cumulative-contribution threshold compresses multi-condition subsets too aggressively and does not repair the source-matched route. The zero-dropout challenger improves the FD003 two-fault subset but is not promoted to FD001 because seed-level stability regresses there. A cap150/raw-test probe is retained as a native-label negative control because it does not close the public raw-test C-MAPSS gap. Validation-only affine output calibration and checkpoint snapshot-ensemble probes are retained as guarded negative results because their validation RMSE gains stay below the admission threshold, so post-hoc output calibration and checkpoint averaging are not treated as admitted path-fusion improvements. A level+first-difference temporal-channel probe is subset-conditional: it regresses FD001, but its full three-seed FD003 challenger gives a small stable improvement over the level-only zero-dropout FD003 branch. The selected full archive therefore freezes a stable low-dropout FD001 branch, a level+first-difference FD003 two-fault branch, and a condition-aware branch for FD002/FD004 under the source-style capped-test claim boundary.

## Next Actions

- Verify whether the low-dropout single-condition branch remains source-compatible with the MDFA protocol or must be reported as an improved local candidate.
- Treat the source PCA cumulative-contribution threshold and exact test-label scoring policy as non-machine-readable until the original authors or supplementary code specify them.
- Compare the completed local branch archive against exact MDFA Table 5 only after PCA/key-sensor policy is verified.
- Keep the local branch archive out of official SOTA tables until exact-source preprocessing and budget equivalence are verified.
