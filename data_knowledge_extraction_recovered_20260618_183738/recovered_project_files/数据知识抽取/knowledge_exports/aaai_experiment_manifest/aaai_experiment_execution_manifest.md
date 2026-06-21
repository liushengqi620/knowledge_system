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
| temporal sequence | TCN | materialized_matched_protocol | matched_preprocessing, same_seeds, same_metric | `python Scripts/public_benchmark_experiment.py --dataset TEP --model "TCN" --seed 42 --protocol matched --validation-only-thresholds` |
| temporal sequence | GRU | materialized_matched_protocol | matched_preprocessing, same_seeds, same_metric | `python Scripts/public_benchmark_experiment.py --dataset TEP --model "GRU" --seed 42 --protocol matched --validation-only-thresholds` |
| temporal sequence | FT-Transformer | materialized_matched_protocol | matched_preprocessing, same_seeds, same_metric | `python Scripts/public_benchmark_experiment.py --dataset TEP --model "FT-Transformer" --seed 42 --protocol matched --validation-only-thresholds` |
| temporal sequence | PatchTST | pending_external_alignment | protocol_alignment_required, same_seeds, no_test_threshold_tuning | `python Scripts/public_benchmark_experiment.py --dataset TEP --model "PatchTST" --seed 42 --protocol matched --validation-only-thresholds` |
| temporal sequence | Anomaly Transformer | pending_external_alignment | protocol_alignment_required, same_seeds, threshold_policy_match | `python Scripts/public_benchmark_experiment.py --dataset SKAB --model "Anomaly Transformer" --seed 42 --protocol matched --validation-only-thresholds` |
| temporal sequence | TranAD | materialized_style_baseline | matched_windowing, same_metric, external_style_not_official_leaderboard | `python Scripts/public_benchmark_experiment.py --dataset SKAB --model "TranAD" --seed 42 --protocol matched --validation-only-thresholds` |
| graph temporal | GDN | materialized_style_baseline | matched_windowing, same_metric, external_style_not_official_leaderboard | `python Scripts/public_benchmark_experiment.py --dataset SKAB --model "GDN" --seed 42 --protocol matched --validation-only-thresholds` |
| graph temporal | MTAD-GAT | materialized_style_baseline | matched_windowing, same_metric, external_style_not_official_leaderboard | `python Scripts/public_benchmark_experiment.py --dataset SKAB --model "MTAD-GAT" --seed 42 --protocol matched --validation-only-thresholds` |
| graph temporal | Graph WaveNet | pending_external_alignment | protocol_alignment_required, same_seeds, graph_input_contract | `python Scripts/public_benchmark_experiment.py --dataset TEP --model "Graph WaveNet" --seed 42 --protocol matched --validation-only-thresholds` |

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
- Forbidden until complete: official universal leaderboard superiority.
- Rule: Pending items are not completed result claims.
