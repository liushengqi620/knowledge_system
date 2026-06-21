# AAAI Experiment Execution Manifest

This manifest turns the remaining paper claims into executable, auditable obligations. Pending items are not completed result claims.

## Global Rule

- Seeds: 42, 43, 44
- tau_R grid: [0.55, 0.6, 0.65, 0.7]
- tau_q grid: [0.5, 0.6, 0.7]
- No test-set threshold or route tuning.
- Same reliability equation across datasets.

## Dataset Protocols

| Dataset | Role | Split | Primary metric |
|---|---|---|---|
| TEP | main strict multiclass benchmark | fault-run-aware train/validation/test split; no window overlap across split boundaries | Target-F1 over 22 classes |
| SKAB | binary anomaly reliability stress test | time-series split by scenario/run with changepoint leakage blocked | Macro-F1 with FAR/MAR safety diagnostics |
| Hydraulic | non-degradation safety evidence | cycle-level split following target-specific operating states | per-target F1 and non-degradation count |
| C-MAPSS | original RUL generalization evidence | FD001-FD004 train/test protocol with validation carved from training units | RUL RMSE, RUL MAE, and PHM-style RUL score |

## Baseline Obligations

| Family | Method | Status | Checks | Command template |
|---|---|---|---|---|
| temporal sequence | TCN | materialized_matched_protocol | matched_preprocessing, same_seeds, same_metric | `python Scripts/protocol_aligned_external_baseline_runner.py --dataset TEP --model "TCN" --seed 42 --protocol matched --validation-only-thresholds --budget-status local_matched_adapter_probe` |
| temporal sequence | GRU | materialized_matched_protocol | matched_preprocessing, same_seeds, same_metric | `python Scripts/protocol_aligned_external_baseline_runner.py --dataset TEP --model "GRU" --seed 42 --protocol matched --validation-only-thresholds --budget-status local_matched_adapter_probe` |
| temporal sequence | FT-Transformer | materialized_matched_protocol | matched_preprocessing, same_seeds, same_metric | `python Scripts/protocol_aligned_external_baseline_runner.py --dataset TEP --model "FT-Transformer" --seed 42 --protocol matched --validation-only-thresholds --budget-status local_matched_adapter_probe` |
| temporal sequence | PatchTST | materialized_official_source_adapted_control | official_source_checkout_verified, same_seeds, validation_only_model_selection, official_external_score_false, no_public_leaderboard_claim | `python Scripts/run_patchtst_tep_official_wrapper.py --seeds 42,43,44 --max-rows 20000 --window-size 32 --epochs 10 --device auto` |
| temporal sequence | Anomaly Transformer | materialized_official_source_adapted_control | official_source_checkout_verified, same_seeds, validation_only_threshold, point_adjustment_disabled, official_external_score_false, no_public_leaderboard_claim | `python Scripts/run_anomaly_transformer_skab_official_wrapper.py --adapter-root knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_adapter --checkout C:\Users\CPILAB\aaai_external_baseline_checkouts\anomaly_transformer --seeds 42,43,44 --epochs 5` |
| temporal sequence | TranAD | materialized_style_baseline | matched_windowing, same_metric, external_style_not_official_leaderboard | `python Scripts/protocol_aligned_external_baseline_runner.py --dataset SKAB --model "TranAD" --seed 42 --protocol matched --validation-only-thresholds --budget-status local_matched_adapter_probe` |
| graph temporal | GDN | materialized_style_baseline | matched_windowing, same_metric, external_style_not_official_leaderboard | `python Scripts/protocol_aligned_external_baseline_runner.py --dataset SKAB --model "GDN" --seed 42 --protocol matched --validation-only-thresholds --budget-status local_matched_adapter_probe` |
| graph temporal | MTAD-GAT | materialized_style_baseline | matched_windowing, same_metric, external_style_not_official_leaderboard | `python Scripts/protocol_aligned_external_baseline_runner.py --dataset SKAB --model "MTAD-GAT" --seed 42 --protocol matched --validation-only-thresholds --budget-status local_matched_adapter_probe` |
| graph temporal | Graph WaveNet | materialized_official_source_adapted_control | official_source_checkout_verified, same_seeds, graph_input_contract_declared, validation_only_model_selection, official_external_score_false, no_public_leaderboard_claim | `python Scripts/run_graph_wavenet_tep_official_wrapper.py --seeds 42,43,44 --max-rows 20000 --window-size 32 --epochs 10 --device auto` |
| RUL tabular-sequence summary | C-MAPSS Ridge/HistGB/ExtraTrees | materialized_matched_protocol | terminal_test_unit_rul, same_seeds, same_ready_data, fd001_fd004_subset_metrics | `python Scripts/run_cmapss_rul_baselines.py --seeds 42,43,44 --use-regime-prototype-residuals --window-size 80` |
| RUL temporal sequence | C-MAPSS GRU/TCN RUL | materialized_matched_protocol | terminal_test_unit_rul, same_seeds, same_ready_data, deep_sequence_runner_materialized | `python Scripts/run_cmapss_rul_baselines.py --baselines gru_sequence,tcn_sequence --seeds 42,43,44 --use-regime-prototype-residuals --window-size 80 --device cuda` |

## Reliability/Gating Controls

| Method | Optimization | Required controls | Purpose |
|---|---|---|---|
| ordinary gate | end-to-end prediction loss | none | tests whether a learned soft gate is enough |
| attention gate | attention-weighted challenger fusion | none | tests whether edge or token attention explains the gain |
| validation-only gate | mean validation gain | G_k | tests whether mean validation gain is sufficient without harm and perturbation evidence |
| complete reliability admission | global admission plus local ERE routing | G_k, H_k, C_k, S_k, B_k | target method; deployment risk control before bounded correction |

## Systematic Ablation Plan

| Variant | Intervention |
|---|---|
| Anchor only | remove all challengers and reliability correction |
| Unfiltered evidence | use all generated evidence without reliability admission |
| Expert only | keep expert mechanism evidence; remove LLM/statistical sources |
| LLM only | keep LLM-generated weak-class rules; remove expert/statistical sources |
| Lag/residual only | keep lag and residual triggers; remove expert/LLM graph evidence |
| Graph only | keep graph path evidence; remove residual and source reliability channels |
| No counterfactual guard | remove C_k perturbation-dependence admission |
| No tail safety | remove H_k low-tail harm control |
| No complexity penalty | remove B_k path/source burden |
| Full model | use all source, safety, perturbation, and routing terms |

## Claim Boundary

- Positive claim: matched-protocol method evidence.
- Forbidden until complete: official all-benchmark leaderboard dominance.
- Rule: Official-source adapted controls are completed matched-protocol controls, not official external leaderboard scores.
