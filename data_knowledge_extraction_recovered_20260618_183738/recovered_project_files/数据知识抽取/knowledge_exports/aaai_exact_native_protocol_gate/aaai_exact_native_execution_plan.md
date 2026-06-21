# AAAI Exact-Native Execution Plan

- Version: aaai-exact-native-execution-plan-v1
- Status: `execution_plan_ready_not_sota_proof`
- Claim rule: This plan is an execution contract, not evidence of official SOTA. A gate may flip only after the referenced artifacts exist and are inspected.
- Primary next datasets: SKAB, C-MAPSS

This file turns the current exact-native SOTA blocker into concrete experiment work. It must not be cited as a completed result.

## Reference Sources

| ID | Source | Protocol use |
|---|---|---|
| skab_official_repository | [SKAB official repository](https://github.com/waico/skab) | Defines SKAB v0.9 data files, anomaly/changepoint labels, proposed leaderboard framing, and notebook/core-based reproduction route. |
| nasa_cmapss_open_data | [NASA C-MAPSS open data page](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data) | Defines train/test trajectories for FD001-FD004, operational settings, sensors, and the terminal test-unit RUL prediction objective. |
| nasa_pcoe_cmapss_repository | [NASA PCoE Turbofan Engine Degradation Simulation repository entry](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/) | Used to cross-check FD001-FD004 operating-condition/fault-mode combinations and the PCoE dataset lineage. |
| tab_protocol_caveats | [Unified Benchmarking of Time Series Anomaly Detection Methods](https://arxiv.org/abs/2506.18046) | Used only as an evaluation-caveat reference for split leakage, drop-last, point adjustment, threshold choice, and inconsistent output-length issues in TSAD comparisons. |
| mdfa_2025_open_protocol | [Remaining Useful Life Prediction for Aero-Engines Based on Multi-Scale Dilated Fusion Attention Model](https://www.mdpi.com/2076-3417/15/17/9813) | Primary open full-text C-MAPSS exact-source candidate after FD004 count reconciliation; exposes FD001-FD004 scope, window, batch, epochs, optimizer, learning rate, dropout, preprocessing, and metrics. |
| acb_2021_open_protocol | [Effective Latent Representation for Prediction of Remaining Useful Life](https://www.techscience.com/csse/v36n1/40892/html) | Fallback all-subset open C-MAPSS baseline candidate; useful if MDFA count reconciliation fails, but its accessible text lacks enough budget fields for immediate exact reproduction. |

## Dataset Execution Matrix

| Dataset | Priority | Claim upgrade target | Required new/tightened assets |
|---|---|---|---|
| SKAB | P0 | from matched reliability-filtered anomaly evidence to native SKAB outlier/changepoint evidence | skab_native_metric_audit (materialized_complete_current_proposed_branches)<br>skab_official_notebook_reproduction (missing_official_repo_level; style_usad_tranad_records_materialized)<br>skab_external_style_baseline_prediction_archive (materialized_usad_tranad_w48_e8_3seed_not_official)<br>skab_threshold_policy_manifest (materialized_in_skab_native_metric_audit) |
| C-MAPSS | P0 | from original-task RUL transfer evidence to native FD001-FD004 prognostics evidence | cmapss_native_preprocessing_manifest (native_preprocessing_complete_alignment_artifact_present_not_sota_proof)<br>cmapss_published_baseline_alignment (materialized_partial_reference_registry_and_lstm_style_candidate_present_reproduction_and_budget_missing)<br>cmapss_published_baseline_contract (materialized_contract_complete_reproduction_pending)<br>cmapss_lstm_source_protocol_audit (materialized_source_protocol_incomplete_local_config_extracted)<br>cmapss_open_protocol_candidate_audit (materialized_open_candidates_identified_exact_profile_pending)<br>cmapss_mdfa_source_profile (materialized_source_profile_count_reconciled_full_budget_pending)<br>cmapss_mdfa_source_matched_runner (materialized_four_subset_three_seed_branch_archive_reproduction_pending)<br>cmapss_mdfa_runner_audit (materialized_smoke_runner_materialized_full_budget_pending)<br>cmapss_mdfa_strategy_probe_audit (materialized_full_branch_archive_reproduction_pending)<br>cmapss_lstm_published_style_candidate (materialized_3seed_fd001_fd004_terminal_records_not_exact_published_reproduction)<br>cmapss_subset_seed_prediction_archive (materialized_seed_level_for_current_branches)<br>cmapss_rul_backbone_optimization_audit (materialized_partial_long_window_anchor_positive_path_fusion_closed)<br>cmapss_pseudo_truncation_validation_audit (materialized_complete_rmse_selection_score_tradeoff_disclosed) |
| TEP | P1 | strict 22-class matched evidence to cited native FDD protocol evidence | tep_native_fdd_protocol_reproduction (missing) |
| Hydraulic | P2 | near-ceiling safety evidence to native four-target Hydraulic table | hydraulic_four_target_protocol_table (missing) |

## Detailed Contracts

### SKAB (P0)

Native protocol contract:
- Keep outlier detection and changepoint detection as separate native tasks; do not mix labels in one score.
- Use the official SKAB data layout and preserve datetime order, anomaly labels, and changepoint labels.
- For changepoint scoring, declare the right-side event window policy before running any model.
- Select thresholds only on training-derived validation data or the official notebook split; never tune on test labels.
- Report F1, FAR, and MAR for point/outlier labels; report the declared event-window score separately for changepoints.
- Disable point-adjustment unless it is the explicit native protocol being reproduced.

Reusable assets:
- `Scripts/skab_external_baselines.py`
- `Scripts/run_anomaly_transformer_skab_official_wrapper.py`
- `Scripts/run_skab_dynamic_llm_graph_experiment.py`
- `Scripts/skab_native_metric_audit.py`
- `knowledge_exports/aaai_formal_public_runs/skab_strong_anchor_w48_e40`
- `knowledge_exports/external_baseline_protocol_runs/skab_external_baselines_native_records_usad_tranad_w48_e8.json`
- `knowledge_exports/public_benchmark_ready_llm_live_skab`
- `knowledge_exports/aaai_exact_native_protocol_gate/skab_native_metric_audit.md`

Baseline protocols to run:
- official SKAB notebook/core baselines where runnable
- USAD-style reconstruction under native point labels
- TranAD-style reconstruction under native point labels
- GDN/MTAD-GAT matched graph-temporal controls with identical thresholds
- official-source Anomaly Transformer wrapper with point adjustment disabled and native output-length audit

First commands:
- `python Scripts/aaai_formal_public_protocol.py --only skab_strong_anchor --seeds 42,43,44 --device cuda --execute`
- `python Scripts/run_anomaly_transformer_skab_official_wrapper.py --seeds 42,43,44 --epochs 5`
- `python Scripts/summarize_skab_external_baselines.py`

Gate flip requirements:
- exact_public_split=true after official split/notebook policy is reproduced and recorded
- exact_preprocessing=true after train-only scaling and missing/valid mask policy match the native reproduction
- exact_metric=true after point and changepoint scores are written from frozen predictions
- official_or_published_baseline_protocol=true after official or faithful baselines have seed-level artifacts
- threshold_or_delay_policy=true after validation-only threshold and right-side changepoint event-window are frozen
- matched_budget=true after model epochs, windowing, and output length are identical across compared methods

Success evidence:
- one JSON file per seed containing scores, binary labels, thresholds, prediction length, and metric variants
- one markdown audit table comparing proposed, anchor, and official/fair baselines under the same native scores
- exact-native gate row for SKAB updated only if every listed gate is true

### C-MAPSS (P0)

Native protocol contract:
- Use the NASA train/test split and terminal test-unit RUL labels for FD001, FD002, FD003, and FD004.
- Report subset-specific RMSE and PHM-style asymmetric RUL score; pooled metrics are secondary.
- Declare the train-target RUL cap before training and include an uncapped terminal-test metric audit.
- Fit scalers, operating-regime prototypes, and any sensor selection on training units only.
- Keep derived health-stage labels auxiliary; the primary task is continuous RUL regression.
- Compare against compatible published RUL baselines only when their subset, cap, score, and preprocessing match.

Reusable assets:
- `Scripts/run_cmapss_rul_baselines.py`
- `Scripts/run_cmapss_mdfa_source_matched.py`
- `Scripts/summarize_cmapss_rul_terminal_results.py`
- `Scripts/run_public_ms_gse_rpf_experiment.py`
- `Scripts/cmapss_native_preprocessing_manifest.py`
- `Scripts/cmapss_published_baseline_alignment.py`
- `Scripts/cmapss_published_baseline_contract.py`
- `Scripts/cmapss_lstm_source_protocol_audit.py`
- `Scripts/cmapss_open_protocol_candidate_audit.py`
- `Scripts/cmapss_mdfa_source_profile.py`
- `Scripts/cmapss_mdfa_runner_audit.py`
- `Scripts/cmapss_mdfa_strategy_probe_audit.py`
- `Scripts/cmapss_rul_backbone_optimization_audit.py`
- `Scripts/cmapss_pseudo_truncation_validation_audit.py`
- `knowledge_exports/aaai_formal_public_runs/cmapss_original_rul_terminal_anchor_w48_e20`
- `knowledge_exports/aaai_formal_public_runs/cmapss_rul_anchorpath_bigru_cls020_w80_e20`
- `knowledge_exports/cmapss_rul_deep_baselines_regime_w160_cap150`
- `knowledge_exports/cmapss_lstm_published_style_w80_cap125`
- `knowledge_exports/aaai_formal_public_runs/cmapss_rul_anchorpath_bigru_cls020_cap150_w80_e20`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_native_preprocessing_manifest.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_published_baseline_alignment.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_published_baseline_contract.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_lstm_source_protocol_audit.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_open_protocol_candidate_audit.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_mdfa_source_profile.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_mdfa_runner_audit.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_mdfa_strategy_probe_audit.md`
- `knowledge_exports/cmapss_mdfa_source_matched_source2d_smoke/cmapss_mdfa_source_matched_summary.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_rul_backbone_optimization_audit.md`
- `knowledge_exports/aaai_exact_native_protocol_gate/cmapss_pseudo_truncation_validation_audit.md`

Baseline protocols to run:
- Ridge/HistGB/ExtraTrees summary baselines as transparent lower-bound controls
- GRU and TCN sequence RUL baselines under identical FD001-FD004 windows
- cap-corrected long-window temporal anchor as the current strongest local C-MAPSS RUL control
- published-compatible LSTM/attention/Transformer RUL baselines only after cap and score formula alignment
- local LSTM sequence branch as a published-style candidate until the exact LSTM paper configuration is reproduced
- MDFA 2025 open full-text profile as the first exact-source all-subset candidate after raw-file count reconciliation
- MDFA 2025 source-matched runner smoke plus completed FD001/FD003 low-dropout long-window and FD002/FD004 condition-aware branch archives as route-selection evidence only, not published-score rows
- ACB 2021 open full-text profile as fallback if MDFA cannot be reconciled
- AnchorPath-BiGRU path residual fusion only as a challenger after validation-safe admission

First commands:
- `python Scripts/run_cmapss_mdfa_source_matched.py --output-dir knowledge_exports/cmapss_mdfa_source_matched_single_condition_w80_all24_dropout01_full --subsets FD001,FD003 --seeds 42,43,44 --window-size 80 --epochs 100 --batch-size 32 --learning-rate 0.0001 --dropout 0.1 --conv-formulation source_2d --feature-policy all24_pca --device cuda --resume`
- `python Scripts/run_cmapss_mdfa_source_matched.py --output-dir knowledge_exports/cmapss_mdfa_condition_full_fd002_fd004_sensor21_pca_kmeans_onehot --subsets FD002,FD004 --seeds 42,43,44 --epochs 100 --batch-size 32 --learning-rate 0.0001 --dropout 0.3 --conv-formulation source_2d --feature-policy sensor21_pca --condition-normalization kmeans6_settings --append-condition-onehot --device cuda --resume`
- `python Scripts/cmapss_pseudo_truncation_validation_audit.py --seeds 42,43,44 --candidates gru_w80_cap125,gru_w80_cap150,gru_w160_cap150 --device cuda --epochs 25 --batch-size 256 --max-rows-per-split 12000`
- `python Scripts/run_cmapss_rul_baselines.py --output-dir knowledge_exports/cmapss_rul_deep_baselines_regime_w160_cap150 --seeds 42,43,44 --baselines gru_sequence --window-size 160 --max-rows-per-split 12000 --rul-cap 150 --use-regime-prototype-residuals --device cuda --epochs 25 --batch-size 256 --hidden-dim 64 --layers 2 --dropout 0.10`
- `python Scripts/run_cmapss_rul_baselines.py --seeds 42,43,44 --baselines ridge_summary,histgb_summary,extra_trees_summary,gru_sequence,tcn_sequence --use-regime-prototype-residuals --window-size 80 --device cuda`
- `python Scripts/run_cmapss_rul_baselines.py --output-dir knowledge_exports/cmapss_lstm_published_style_w80_cap125 --seeds 42,43,44 --baselines lstm_sequence --window-size 80 --max-rows-per-split 12000 --rul-cap 125 --use-regime-prototype-residuals --device cuda --epochs 25 --batch-size 256 --hidden-dim 64 --layers 2 --dropout 0.10`
- `python Scripts/aaai_formal_public_protocol.py --only cmapss_rul_anchorpath_bigru_cls020 --seeds 42,43,44 --device cuda --execute # challenger only; not a C-MAPSS path-fusion claim unless validation-safe admission beats the temporal anchor`
- `python Scripts/summarize_cmapss_rul_terminal_results.py`

Gate flip requirements:
- exact_preprocessing=true is satisfied by the native preprocessing manifest; published-baseline preprocessing equivalence remains part of the baseline-protocol gate
- official_or_published_baseline_protocol=true after cited baselines are aligned or explicitly excluded
- matched_budget=true after epochs, windows, seeds, and FD subset coverage are matched or normalized
- LSTM published-style candidate becomes a reproduced published baseline only after exact paper preprocessing, cap, hidden size, epochs, validation split, and subset table are matched
- cmapss_published_baseline_contract must show source-matched fields, matched budget, and prediction archives before official_or_published_baseline_protocol can flip
- cmapss_lstm_source_protocol_audit must show paper_fulltext_protocol_available and all_required_source_fields_verified before promoting the local LSTM row
- cmapss_mdfa_strategy_probe_audit must identify the selected source_2d long-window single-condition and condition-aware multi-condition routes before launching the full archive
- cmapss_mdfa_runner_audit must show full_three_seed_archive_present, full_source_budget_100epoch_present, pca_key_sensor_exact_policy_verified, and safe_to_promote_mdfa_to_exact_reproduction before promoting the open full-text candidate
- C-MAPSS path-fusion claim enabled only after pseudo-truncation validation shows RMSE gain over the same-window temporal anchor and either improves PHM score or explicitly passes a predeclared score trade-off rule

Success evidence:
- FD001-FD004 subset table with RMSE, MAE, and RUL score for every seed and branch
- terminal per-engine prediction archive with no derived-label primary metric
- exact-native gate row for C-MAPSS remains blocked only by published-baseline protocol and budget after native preprocessing evidence is complete

### TEP (P1)

Native protocol contract:
- Pick the cited TEP/FDD taxonomy before training.
- Match split, delay policy, metric, and class inclusion exactly.
- Attach strict full-model seed-level predictions before using the row as the main official claim.

Reusable assets:
- `knowledge_exports/aaai_latex_draft`
- `knowledge_exports/aaai_ablation_coverage_audit.json`

Baseline protocols to run:
- published TEP/FDD protocols selected from cited papers

First commands:
- `python Scripts/aaai_exact_native_protocol_gate.py --output-dir knowledge_exports/aaai_exact_native_protocol_gate`

Gate flip requirements:
- all TEP exact-native gates true

Success evidence:
- seed-level strict 22-class predictions and cited-protocol reproduction table

### Hydraulic (P2)

Native protocol contract:
- Use published target definitions and metrics for all four condition-monitoring targets.
- Report near-ceiling non-degradation unless a compatible temporal baseline table is reproduced.

Reusable assets:
- `knowledge_exports/aaai_latex_draft`
- `knowledge_exports/aaai_ablation_coverage_audit.json`

Baseline protocols to run:
- published Hydraulic four-target baselines
- one compatible temporal neural baseline

First commands:
- `python Scripts/aaai_exact_native_protocol_gate.py --output-dir knowledge_exports/aaai_exact_native_protocol_gate`

Gate flip requirements:
- all Hydraulic exact-native gates true

Success evidence:
- four-target table with seed-level metrics and matched published baseline rows
