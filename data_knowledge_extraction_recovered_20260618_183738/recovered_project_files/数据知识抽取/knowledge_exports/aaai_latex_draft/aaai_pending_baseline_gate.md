# AAAI Pending Baseline Alignment Gate

- Overall status: no_pending_baselines
- Claim rule: official-source adapted controls are scored matched-protocol controls but remain inadmissible as official external leaderboard scores

This gate is intentionally not a training result. It records which strong external baselines still require implementation, protocol alignment, seed-level artifacts, and validation-only thresholding before any public comparison claim is allowed.

| Method | Family | Official task | Repo snapshot | Repo checkout | Datasets | Runner status | Score status | Admissibility | Checks | Command template | Input contract | Output contract | Claim gate | Decision artifact | Blocking reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Materialized Official-Source Adapted Controls

These rows have executable source-provenance-controlled artifacts under the matched protocol. They are not official external leaderboard scores.

| Method | Family | Official task | Datasets | Runner status | Score status | Official external score | Score artifact | Claim gate |
|---|---|---|---|---|---|---|---|---|
| PatchTST | temporal sequence | long-term time-series forecasting and representation learning | TEP, SKAB | official_source_adapted_budget_probe_available | matched_protocol_control_scored | False | `knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_budget_probe.json` | matched-protocol control only; no public leaderboard claim |
| Anomaly Transformer | temporal sequence | unsupervised time-series anomaly detection | SKAB, TEP | official_source_adapted_budget_probe_available | matched_protocol_control_scored | False | `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json` | matched-protocol control only; no public leaderboard claim |
| Graph WaveNet | graph temporal | spatial-temporal traffic forecasting | TEP | official_source_adapted_budget_probe_available | matched_protocol_control_scored | False | `knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_budget_probe.json` | matched-protocol control only; no public leaderboard claim |

## Required Runner Contract

- accept declared dataset, seed, split, window, and validation-threshold arguments
- use the same train/validation/test units as the reliable-route protocol
- write seed-level validation predictions and test predictions
- write validation-selected thresholds and no test-tuned thresholds
- write metric JSON, config hash, and executable command provenance
