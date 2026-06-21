# AAAI SOTA Gap Ledger

- Version: aaai-sota-gap-ledger-v1
- Status: official_sota_not_admissible
- Claim rule: Matched numerical gains are not official SOTA unless the exact-native gate for the dataset is fully true.

## Matched Results vs Current Anchors

| Dataset | Metric | Anchor | Current | Improvement | Official status | Missing exact-native gates |
|---|---|---:|---:|---:|---|---|
| TEP | Target-F1 | 0.9122 | 0.9549 | +0.0427 | matched_only | exact_public_split, exact_preprocessing, exact_metric, official_or_published_baseline_protocol, threshold_or_delay_policy, matched_budget, seed_level_prediction_artifacts |
| SKAB | Macro-F1 | 0.8193 | 0.8450 | +0.0257 | matched_only | exact_public_split, exact_preprocessing, official_or_published_baseline_protocol, matched_budget |
| Hydraulic | Macro-F1 | 0.9773 | 0.9784 | +0.0011 | matched_only | exact_public_split, exact_preprocessing, exact_metric, official_or_published_baseline_protocol, matched_budget |
| C-MAPSS | RMSE | 20.7559 | 18.0617 | +2.6942 | matched_only | official_or_published_baseline_protocol, matched_budget |

## C-MAPSS MDFA Source-Style Gap

These rows are capped/source-style comparison evidence only. They are not official SOTA proof.

| Subset | Current branch | Current RMSE | MDFA Table 5 RMSE | Gap current-reference | Boundary |
|---|---|---:|---:|---:|---|
| FD001 | window80/all24_pca/dropout0.1 | 12.5498 | 11.7800 | +0.7698 | source_style_capped_test_only_not_official_sota |
| FD003 | window80/all24_pca/dropout0.0+level_diff | 12.9260 | 11.8900 | +1.0360 | source_style_capped_test_only_not_official_sota |
| FD002 | sensor21_pca+kmeans6_settings+condition_onehot | 15.8410 | 16.3800 | -0.5390 | source_style_capped_test_only_not_official_sota |
| FD004 | sensor21_pca+kmeans6_settings+condition_onehot | 15.9596 | 19.2300 | -3.2704 | source_style_capped_test_only_not_official_sota |

- Mean source-style RMSE gap current-reference: -0.5009.

## Priority Actions

### P0 SKAB

- Reason: Current Macro-F1 is native-audited and improved, and the SKAB official baseline gate now separates fair frozen-record controls, official-source controls with frozen wrapper prediction records, recomputed official SKAB precomputed leaderboard rows, matched partial official notebook/core source reruns for T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE, and diagnostic LSTM-AE/MSCRED/Vanilla-LSTM reruns with frozen records whose row/label deltas are attributed to prediction-level rerun variance, but exact split/preprocessing, ArimaFD, and budget gates remain closed.
- Blocking gates: exact_public_split, exact_preprocessing, official_or_published_baseline_protocol, matched_budget
- Next: Use skab_official_baseline_gate as the gate-closing checklist before any SKAB official SOTA wording.
- Next: Promote the official precomputed leaderboard rows only as frozen repository-result evidence; rerun official or faithful SKAB notebook/core baselines before official SOTA wording.
- Next: Use the T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE notebook/core reruns as partial provenance evidence, and keep the LSTM-AE/MSCRED/Vanilla-LSTM reruns as diagnostic frozen-record evidence despite their explained prediction-level deltas.
- Next: Run or formally scope out the remaining official ArimaFD notebook.
- Next: Add GDN and MTAD-GAT frozen prediction records only after their split, preprocessing, threshold, event-window, and budget contract matches the SKAB official/fair gate.
- Next: Keep LLM verifier diagnostic until it beats the algorithmic anchor under validation and low-tail admission.

### P0 C-MAPSS

- Reason: Native preprocessing is largely complete and MDFA source-style mean RMSE is competitive, but FD001/FD003 still trail MDFA by 0.7698/1.0360 RMSE and exact published-budget gates remain closed.
- Blocking gates: official_or_published_baseline_protocol, matched_budget
- Next: Verify MDFA source fields for key-sensor/PCA policy, RUL cap/label policy, scheduler, and full-budget equivalence.
- Next: Run the selected FD001/FD003 single-condition branch and FD002/FD004 condition-aware branch under a published-budget reproduction contract.
- Next: Treat raw-test cap150 results as a negative control until uncapped/native RUL scoring closes the gap.

### P1 TEP

- Reason: The matched Target-F1 gain is largest, but too many external protocol gates are missing for official SOTA wording.
- Blocking gates: exact_public_split, exact_preprocessing, exact_metric, official_or_published_baseline_protocol, threshold_or_delay_policy, matched_budget, seed_level_prediction_artifacts
- Next: Choose two external TEP/FDD protocols and reproduce their split, delay policy, class taxonomy, and metrics exactly.
- Next: Export seed-level prediction artifacts for the strict 22-class route, not summary-only rows.

### P2 Hydraulic

- Reason: Near-ceiling gains are too small to carry the paper; use it as non-degradation evidence.
- Blocking gates: exact_public_split, exact_preprocessing, exact_metric, official_or_published_baseline_protocol, matched_budget
- Next: Reformat to a published four-target protocol only after SKAB/C-MAPSS gates stop blocking the main claim.
- Next: Add one compatible temporal neural baseline if this benchmark is kept in the final main table.
