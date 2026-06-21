# C-MAPSS Open Protocol Candidate Audit

- Version: cmapss-open-protocol-candidate-audit-v1
- Status: `open_candidates_identified_exact_profile_pending`
- Claim boundary: Accessible published C-MAPSS baselines exist, but none is promoted to exact-native evidence until dataset-count conflicts, preprocessing, source-matched budget, and prediction archives are resolved.

## Gate Status

| Gate | Status |
|---|---|
| open_candidate_audit_present | pass |
| accessible_all_subset_candidate_present | pass |
| accessible_training_budget_candidate_present | pass |
| mdfa_count_profile_reconciled | pass |
| exact_source_profile_ready | missing |
| safe_to_flip_published_baseline_gate | missing |

## Candidate Sources

| Candidate | Scope | Priority | Extractable fields | Blocking fields |
|---|---|---|---|---|
| [mdfa_2025](https://www.mdpi.com/2076-3417/15/17/9813) | FD001, FD002, FD003, FD004 | p0_open_exact_candidate_after_count_reconciliation | architecture, batch_size, dropout, epochs, learning_rate, loss, metrics, optimizer, preprocessing, rul_cap_or_plateau, window_size | The bundled C-MAPSS readme has an FD004 train/test count inconsistency, but the raw-file unique-unit counts match the MDFA table after source-profile reconciliation.<br>PCA component-selection details and exact train-only fitting procedure are not fully machine-readable from the HTML tables.<br>No official code snapshot is linked in the current source audit.<br>No source-matched MDFA runner or seed-level prediction archive exists yet. |
| [acb_2021](https://www.techscience.com/csse/v36n1/40892/html) | FD001, FD002, FD003, FD004 | p0_open_all_subset_candidate_training_budget_missing | architecture, metrics, penalty, rul_cap_or_degradation_start, window_size | Optimizer, learning rate, epochs, batch size, random seeds, and exact normalization procedure are not fully declared in accessible HTML text.<br>The published comparison table imports several baselines from other papers, so exact baseline reproduction still needs separate source matching. |
| [attention_lstm_ijphm_2025](https://doi.org/10.36001/ijphm.2025.v16i2.4274) | FD001, FD003 | p1_subset_reference | architecture, metrics | Only FD001 and FD003 are reported, so it cannot close the all-subset FD001-FD004 C-MAPSS gate.<br>It is useful as a subset reference, not the primary all-subset exact-native baseline. |
| [fd001_change_point_cnn_lstm_2023](https://www.mdpi.com/2076-3417/13/21/11893) | FD001 | p2_fd001_auxiliary | filtering, metrics, normalization, sensor_selection | FD001-only protocol cannot close an FD001-FD004 all-subset gate.<br>Change-point label construction would be an auxiliary protocol, not the current terminal-test RUL contract without additional alignment. |
| [lstm_rul_2017](https://doi.org/10.1109/ICPHM.2017.7998311) | FD001, FD002, FD003, FD004 | blocked_until_primary_fulltext_available | local_candidate | IEEE full-text protocol is unavailable in the current environment.<br>Exact sensor selection, normalization, architecture, sequence length, validation, and budget fields are not verified. |

## Recommended Next Target

- Primary: `mdfa_2025` - It is open full text, covers FD001-FD004, and exposes window, batch, epochs, optimizer, learning rate, dropout, sensor/PCA preprocessing, architecture, and result table fields; raw-file counts now match the MDFA table, but PCA/key-sensor preprocessing and a source-matched runner are still needed before exact claims.
- Fallback: `acb_2021` - It is open full text and all-subset, but lacks enough budget fields in the accessible HTML text.

## Next Actions

- Use cmapss_mdfa_source_profile as the count-reconciled MDFA source profile and treat the bundled readme FD004 mismatch as a disclosed data-package caveat.
- Implement a source-matched MDFA runner with window=30, batch=32, epochs=100, Adam, lr=0.0001, dropout=0.3, PCA/key-sensor preprocessing, and FD001-FD004 terminal RUL records.
- Run a three-seed reproduction and archive per-test-engine predictions before considering a published-baseline gate flip.
- Keep ACB as the fallback all-subset open baseline if MDFA source-count reconciliation fails.
