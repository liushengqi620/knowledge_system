# AAAI Exact-Native Protocol Gate

- Version: aaai-exact-native-protocol-gate-v1
- Overall status: official_sota_not_admissible
- Claim rule: Use matched-protocol or official-source adapted controls only until every exact-native gate is true for the target dataset.
- Safe overall claim: reliability-calibrated mechanism evidence fusion with strong matched-protocol industrial evidence
- Unsafe overall claim: universal official leaderboard SOTA across all datasets

This gate is stricter than the matched-protocol paper audit. A dataset can support official SOTA wording only when its task, split, preprocessing, metric, threshold/delay policy, budget, baseline protocol, and seed-level artifacts match the cited native benchmark protocol.

## Dataset Gate Matrix

| Dataset | Current result | Status | Missing exact-native gates | Safe current claim | Next action |
|---|---|---|---|---|---|
| TEP | Target-F1 0.9549 +/- 0.0023 | matched_only | exact_public_split, exact_preprocessing, exact_metric, official_or_published_baseline_protocol, threshold_or_delay_policy, matched_budget, seed_level_prediction_artifacts | strong strict 22-class matched-protocol mechanism-diagnosis evidence | Reproduce at least two cited TEP/FDD protocols end-to-end, including their split, preprocessing, delay handling, metric, budget, and seed-level predictions. |
| SKAB | Macro-F1 0.8450 +/- 0.0189 | matched_only | exact_public_split, exact_preprocessing, official_or_published_baseline_protocol, matched_budget | matched-protocol native-audited algorithmic anomaly evidence; LLM condition verifier retained as diagnostic evidence | Run official or faithful USAD, TranAD, GDN, MTAD-GAT, and Anomaly Transformer protocols with identical split, preprocessing, threshold, event-window, and budget rules. |
| Hydraulic | Macro-F1 0.9784 +/- 0.0301 | matched_only | exact_public_split, exact_preprocessing, exact_metric, official_or_published_baseline_protocol, matched_budget | near-ceiling non-degradation and safety evidence | Reformat to the published four-target protocol and add at least one compatible temporal neural baseline. |
| C-MAPSS | RUL RMSE 18.0617 +/- 0.3621; pseudo-terminal validation rerun RMSE 18.2840 +/- 0.1324 | matched_only | official_or_published_baseline_protocol, matched_budget | original terminal RUL transfer evidence with cap-corrected long-window temporal anchor; path fusion not admitted | Run the MDFA 2025 source-matched runner at full budget after freezing PCA/key-sensor preprocessing, then reproduce selected published RUL baselines with identical FD001-FD004 split, published-compatible preprocessing, RUL cap, score/RMSE reporting, windows, seeds, and budget before literature-wide SOTA claims. |

## Blocking Evidence

### TEP

- Native reference target: external TEP/FDD paper protocol with identical split, delay handling, class taxonomy, metric, and budget
- Strict TEP full mechanism row is still summary-level in the ablation audit.
- External TEP papers use non-identical split, delay, taxonomy, or metric conventions.

### SKAB

- Native reference target: official SKAB anomaly scoring with repository-level baseline implementations and declared event/point threshold policy
- The SKAB official baseline gate materializes USAD/TranAD-style frozen-record controls, official-source Anomaly Transformer provenance, frozen wrapper prediction records, official SKAB precomputed leaderboard rows with frozen records, matched partial official notebook/core source reruns for T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE, plus diagnostic LSTM-AE/MSCRED/Vanilla-LSTM source reruns, but keeps the official-baseline gate closed.
- Current official-source Anomaly Transformer wrapper is a patched matched control and keeps official_external_score=false.
- Official SKAB result pickles are aligned to raw data and the README outlier leaderboard is recomputed; T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE notebook/core logic are rerun or preserved from the pinned official environment and match the README rows. LSTM-AE, MSCRED, and Vanilla-LSTM are rerun with frozen records but do not match the official leaderboard within tolerance; the source-rerun delta audit attributes those mismatches to prediction-level rerun variance rather than row or label mismatch. ArimaFD, exact split, preprocessing, and budget matching are still not closed.
- The current native audit selects the algorithmic-only branch as the accuracy anchor and keeps LLM condition verification as diagnostic evidence.
- Proposed branches now have frozen point metrics and right-window changepoint event scores, but exact official split, preprocessing, baseline protocol, and compute budget are still not aligned.

### Hydraulic

- Native reference target: published four-target Hydraulic condition-monitoring table with identical target definitions and metrics
- Hydraulic is used as a safety/non-degradation benchmark, not the main novelty benchmark.
- The final paper package does not yet align a published four-target table with identical formatting and deep temporal baselines.

### C-MAPSS

- Native reference target: NASA C-MAPSS subset-specific RUL scoring with compatible published prognostics baselines
- The task is correctly restored to original terminal RUL regression.
- The C-MAPSS native preprocessing manifest is complete: FD001-FD004 terminal test-unit records, RUL cap declaration, subset RMSE/score, continuous RUL metrics, train-only preprocessing declaration, and seed-level prediction archives are materialized.
- An LSTM sequence branch is materialized as a three-seed published-style local candidate for the LSTM RUL baseline family, but it is not an exact published-baseline reproduction.
- The current strongest local branch is the cap=150, window=160 GRU temporal anchor; AnchorPath path fusion is closed for C-MAPSS until it beats the same-window anchor.
- Train-unit pseudo-terminal validation selects the same w160/cap150 branch by RMSE, but official-test PHM score favors w80/cap150 by 408.20, so the score trade-off must be disclosed.
- The published-baseline alignment table is now materialized, but exact published-baseline reproduction, published-baseline preprocessing equivalence, and matched budget are still missing.
- The published-baseline contract is now materialized as a field-level checklist for LSTM, temporal CNN, attention-LSTM, and FD001-only CNN-LSTM references; it keeps official/published protocol and matched-budget gates closed until an exact reproduced baseline has source-matched fields and archived predictions.
- The LSTM source-protocol audit extracts the local LSTM configuration but records the primary full-text protocol as unavailable in the current environment, so source fields remain unverified.
- The open-protocol candidate audit identifies MDFA 2025 as an accessible all-subset published target and ACB 2021 as a fallback.
- The MDFA source profile reconciles FD001-FD004 raw-file counts with the MDFA published table, including FD004 train=249/test=248.
- The MDFA source-matched runner now uses source_2d time-feature convolutions; the all-subset smoke prediction archive is materialized and the FD001/FD003 low-dropout long-window plus FD002/FD004 condition-aware local branch archive is complete, but it cannot be promoted until PCA/key-sensor preprocessing and exact budget equivalence are verified.
- The MDFA strategy probe audit selects source2d_all24_pca_window80_dropout01_fd001_full and source2d_all24_pca_window80_dropout01_fd003_full for the single-condition branch while explicitly blocking any published-reproduction claim.
