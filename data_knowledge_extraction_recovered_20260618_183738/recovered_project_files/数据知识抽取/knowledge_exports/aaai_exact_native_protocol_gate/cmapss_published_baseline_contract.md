# C-MAPSS Published Baseline Contract

- Version: cmapss-published-baseline-contract-v1
- Status: `contract_complete_reproduction_pending`
- Claim boundary: This contract converts C-MAPSS published-baseline comparison into a field-by-field reproduction checklist. It does not open the official SOTA gate until a published baseline has exact source-matched preprocessing, budget, metrics, and archived predictions.

## Gate Status

| Gate | Status |
|---|---|
| source_registry_present | pass |
| native_data_contract_present | pass |
| field_matrix_present | pass |
| local_published_style_lstm_archive_present | pass |
| exact_published_reproduction_complete | missing |
| matched_budget_complete | missing |
| official_or_published_baseline_protocol_pass | missing |

## Source Registry

| Source | Type | Contract use |
|---|---|---|
| nasa_open_data_cmapss | official_dataset | [NASA CMAPSS Jet Engine Simulated Data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data) - Authoritative native task, split, and terminal-test RUL source. |
| local_cmapss_readme | local_dataset_readme | [Downloaded NASA C-MAPSS readme.txt](knowledge_exports/public_datasets/cmapss/raw/extracted/readme.txt) - Local checksum-level evidence that the ready data follows the NASA package description. |
| saxena2008_cmapss | dataset_lineage_paper | [Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation](https://doi.org/10.1109/PHM.2008.4711414) - Dataset lineage and benchmark citation, not a neural baseline protocol. |
| deep_cnn_rul_2016 | published_baseline_family | [Deep convolutional neural network based regression approach for estimation of remaining useful life](https://doi.org/10.1007/978-3-319-32025-0_14) - Candidate published CNN baseline family; exact preprocessing and budget must still be reproduced. |
| lstm_rul_2017 | published_baseline_family | [Long Short-Term Memory Network for Remaining Useful Life estimation](https://doi.org/10.1109/ICPHM.2017.7998311) - Highest-priority exact reproduction target because a local LSTM runner already exists. |
| mdfa_2025 | open_fulltext_published_baseline | [Remaining Useful Life Prediction for Aero-Engines Based on Multi-Scale Dilated Fusion Attention Model](https://www.mdpi.com/2076-3417/15/17/9813) - Open full-text P0 exact-source target after PCA/key-sensor preprocessing and budget equivalence are verified. |
| attention_lstm_ijphm_2025 | recent_published_reference | [Remaining Useful Life Prediction Using Attention-LSTM Neural Network of Aircraft Engines](https://doi.org/10.36001/ijphm.2025.v16i2.4274) - Recent high-performing subset-limited reference; useful for FD001/FD003 discussion, not FD001-FD004 all-subset proof. |
| fd001_change_point_cnn_lstm_2023 | recent_protocol_reference | [Remaining Useful Life Estimation of Turbofan Engines with Deep Learning Using Change-Point Detection Based Labeling and Feature Engineering](https://www.mdpi.com/2076-3417/13/21/11893) - Useful FD001 preprocessing reference; not sufficient for all-subset official SOTA wording. |

## Required Reproduction Fields

| Field | Requirement |
|---|---|
| official_data_split | NASA FD001-FD004 train files, test files, and terminal RUL files are used without regrouping test engines. |
| subset_scope | The compared baseline declares exactly which FD subsets are evaluated, and all reported tables use the same subset scope. |
| rul_label_policy | RUL target construction is explicit, including any piecewise cap, early-life clipping, or train-unit pseudo-terminal validation policy. |
| sensor_selection | Selected operational settings and sensors are listed; dropped constant or non-informative channels are reproducible. |
| normalization_scope | Scaler, regime normalizer, or filtering parameters are fit only on training data and reused for validation/test. |
| sequence_window | Window length, stride, padding/truncation, and last-cycle terminal evaluation are identical across compared methods. |
| architecture_config | Layer count, hidden/channel sizes, attention heads, kernels, dropout, and parameter count are declared. |
| training_budget | Epochs, batch size, optimizer, learning rate, early stopping, hardware device, and seeds are budget-matched. |
| metric_recompute | RMSE and PHM-style asymmetric RUL score are recomputed from archived per-test-engine predictions. |
| prediction_archive | Each seed stores per-test-engine prediction records with subset, unit id, true RUL, predicted RUL, and split role. |

## Baseline Contracts

| Baseline | Family | Priority | Required scope | Local archive | Exact status | Main blockers |
|---|---|---|---|---|---|---|
| lstm_rul_2017 | LSTM | p0_exact_reproduction_target | FD001, FD002, FD003, FD004 | yes | not_exact_reproduction | local row is published-style only, exact hidden size, layer count, preprocessing, validation split, and budget are not proven to match the paper |
| deep_cnn_rul_2016 | temporal CNN | p1_implementation_needed | FD001, FD002, FD003, FD004 | no | not_exact_reproduction | no exact local CNN reproduction artifact exists, source preprocessing, windowing, and training budget are not encoded in the current runner |
| mdfa_2025 | multi-scale dilated fusion attention | p0_open_exact_source_target | FD001, FD002, FD003, FD004 | no | not_exact_reproduction | source_2d runner and local branch archives exist, but the best branch changes window/dropout/condition preprocessing relative to the MDFA table, Table-4 key-sensor PCA is machine-readable but performs poorly in a short-budget probe, especially on multi-condition subsets, exact cumulative-contribution threshold and budget equivalence are not yet verified against the source |
| attention_lstm_ijphm_2025 | attention LSTM | p1_subset_reference | FD001, FD003 | no | not_exact_reproduction | published result covers FD001 and FD003, not all FD001-FD004 subsets, no local attention-LSTM exact reproduction artifact exists |
| fd001_change_point_cnn_lstm_2023 | change-point CNN-LSTM | p2_fd001_auxiliary | FD001 | no | not_exact_reproduction | FD001-only study cannot prove FD001-FD004 all-subset alignment, change-point label and filter details are not implemented in the current exact-native runner |

## Next Reproduction Queue

- lstm_rul_2017: Promote local lstm_sequence from published-style to exact reproduction by matching the paper preprocessing, sequence length, hidden/layer config, epochs, validation policy, and per-subset table.
- lstm_rul_2017_source_audit: Use cmapss_lstm_source_protocol_audit to keep the local LSTM row blocked until primary full-text protocol fields are available and verified.
- mdfa_2025: Use cmapss_mdfa_source_profile and the Table-4 key-sensor probe to separate exact-source reproduction from the stronger local branch before any gate flip.
- deep_cnn_rul_2016: Implement the temporal CNN baseline only after exact sensor/window/preprocessing and training budget fields are extracted from the source paper.
- attention_lstm_ijphm_2025: Use only as an FD001/FD003 subset reference unless a full FD001-FD004 compatible reproduction is created.

## Paper Policy

Keep C-MAPSS wording at original-task transfer evidence. Do not claim literature-wide RUL SOTA; do not compare the pooled FD001-FD004 RMSE directly against FD001-only or FD001/FD003-only references.
