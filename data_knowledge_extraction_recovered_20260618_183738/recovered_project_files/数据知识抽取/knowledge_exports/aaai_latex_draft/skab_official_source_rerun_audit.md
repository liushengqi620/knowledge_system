# SKAB Official Source Rerun Audit

- Version: skab-official-source-rerun-audit-v1
- Status: official_skab_source_rerun_audit_partial
- Claim boundary: This audit reruns implemented official SKAB notebook/core logic and records environment blockers for the remaining official notebooks. It is partial source-rerun evidence, not a complete official leaderboard rerun.
- Python: 3.12.12
- Declared Python constraint: >=3.10,<3.11

## Gates

| Gate | Status |
|---|---:|
| official_skab_repository_extracted | pass |
| official_notebook_sources_present | pass |
| official_core_sources_present | pass |
| current_python_matches_official_constraint | blocked |
| tensorflow_available_for_deep_official_notebooks | blocked |
| arimafd_available_for_external_official_notebook | blocked |
| source_rerun_t2_family_recomputed | pass |
| source_rerun_tensorflow_lightweight_baselines_recomputed | pass |
| source_rerun_tensorflow_deep_baselines_partial | pass |
| source_rerun_frozen_records_materialized | pass |
| official_deep_notebooks_rerun_from_source | pass |
| source_rerun_leaderboard_deltas_explained | pass |
| official_notebooks_rerun_from_source | blocked |

## Source Rerun Rows

| Method | Records | F1 | FAR | MAR | README match | Frozen record file | Boundary |
|---|---:|---:|---:|---:|---:|---|---|
| T2 | 23801 | 0.6598 | 19.21 | 42.60 | yes | `skab_official_source_rerun_records\T2.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. |
| T2-q | 23801 | 0.7581 | 26.62 | 24.92 | yes | `skab_official_source_rerun_records\T2-q.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. |
| MSCRED | 22475 | 0.3382 | 48.57 | 72.09 | no | `skab_official_source_rerun_records\MSCRED.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Minimal Keras call-signature compatibility patch applied; architecture and threshold logic unchanged. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| Isolation_Forest | 23801 | 0.2868 | 2.56 | 82.89 | yes | `skab_official_source_rerun_records\Isolation_Forest.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| MSET | 23801 | 0.7800 | 39.73 | 14.13 | yes | `skab_official_source_rerun_records\MSET.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| Vanilla_AE | 23801 | 0.3938 | 2.96 | 74.86 | yes | `skab_official_source_rerun_records\Vanilla_AE.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| Conv_AE | 23801 | 0.7842 | 13.38 | 28.05 | yes | `skab_official_source_rerun_records\Conv_AE.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| LSTM_AE | 23801 | 0.7515 | 29.27 | 24.59 | no | `skab_official_source_rerun_records\LSTM_AE.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |
| Vanilla_LSTM | 23631 | 0.5111 | 11.59 | 62.29 | no | `skab_official_source_rerun_records\Vanilla_LSTM.jsonl` | Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun. Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method. |

## Source-Rerun Delta Audit

- Audit file: `skab_source_rerun_delta_audit.json`
- Status: source_rerun_delta_profile_complete
- Explained: yes
- Covered delta methods: LSTM_AE, MSCRED, Vanilla_LSTM
- Claim boundary: This audit explains source-rerun leaderboard deltas at the frozen-record level. It does not convert unmatched source reruns into official leaderboard matches.

## Unmatched Source Rerun Rows

These methods have frozen source-rerun records and row/label alignment deltas are explained at the prediction level; they still do not match the README leaderboard tolerance, so they remain diagnostic evidence.

- LSTM_AE
- MSCRED
- Vanilla_LSTM

## Dependency Readiness

| Method | Notebook | Missing dependencies | Runnable now? |
|---|---|---|---:|
| T2 | `t2_SKAB.ipynb` | none | yes |
| T2-q | `t2_with_q_SKAB.ipynb` | none | yes |
| Isolation_Forest | `isolation_forest.ipynb` | tensorflow | no |
| MSET | `MSET.ipynb` | tensorflow | no |
| Conv_AE | `Conv_AE.ipynb` | tensorflow | no |
| LSTM_AE | `LSTM_AE.ipynb` | tensorflow | no |
| MSCRED | `mscred.ipynb` | tensorflow | no |
| Vanilla_AE | `Vanilla_AE.ipynb` | tensorflow | no |
| Vanilla_LSTM | `Vanilla_LSTM.ipynb` | tensorflow | no |
| Arima_anomaly_detection | `ArimaFD.ipynb` | arimafd | no |

## Next Actions

- Use the pinned Python 3.10 official-SKAB environment with TensorFlow 2.15 for any TensorFlow source-rerun refresh.
- Resolve or formally scope out the unavailable arimafd dependency before making any ArimaFD official-source claim.
- Keep LSTM-AE/MSCRED/Vanilla-LSTM source reruns as diagnostic frozen-record evidence: their row/label alignment deltas are explained at the prediction level, but they still do not match the official leaderboard within tolerance.
- Keep the implemented official source reruns as partial provenance evidence, not as a full leaderboard-superiority claim.
