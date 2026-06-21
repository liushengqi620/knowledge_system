# SKAB Native Metric Audit

- Version: skab-native-metric-audit-v1
- Status: `native_metric_audit_complete`
- Claim boundary: This audit tracks SKAB native metric readiness. It is not an official leaderboard result unless all proposed-branch gates are true and official/fair baselines share the same split, threshold, and event-window policy.

## Gate Status

| Gate | Status |
|---|---|
| proposed_frozen_prediction_archive | pass |
| proposed_point_metrics_recomputable | pass |
| proposed_changepoint_event_window_scored | pass |
| external_protocol_controls_present | pass |
| point_adjustment_disabled_for_claim_rows | pass |
| validation_thresholds_recorded | pass |

## Branch Summary

| Branch | Seeds | Macro-F1 | Positive F1 | FAR % | MAR % | CP Recall | Event-window | Frozen predictions |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Anomaly Transformer | 3 | 0.4716 | 0.3034 | 38.34 | 63.29 | 1.0000 | yes | yes |
| a0_algorithmic_only | 3 | 0.8450 | 0.8136 | 9.21 | 22.73 | 0.9060 | yes | yes |
| anomaly_transformer | 3 | 0.4493 | 0.3739 | 56.69 | 44.87 | - | yes | no |
| skab_llm_condition_candidate_gate_valadm001_w005_c010_w48_e40 | 3 | 0.8209 | 0.7788 | 8.39 | 28.66 | 0.8852 | yes | yes |
| skab_strong_anchor_w48_e40 | 3 | 0.8193 | 0.7830 | 11.36 | 25.62 | 0.8754 | yes | yes |
| tranad | 3 | 0.4825 | 0.3633 | 46.22 | 50.32 | 0.6738 | yes | yes |
| usad | 3 | 0.4423 | 0.3402 | 54.32 | 52.88 | 0.8753 | yes | yes |

## Next Actions

- Align official/fair SKAB baselines to the same split, validation-only threshold policy, event-window width, and compute budget.
- Keep point adjustment disabled unless reproducing an explicitly declared native point-adjusted protocol.
- Do not upgrade to official leaderboard wording until exact public split, preprocessing, baseline, threshold, and budget gates are all true.
