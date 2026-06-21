# C-MAPSS Exact-Native Gap Audit

- Version: cmapss-exact-native-gap-audit-v1
- Status: cmapss_exact_native_gap_protocol_budget_pending
- Claim boundary: This audit separates C-MAPSS score gaps from exact-native protocol gaps. It does not authorize official or literature-wide SOTA wording.
- Exact gate missing gates: official_or_published_baseline_protocol, matched_budget

## Gates

| Gate | Status |
|---|---:|
| native_exact_nonbaseline_fields_pass | pass |
| published_contract_materialized | pass |
| mdfa_open_source_profile_materialized | pass |
| mdfa_local_full_branch_archive_present | pass |
| mdfa_score_gap_quantified | pass |
| exact_published_reproduction_complete | blocked |
| matched_budget_complete | blocked |
| mdfa_exact_source_policy_verified | blocked |
| official_sota_admissible | blocked |

## Requirement Matrix

| Requirement | Status | Evidence |
|---|---|---|
| native C-MAPSS task/split/preprocessing/metric | pass | exact-native gate and native preprocessing manifest pass all non-baseline C-MAPSS fields |
| published baseline contract | partial | field-level contract exists, but no published baseline is exact-reproduced |
| MDFA open-source profile | partial | open full text, hyperparameters, architecture fields, Table-4 key sensors, and raw-count reconciliation are materialized |
| MDFA local four-subset archive | partial | strategy audit reports a complete FD001-FD004 three-seed local branch archive |
| exact MDFA preprocessing and label policy | blocked | PCA cumulative threshold and exact test-label scoring policy are not machine-readable; selected local branches intentionally deviate from MDFA preprocessing |
| matched training budget | blocked | local full branches use 100 epochs/batch 32 but selected window/dropout/condition policies are not budget-equivalent to the published MDFA protocol |
| C-MAPSS path fusion | closed_challenger | backbone audit keeps path fusion closed until it beats the same-window temporal anchor under the pseudo-terminal validation panel |

## MDFA Budget And Protocol Matrix

| Route | Window | Epochs | Batch | Dropout | Feature policy | Temporal mode | Condition policy | Claim use |
|---|---:|---:|---:|---|---|---|---|---|
| MDFA 2025 published protocol | 30 | 100 | 32 | 0.3 | Table-4/key-sensor PCA policy, exact PCA threshold unresolved | level | not machine-readable | reference protocol only |
| FD001/FD003 selected local branch | 80 | 100 | 32 | 0.1 for FD001; 0.0 selected for FD003 | all24_pca | level for FD001; level_diff for FD003 | none | local source-style candidate, not exact MDFA reproduction |
| FD002/FD004 selected local branch | 80 | 100 | 32 | 0.3 | sensor21_pca | level | kmeans6_settings + condition_onehot | condition-aware local candidate, intentionally deviates from exact MDFA preprocessing |

## MDFA External Source Resolution

| Field | Status | Source | Evidence |
|---|---|---|---|
| paper identity | machine_readable | https://www.mdpi.com/2076-3417/15/17/9813 | MDPI article page identifies Applied Sciences 2025, 15(17), 9813 and DOI 10.3390/app15179813. |
| RUL label cap | machine_readable | https://www.mdpi.com/2076-3417/15/17/9813 | The article states a piecewise linear RUL strategy and sets the initial RUL to 125. |
| C-MAPSS split and subset counts | machine_readable | https://www.mdpi.com/2076-3417/15/17/9813 | The article lists FD001-FD004 operating conditions, fault modes, and train/test unit counts. |
| training hyperparameters | machine_readable | https://www.mdpi.com/2076-3417/15/17/9813 | The article lists batch_size 32, window_size 30, epoch 100, Adam, MSE, learning rate 0.0001, and dropout 0.3. |
| MDFA architecture | machine_readable | https://www.mdpi.com/2076-3417/15/17/9813 | The article lists the parallel dilated convolution branches with dilation rates 1, 2, and 4 and attention/fusion module settings. |
| key sensors | machine_readable | https://www.mdpi.com/2076-3417/15/17/9813 | The article's Table 4 lists key C-MAPSS sensor variables including Ps30, T24, T30, P30, Phi, Nf, Nc, and W31/W32. |
| PCA threshold or per-subset component count | not_machine_readable | https://www.mdpi.com/2076-3417/15/17/9813 | The article states that PCA components are selected by cumulative contribution rate and references Figure 4, but does not provide a numeric threshold or exact component counts. |
| source code or supplementary reproduction package | not_available_from_article_page | https://www.mdpi.com/2076-3417/15/17/9813 | The article page exposes no Supplementary or GitHub entry, and the data availability statement says supporting data are available from the corresponding author upon reasonable request. |

## MDFA Source-Style Subset Gaps

| Subset | Current RMSE | Reference RMSE | Gap current-reference | Claim boundary |
|---|---:|---:|---:|---|
| FD001 | 12.5498 | 11.7800 | +0.7698 | source_style_capped_test_only_not_official_sota |
| FD003 | 12.9260 | 11.8900 | +1.0360 | source_style_capped_test_only_not_official_sota |
| FD002 | 15.8410 | 16.3800 | -0.5390 | source_style_capped_test_only_not_official_sota |
| FD004 | 15.9596 | 19.2300 | -3.2704 | source_style_capped_test_only_not_official_sota |

## Next Actions

- Do not spend the next run on broad architecture search; the source audit now shows the MDFA paper is partially machine-readable but does not expose the PCA threshold or code needed for exact reproduction.
- For exact MDFA reproduction, obtain the missing PCA threshold/per-subset component policy and any source code from the authors, then rerun the source-compatible window=30/dropout=0.3/batch=32/epoch=100 route with archived per-engine predictions.
- For local SOTA-style evidence, target FD001/FD003 residual RMSE gaps while keeping the claim outside official MDFA reproduction wording.
- Keep C-MAPSS path fusion as a challenger until it beats the w160/cap150 temporal anchor on the train-only pseudo-terminal validation panel.
