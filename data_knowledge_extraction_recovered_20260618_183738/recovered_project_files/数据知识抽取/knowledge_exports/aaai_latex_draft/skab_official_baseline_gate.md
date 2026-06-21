# SKAB Official Baseline Gate

- Version: skab-official-baseline-gate-v1
- Status: skab_official_baseline_gate_not_closed
- Claim boundary: Current SKAB external evidence includes fair reconstruction baselines with frozen records and an official-source Anomaly Transformer wrapper, but it is not an official SKAB leaderboard or paper-score reproduction.

## Gate Status

| Gate | Status |
|---|---:|
| style_baseline_frozen_records_present | pass |
| official_repo_provenance_present | pass |
| anomaly_transformer_official_source_adapter_present | pass |
| anomaly_transformer_official_source_wrapper_present | pass |
| official_source_wrapper_frozen_prediction_records_present | pass |
| official_external_score_claim_blocked | pass |
| skab_official_repository_artifacts_present | pass |
| skab_official_precomputed_outlier_baselines_recomputed | pass |
| skab_official_partial_source_rerun_evidence_present | pass |
| skab_official_repository_notebook_baselines_reproduced | blocked |
| exact_split_preprocessing_budget_matched | blocked |
| safe_to_flip_skab_official_baseline_gate | blocked |

## Style Baselines

| Method | Seeds | Macro-F1 | FAR | MAR | Frozen records | Boundary |
|---|---:|---:|---:|---:|---:|---|
| usad | 3 | 0.4423 +/- 0.0370 | 54.32 | 52.88 | 3/3 | USAD/TranAD-style fair baselines with frozen native records; not official repository reproductions. |
| tranad | 3 | 0.4825 +/- 0.0533 | 46.22 | 50.32 | 3/3 | USAD/TranAD-style fair baselines with frozen native records; not official repository reproductions. |

## Official-Source Adapted Controls

| Method | Seeds | Macro-F1 | FAR | Official score? | Frozen records? | Boundary |
|---|---:|---:|---:|---:|---:|---|
| anomaly_transformer_official_source_wrapper | 3 | 0.4716 +/- 0.0487 | 38.34 | no | yes | Official source architecture with patched SKAB validation-only protocol; not an official Anomaly Transformer paper benchmark score. |

## Official Repository Precomputed Rows

| Method | Records | F1 | FAR | MAR | README match | Frozen record file | Boundary |
|---|---:|---:|---:|---:|---:|---|---|
| Conv_AE | 23801 | 0.7838 | 13.55 | 28.02 | yes | `skab_official_repository_baseline_records\Conv_AE.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |
| Isolation_Forest | 23801 | 0.2868 | 2.56 | 82.89 | yes | `skab_official_repository_baseline_records\Isolation_Forest.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |
| LSTM_AE | 23801 | 0.7410 | 29.96 | 25.92 | yes | `skab_official_repository_baseline_records\LSTM_AE.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |
| MSCRED | 22475 | 0.3567 | 49.72 | 70.04 | yes | `skab_official_repository_baseline_records\MSCRED.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |
| MSET | 23801 | 0.7800 | 39.73 | 14.13 | yes | `skab_official_repository_baseline_records\MSET.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |
| T2-q | 23801 | 0.7581 | 26.62 | 24.92 | yes | `skab_official_repository_baseline_records\T2-q.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |
| T2 | 23801 | 0.6598 | 19.21 | 42.60 | yes | `skab_official_repository_baseline_records\T2.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |
| Vanilla_AE | 23801 | 0.3910 | 2.59 | 75.15 | yes | `skab_official_repository_baseline_records\Vanilla_AE.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |
| Vanilla_LSTM | 23631 | 0.5356 | 12.54 | 59.53 | yes | `skab_official_repository_baseline_records\Vanilla_LSTM.jsonl` | Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun. |

## Official Notebook/Core Source Rerun Rows

| Method | Notebook | Records | F1 | FAR | MAR | README match | Frozen record file | Boundary |
|---|---|---:|---:|---:|---:|---:|---|---|
| T2 | `t2_SKAB.ipynb` | 23801 | 0.6598 | 19.21 | 42.60 | yes | `skab_official_source_rerun_records\T2.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. |
| T2-q | `t2_with_q_SKAB.ipynb` | 23801 | 0.7581 | 26.62 | 24.92 | yes | `skab_official_source_rerun_records\T2-q.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. |
| MSCRED | `mscred.ipynb` | 22475 | 0.3382 | 48.57 | 72.09 | no | `skab_official_source_rerun_records\MSCRED.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Minimal Keras call-signature compatibility patch applied; architecture and threshold logic unchanged. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| Isolation_Forest | `isolation_forest.ipynb` | 23801 | 0.2868 | 2.56 | 82.89 | yes | `skab_official_source_rerun_records\Isolation_Forest.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| MSET | `MSET.ipynb` | 23801 | 0.7800 | 39.73 | 14.13 | yes | `skab_official_source_rerun_records\MSET.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| Vanilla_AE | `Vanilla_AE.ipynb` | 23801 | 0.3938 | 2.96 | 74.86 | yes | `skab_official_source_rerun_records\Vanilla_AE.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| Conv_AE | `Conv_AE.ipynb` | 23801 | 0.7842 | 13.38 | 28.05 | yes | `skab_official_source_rerun_records\Conv_AE.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| LSTM_AE | `LSTM_AE.ipynb` | 23801 | 0.7515 | 29.27 | 24.59 | no | `skab_official_source_rerun_records\LSTM_AE.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| Vanilla_LSTM | `Vanilla_LSTM.ipynb` | 23631 | 0.5111 | 11.59 | 62.29 | no | `skab_official_source_rerun_records\Vanilla_LSTM.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |

Source rerun blockers: current_python_matches_official_constraint, tensorflow_available_for_deep_official_notebooks, arimafd_available_for_external_official_notebook, official_notebooks_rerun_from_source

Source rerun delta audit: source_rerun_delta_profile_complete; explained=yes; covered=LSTM_AE, MSCRED, Vanilla_LSTM

Source rerun unmatched methods: LSTM_AE, MSCRED, Vanilla_LSTM

## Next Actions

- Run or faithfully port the official SKAB repository notebook/core baselines, not only style-matched reconstruction models.
- Use the official precomputed leaderboard rows only as frozen repository-result evidence until notebook/source rerun is closed.
- Use T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE source reruns as partial provenance evidence; keep LSTM-AE/MSCRED/Vanilla-LSTM as diagnostic reruns because their deltas are prediction-level rerun variance rather than official leaderboard matches; keep ArimaFD blocked until rerun or formally scoped out.
- Add the official SKAB notebook/core baseline predictions to the same frozen-record audit format used by the fair controls and official-source wrapper.
- Freeze the exact split, preprocessing, threshold, event-window, and budget contract across proposed and baseline models.
