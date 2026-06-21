# SKAB Source-Rerun Delta Audit

- Version: skab-source-rerun-delta-audit-v1
- Status: source_rerun_delta_profile_complete
- Claim boundary: This audit explains source-rerun leaderboard deltas at the frozen-record level. It does not convert unmatched source reruns into official leaderboard matches.
- Unmatched source-rerun methods: LSTM_AE, MSCRED, Vanilla_LSTM

## Gates

| Gate | Status |
|---|---:|
| source_rerun_audit_present | pass |
| unmatched_methods_covered | pass |
| records_present_for_all_methods | pass |
| record_sets_identical_for_unmatched_methods | pass |
| labels_identical_for_unmatched_methods | pass |
| deltas_attributed_to_predictions | pass |

## Delta Rows

| Method | Status | Records repo/source/common | Pred disagreement | Agreement | Source-repo F1 | Source-repo FAR | Source-repo MAR | Interpretation |
|---|---|---:|---:|---:|---:|---:|---:|---|
| LSTM_AE | prediction_delta_only | 23801/23801/23801 | 2162 | 0.9092 | +0.0105 | -0.69 | -1.33 | Repository pickle and source-rerun records cover the same keyed samples with identical labels; the leaderboard delta is therefore from prediction differences under the rerun, not from row alignment or label mismatch. |
| MSCRED | prediction_delta_only | 22475/22475/22475 | 563 | 0.9749 | -0.0185 | -1.15 | +2.05 | Repository pickle and source-rerun records cover the same keyed samples with identical labels; the leaderboard delta is therefore from prediction differences under the rerun, not from row alignment or label mismatch. |
| Vanilla_LSTM | prediction_delta_only | 23631/23631/23631 | 1218 | 0.9485 | -0.0245 | -0.95 | +2.77 | Repository pickle and source-rerun records cover the same keyed samples with identical labels; the leaderboard delta is therefore from prediction differences under the rerun, not from row alignment or label mismatch. |

## Interpretation

For the covered unmatched methods, official repository pickles and source reruns have identical keyed sample sets and labels. The remaining delta is prediction-level and is consistent with stochastic deep-model reruns, modern TensorFlow/Keras execution differences, and the fact that official pickles are fixed precomputed outputs.

## Next Actions

- Do not use unmatched source reruns as official leaderboard matches.
- Use this audit to distinguish prediction-level rerun variance from split/label/alignment errors.
- If exact leaderboard matching is required, recover the original dependency/runtime stack or use the official precomputed rows as repository-result evidence only.
