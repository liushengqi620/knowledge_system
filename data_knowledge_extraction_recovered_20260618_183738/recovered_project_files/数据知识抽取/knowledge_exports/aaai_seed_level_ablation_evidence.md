# AAAI Seed-Level Ablation Evidence

- Status: partial
- Rows total: 24
- Complete seed-level rows: 24
- Artifact root: `knowledge_exports/aaai_seed_level_ablation_artifacts`
- Completion rule: Rows count as seed-level evidence when all three expected seeds have metrics and copied source JSON artifacts. This ledger does not by itself complete missing no-tail/no-counterfactual/no-complexity final interventions.

| Group | Variant | Dataset | Metric | Seeds | Mean | Std | Planned ablation link | Source |
|---|---|---|---|---:|---:|---:|---|---|
| formal_public_protocol | skab_strong_anchor | skab | macro_f1 | 3 | 0.8457 | 0.0144 | Anchor only / Full model / RUL transfer | `knowledge_exports/aaai_formal_public_protocol/aaai_formal_public_protocol.json` |
| formal_public_protocol | skab_llm_condition_candidate_gate | skab | macro_f1 | 3 | 0.8308 | 0.0082 | LLM only safety/control | `knowledge_exports/aaai_formal_public_protocol/aaai_formal_public_protocol.json` |
| formal_public_protocol | cmapss_original_rul_anchor | cmapss | rul_rmse | 3 | 31.2554 | 0.7798 | Anchor only / Full model / RUL transfer | `knowledge_exports/aaai_formal_public_protocol/aaai_formal_public_protocol.json` |
| formal_public_protocol | cmapss_rul_direct_regime_tempmix | cmapss | rul_rmse | 3 | 23.8395 | 0.2021 | Lag/residual only / Full model | `knowledge_exports/aaai_formal_public_protocol/aaai_formal_public_protocol.json` |
| formal_public_protocol | cmapss_rul_direct_regime_bitempmix | cmapss | rul_rmse | 3 | 21.6882 | 0.2857 | Lag/residual only / Full model | `knowledge_exports/aaai_formal_public_protocol/aaai_formal_public_protocol.json` |
| formal_public_protocol | cmapss_rul_anchorpath_bigru_cls020 | cmapss | rul_rmse | 3 | 20.4792 | 0.1344 | Lag/residual only / Full model | `knowledge_exports/aaai_formal_public_protocol/aaai_formal_public_protocol.json` |
| tep_sequence_gdn | no_graph | TEP | target_defect_macro_f1 | 3 | 0.3922 | 0.0510 | Anchor only / Graph only control | `knowledge_exports/tep_gdn_20k_e10_recovered.json` |
| tep_sequence_gdn | all_lagged | TEP | target_defect_macro_f1 | 3 | 0.4051 | 0.0518 | Unfiltered evidence | `knowledge_exports/tep_gdn_20k_e10_recovered.json` |
| tep_sequence_gdn | reliable_lagged | TEP | target_defect_macro_f1 | 3 | 0.4149 | 0.0502 | No complexity penalty control / reliability pruning | `knowledge_exports/tep_gdn_20k_e10_recovered.json` |
| tep_sequence_gdn | residual_gated_lagged | TEP | target_defect_macro_f1 | 3 | 0.5179 | 0.0372 | Lag/residual only / Full graph-temporal route | `knowledge_exports/tep_gdn_20k_e10_recovered.json` |
| tep_sequence_mtad_gat | no_graph | TEP | target_defect_macro_f1 | 3 | 0.6369 | 0.0050 | Anchor only / Graph only control | `knowledge_exports/tep_mtad_20k_e10_recovered.json` |
| tep_sequence_mtad_gat | all_lagged | TEP | target_defect_macro_f1 | 3 | 0.6337 | 0.0031 | Unfiltered evidence | `knowledge_exports/tep_mtad_20k_e10_recovered.json` |
| tep_sequence_mtad_gat | reliable_lagged | TEP | target_defect_macro_f1 | 3 | 0.6321 | 0.0021 | No complexity penalty control / reliability pruning | `knowledge_exports/tep_mtad_20k_e10_recovered.json` |
| tep_sequence_mtad_gat | residual_gated_lagged | TEP | target_defect_macro_f1 | 3 | 0.6447 | 0.0038 | Lag/residual only / Full graph-temporal route | `knowledge_exports/tep_mtad_20k_e10_recovered.json` |
| skab_mechanism_gate | no_mechanism | SKAB | macro_f1 | 3 | 0.6989 | 0.1095 | Anchor only / no expert graph | `knowledge_exports/ms_gse_rpf_mechanism_gate_ablation_full/mechanism_gate_ablation_matrix.json` |
| skab_mechanism_gate | raw_expert_graph | SKAB | macro_f1 | 3 | 0.6946 | 0.1046 | Unfiltered evidence / raw expert graph | `knowledge_exports/ms_gse_rpf_mechanism_gate_ablation_full/mechanism_gate_ablation_matrix.json` |
| skab_mechanism_gate | late_expert_path | SKAB | macro_f1 | 3 | 0.8166 | 0.0251 | Expert only / late path evidence | `knowledge_exports/ms_gse_rpf_mechanism_gate_ablation_full/mechanism_gate_ablation_matrix.json` |
| skab_mechanism_gate | expert_candidate_no_gate | SKAB | macro_f1 | 3 | 0.7947 | 0.0473 | Expert only / no reliability gate | `knowledge_exports/ms_gse_rpf_mechanism_gate_ablation_full/mechanism_gate_ablation_matrix.json` |
| skab_mechanism_gate | expert_candidate_data_gate | SKAB | macro_f1 | 3 | 0.7631 | 0.0738 | Expert only / reliability admission | `knowledge_exports/ms_gse_rpf_mechanism_gate_ablation_full/mechanism_gate_ablation_matrix.json` |
| skab_mechanism_gate | expert_candidate_data_gate_consistency | SKAB | macro_f1 | 3 | 0.7467 | 0.0798 | Expert only / path consistency | `knowledge_exports/ms_gse_rpf_mechanism_gate_ablation_full/mechanism_gate_ablation_matrix.json` |
| skab_mechanism_gate | algorithmic_candidate_gate_control | SKAB | macro_f1 | 3 | 0.7534 | 0.0549 | Graph only / algorithmic control | `knowledge_exports/ms_gse_rpf_mechanism_gate_ablation_full/mechanism_gate_ablation_matrix.json` |
| skab_no_complexity_full | no_mechanism | SKAB | macro_f1 | 3 | 0.7255 | 0.0597 | Anchor only / no expert graph | `knowledge_exports/aaai_missing_ablation_runs/skab_no_complexity_full/mechanism_gate_ablation_matrix.json` |
| skab_no_complexity_full | expert_llm_candidate_data_gate_no_complexity | SKAB | macro_f1 | 3 | 0.8234 | 0.0153 | No complexity penalty / source-family scale removed | `knowledge_exports/aaai_missing_ablation_runs/skab_no_complexity_full/mechanism_gate_ablation_matrix.json` |
| skab_no_complexity_full | expert_llm_candidate_data_gate_complexity_guarded | SKAB | macro_f1 | 3 | 0.8261 | 0.0138 | No complexity penalty control / source-family scale retained | `knowledge_exports/aaai_missing_ablation_runs/skab_no_complexity_full/mechanism_gate_ablation_matrix.json` |

## Remaining Design Gaps

- No-tail-safety intervention still needs a matched run removing only H_k.
- No-counterfactual-guard still needs a formal three-seed removal row, beyond the current CF-guarded smoke.
