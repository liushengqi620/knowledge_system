# C-MAPSS LSTM Source Protocol Audit

- Version: cmapss-lstm-source-protocol-audit-v1
- Status: `source_protocol_incomplete_local_config_extracted`
- Claim boundary: The local LSTM sequence branch is a reproducible published-style candidate, but the 2017 LSTM paper cannot be promoted to an exact reproduced baseline until the primary full-text protocol fields are available and all required fields are matched.

## Gate Status

| Gate | Status |
|---|---|
| primary_source_identity_verified | pass |
| official_dataset_protocol_verified | pass |
| local_lstm_seed_archive_present | pass |
| local_config_extracted | pass |
| paper_fulltext_protocol_available | missing |
| all_required_source_fields_verified | missing |
| safe_to_promote_lstm_to_exact_reproduction | missing |

## Source Access

| Source | Type | Status | Exact use |
|---|---|---|---|
| [ieee_lstm_2017_record](https://doi.org/10.1109/ICPHM.2017.7998311) | primary_metadata | metadata_available_protocol_fields_insufficient | no |
| [ieee_lstm_2017_pdf](https://ieeexplore.ieee.org/iel7/7990620/7998291/07998311.pdf) | primary_fulltext | not_available_in_current_environment | no |
| [nasa_cmapss_data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data) | official_dataset | available | yes |

## Local LSTM Candidate

- Seed files: 3
- Seeds: 42, 43, 44
- Mean RMSE: 21.6521
- Mean score: 9679.97
- Unique config: `{"batch_size": [256], "dropout": [0.1], "epochs": [25], "hidden_dim": [64], "layers": [2], "learning_rate": [0.001], "rul_cap": [125.0], "window_size": [80]}`

## Unverified Source Fields

- sensor_selection
- normalization_scope
- rul_label_policy
- sequence_window
- architecture_config
- training_budget
- optimizer
- learning_rate
- epochs
- batch_size
- validation_policy
- seed_policy
- published_subset_table

## Next Actions

- Obtain the IEEE-authorized full text or author-provided official manuscript for Zheng et al. 2017.
- Extract exact sensor selection, normalization, RUL cap, sequence length, architecture, optimizer, epochs, batch size, validation, and seed policy.
- Add a source-matched LSTM runner profile only after those fields are extracted; keep the current local LSTM as published-style evidence until then.
- After running the source-matched profile, archive per-test-engine predictions and recompute FD001-FD004 subset RMSE/score before flipping the published-baseline gate.
