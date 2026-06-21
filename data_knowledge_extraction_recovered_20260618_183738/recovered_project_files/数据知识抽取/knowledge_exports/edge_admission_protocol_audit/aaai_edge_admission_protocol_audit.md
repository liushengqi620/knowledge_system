# AAAI Edge Admission Protocol Audit

- Overall status: protocol_and_evidence_complete
- Gate order: validation_gain, low_tail_far_mar_safety, cf_guard
- Probe levels: lag_group, single_edge, source_family, target_group
- Relation interfaces: attention_bias, channel_fusion_gate, edge_mask, patch_or_frequency_relation_mask

This audit checks whether the paper's edge/path-fusion story is backed by reusable experiment artifacts. It deliberately separates the protocol contract from measured evidence, including negative evidence.

## Requirement Status

| Requirement | Status | Evidence | Next action |
|---|---|---|---|
| Freeze and hierarchically probe candidate edge pools | satisfied | Gate order=['validation_gain', 'low_tail_far_mar_safety', 'cf_guard']; probe levels=['lag_group', 'single_edge', 'source_family', 'target_group']; families=['expert', 'llm']; relation interfaces=['attention_bias', 'channel_fusion_gate', 'edge_mask', 'patch_or_frequency_relation_mask', 'residual_channel_after_validation_admission']. | Keep source-family, target-group, lag-group, and single-edge probes synchronized with every new candidate source. |
| Materialize measured hierarchical edge-probe evidence | satisfied | TEP probe status=ok; seeds=[42, 43, 44]; max_rows=None; levels=['lag_group', 'single_edge', 'source_family', 'target_group']; admitted_edges=[]; pre_cf_rejections=20. | Keep the measured probe archived with seed-level rows and admitted single-edge records. |
| Compare independent LLM edges against conditional expert-edge verification | satisfied | Variants=['a0_algorithmic_only', 'a1_expert_candidate_gate', 'a2_independent_llm_candidate', 'a3_llm_expert_graph_correction', 'a4_llm_expert_condition_verifier', 'a5_weak_class_condition_verifier']; complete run rows=['a0_algorithmic_only', 'a1_expert_candidate_gate', 'a2_independent_llm_candidate', 'a3_llm_expert_graph_correction', 'a4_llm_expert_condition_verifier', 'a5_weak_class_condition_verifier']; admitted=[]; rejected=['a1_expert_candidate_gate', 'a2_independent_llm_candidate', 'a3_llm_expert_graph_correction', 'a4_llm_expert_condition_verifier', 'a5_weak_class_condition_verifier']; a4 uses verifier metadata and a2 keeps independent LLM as a negative control. | Report current LLM verifier evidence as reliability-gated negative/diagnostic evidence unless a future verified matrix passes validation and low-tail guards. |
| Prove mechanism evidence helps through admission rather than raw graph injection | satisfied | Variants=['algorithmic_candidate_gate_control', 'expert_candidate_data_gate', 'expert_candidate_data_gate_consistency', 'expert_candidate_no_gate', 'late_expert_path', 'no_mechanism', 'raw_expert_graph']; complete rows=['no_mechanism', 'raw_expert_graph', 'late_expert_path', 'expert_candidate_no_gate', 'expert_candidate_data_gate', 'expert_candidate_data_gate_consistency', 'algorithmic_candidate_gate_control']; negative_control=True; data_gate=True; algorithmic_control=True. | Keep raw-expert, data-gated expert, and algorithmic controls in the same seed/budget matrix. |

## Paper Policy

Use the protocol as the method contract now. The current three-seed/full-row TEP probe is measured edge-admission evidence for the bounded probe plan and admits no single edge under the ordered guards; the full SKAB LLM verifier matrix is complete and treats LLM evidence as reliability-gated negative/diagnostic evidence because no LLM branch passes validation and low-tail admission.

## Next Actions

- none
