# SKAB Tail-Safety Policy Replay

- Status: complete_policy_replay
- Guarded H_k threshold: max low-tail F1 drop <= 0.0200
- No-tail replay threshold: 999.0
- Source matrices: `knowledge_exports/ms_gse_rpf_mechanism_gate_ablation_full/mechanism_gate_ablation_matrix.json`, `knowledge_exports/aaai_missing_ablation_runs/skab_no_complexity_full/mechanism_gate_ablation_matrix.json`
- Changed admissions after removing H_k: 0
- Candidate low-tail gain: -0.0019 +/- 0.0046

For each seed, compute candidate minus baseline validation F1 for every common class and take the configured low-tail quantile; removing H_k means this term is not allowed to reject admission.

| Variant | Runs | Test Macro-F1 | Val Gain | Low-tail Val F1 Gain | Guarded | No-tail | Changed |
|---|---:|---:|---:|---:|---|---|---|
| no_mechanism | 3 | 0.6989 +/- 0.1095 | 0.0000 | 0.0000 | admit | admit | no |
| raw_expert_graph | 3 | 0.6946 +/- 0.1046 | 0.0018 | -0.0113 | admit | admit | no |
| late_expert_path | 3 | 0.8166 +/- 0.0251 | 0.0920 | -0.0042 | admit | admit | no |
| expert_candidate_no_gate | 3 | 0.7947 +/- 0.0473 | 0.0977 | 0.0029 | admit | admit | no |
| expert_candidate_data_gate | 3 | 0.7631 +/- 0.0738 | 0.0509 | -0.0021 | admit | admit | no |
| expert_candidate_data_gate_consistency | 3 | 0.7467 +/- 0.0798 | 0.0375 | 0.0005 | admit | admit | no |
| algorithmic_candidate_gate_control | 3 | 0.7534 +/- 0.0549 | 0.0469 | -0.0043 | admit | admit | no |
| no_mechanism | 3 | 0.7255 +/- 0.0597 | 0.0000 | 0.0000 | admit | admit | no |
| expert_llm_candidate_data_gate_no_complexity | 3 | 0.8234 +/- 0.0153 | 0.0750 | 0.0043 | admit | admit | no |
| expert_llm_candidate_data_gate_complexity_guarded | 3 | 0.8261 +/- 0.0138 | 0.0681 | -0.0011 | admit | admit | no |

## Conclusion

Removing H_k does not change the final SKAB admissions because all full-protocol candidates satisfy the low-tail safety threshold; this is evidence that the reported SKAB gains are not obtained by sacrificing the weak validation class. A separate tail-stress branch is optional if the paper needs a visibly differential safety example.
