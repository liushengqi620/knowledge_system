# C-MAPSS Published Baseline Alignment

- Version: cmapss-published-baseline-alignment-v1
- Status: `published_baseline_alignment_partial_not_sota_proof`
- Claim boundary: This artifact separates local matched C-MAPSS baselines from published-reference baselines. It materializes the alignment table, but does not mark any published baseline as reproduced or budget-matched.

## Gate Status

| Gate | Status |
|---|---|
| alignment_artifact_present | pass |
| native_manifest_present | pass |
| local_fd001_fd004_seed_archive_present | pass |
| local_matched_baseline_protocol_present | pass |
| published_reference_registry_present | pass |
| published_style_candidate_seed_archive_present | pass |
| published_reproduction_seed_artifacts_present | missing |
| exact_published_preprocessing_matched | missing |
| matched_budget_present | missing |
| literature_wide_sota_admissible | missing |

## Reference Sources

| ID | Source | Protocol use |
|---|---|---|
| nasa_open_data_cmapss | [NASA CMAPSS Jet Engine Simulated Data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data) | Primary data source for train/test trajectories, terminal test-unit RUL labels, three operating settings, and sensor columns. |
| nasa_pcoe_repository | [NASA PCoE Turbofan Engine Degradation Simulation](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/) | Repository-level description of four C-MAPSS subsets under different operating-condition and fault-mode combinations. |
| saxena2008_cmapss | [Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation](https://doi.org/10.1109/PHM.2008.4711414) | Original PHM 2008 C-MAPSS simulation reference; use for dataset lineage and PHM-style RUL scoring context. |

## Local Matched Protocol Rows

| Source | Name | Seeds | RUL cap | Windows | Subsets | RMSE | Score | Status |
|---|---|---:|---|---|---|---:|---:|---|
| current_proposed_or_formal_branch | cmapss_original_rul_terminal_anchor_w48_e20 | 3 | 125.0 | 48 | FD001, FD002, FD003, FD004 | 31.2554 | 41469.99 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | cmapss_rul_anchorpath_bigru_cls020_cap150_w80_e20 | 3 | 150.0 | 80 | FD001, FD002, FD003, FD004 | 18.6666 | 6981.54 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | cmapss_rul_anchorpath_bigru_cls020_w80_e20 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 20.4792 | 7185.62 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | cmapss_rul_direct_regime_bitempmix_w80_e20 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 21.6882 | 8816.97 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | cmapss_rul_direct_regime_tempmix_w80_e20 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 23.8395 | 12964.15 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | gru_sequence_w80_cap125 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 20.7559 | 7531.00 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | gru_sequence_w80_cap150 | 3 | 150.0 | 80 | FD001, FD002, FD003, FD004 | 18.4365 | 6428.78 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | gru_sequence_w160_cap150 | 3 | 150.0 | 160 | FD001, FD002, FD003, FD004 | 18.0617 | 6525.46 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | lstm_sequence | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 21.6521 | 9679.97 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | tcn_sequence_w80_cap125 | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 25.8894 | 19477.53 | local_matched_protocol_seed_archive |
| current_proposed_or_formal_branch | tcn_sequence_w80_cap150 | 3 | 150.0 | 80 | FD001, FD002, FD003, FD004 | 25.6942 | 25817.31 | local_matched_protocol_seed_archive |
| local_matched_baseline | gru_sequence | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 20.7559 | 7531.00 | local_matched_protocol_not_published_reproduction |
| local_matched_baseline | tcn_sequence | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 25.8894 | 19477.53 | local_matched_protocol_not_published_reproduction |
| published_style_local_candidate | lstm_sequence | 3 | 125.0 | 80 | FD001, FD002, FD003, FD004 | 21.6521 | 9679.97 | published_style_seed_archive_not_exact_reproduction |

## Published Reference Registry

| ID | Family | Year | Status | Blocking fields |
|---|---|---:|---|---|
| deep_cnn_rul_2016 | [CNN regression](https://doi.org/10.1007/978-3-319-32025-0_14) | 2016 | reference_only_not_reproduced | exact sensor selection, RUL cap, normalization scope, training budget, seed-level prediction archive |
| lstm_rul_2017 | [LSTM sequence RUL](https://doi.org/10.1109/ICPHM.2017.7998311) | 2017 | reference_only_not_reproduced | subset table reproduction, RUL cap, validation split, epochs and hidden size, seed-level prediction archive |
| attention_lstm_ijphm_2025 | [attention LSTM](https://papers.phmsociety.org/index.php/ijphm/article/download/4274/2620) | 2025 | reference_only_not_reproduced | covered FD subsets, preprocessing equivalence, RUL cap equivalence, matched training budget, seed-level prediction archive |
| hierarchical_transformer_sensors_2024 | [hierarchical Transformer](https://www.mdpi.com/1424-8220/24/3/824) | 2024 | reference_only_not_reproduced | windowing, label cap, feature scaling, FD001-FD004 table comparability, training budget |

## Wording

- Safe: C-MAPSS supports original terminal RUL transfer under local matched FD001-FD004 controls; current path-fusion branches remain challengers unless admitted over the temporal anchor.
- Unsafe: C-MAPSS proves literature-wide or official RUL SOTA, or proves path-fusion benefit before validation-safe admission.

## Next Actions

- Use cmapss_published_baseline_contract as the field-level checklist before promoting any published-style row into an exact published-baseline reproduction.
- Select at least two published C-MAPSS RUL baselines and reproduce them with identical FD001-FD004 split, RUL cap, preprocessing, and metrics.
- Promote the LSTM published-style candidate only after the exact LSTM paper configuration, preprocessing, epochs, hidden size, and subset table are matched.
- Archive per-test-engine predictions for every reproduced published baseline and compute subset RMSE/score from the frozen records.
- Normalize or explicitly match training budget: window length, epochs, batch size, hidden size, seeds, and train/validation unit split.
