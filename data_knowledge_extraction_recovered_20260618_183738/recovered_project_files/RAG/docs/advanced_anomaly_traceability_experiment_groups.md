# Advanced Experiment Groups for KG-Enhanced Anomaly Traceability

## Positioning

The mechanism KG is not trained on production traceability rows. It is first extracted from mechanism text, then attached to downstream anomaly traceability as a reasoning and explanation layer.

Target application flow:

`anomaly event -> process observations -> KG alignment -> causal path ranking -> LLM atom adjudication -> trace explanation and optimization suggestion`

## Evidence Levels

- Level 1: mechanism KG extraction quality, already covered by the seed and paper-scale extraction protocols.
- Level 2: event-to-KG alignment quality, evaluated with reviewed process/defect mappings.
- Level 3: root-cause and trace-path ranking quality, evaluated with case labels and expert review.
- Level 4: operational usefulness, evaluated with diagnosis time, recommendation usefulness, and safety checks.

## Summary

- Total experiment rows: 57
- Tracks: 10
- Main graph artifact: `data/quality_traceability_large_kg/quality_traceability_large_kg_seed.json`
- Main instance pool: `data/baosteel_knowledge_extraction/records.jsonl`

## Experiment Tracks

### plain_traceability_baselines

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E1.1 | `rule_top_feature_trace` | non_kg_traceability | none | Hit@1/3/5 for root-cause group; trace path hit rate | P0 |
| AT-E1.2 | `shap_feature_trace` | non_kg_traceability | none | Hit@1/3/5 for root-cause group; trace path hit rate | P0 |
| AT-E1.3 | `bm25_case_retrieval` | non_kg_traceability | none | Hit@1/3/5 for root-cause group; trace path hit rate | P0 |
| AT-E1.4 | `vector_case_retrieval` | non_kg_traceability | none | Hit@1/3/5 for root-cause group; trace path hit rate | P0 |

### anomaly_detection_backbone_comparison

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E2.1 | `isolation_forest_trace` | classical_unsupervised | optional_posthoc_mapping_to_kg | Anomaly F1; AUROC; AUPRC; root-cause Hit@k | P1 |
| AT-E2.2 | `one_class_svm_trace` | classical_unsupervised | optional_posthoc_mapping_to_kg | Anomaly F1; AUROC; AUPRC; root-cause Hit@k | P1 |
| AT-E2.3 | `autoencoder_reconstruction_trace` | neural_reconstruction | optional_posthoc_mapping_to_kg | Anomaly F1; AUROC; AUPRC; root-cause Hit@k | P1 |
| AT-E2.4 | `dagmm_trace` | deep_density_reconstruction | optional_posthoc_mapping_to_kg | Anomaly F1; AUROC; AUPRC; root-cause Hit@k | P1 |
| AT-E2.5 | `tranad_trace` | transformer_time_series | optional_posthoc_mapping_to_kg | Anomaly F1; AUROC; AUPRC; root-cause Hit@k | P0 |
| AT-E2.6 | `mtad_gat_trace` | graph_attention_time_series | optional_posthoc_mapping_to_kg | Anomaly F1; AUROC; AUPRC; root-cause Hit@k | P0 |
| AT-E2.7 | `gdn_trace` | learned_sensor_graph | optional_posthoc_mapping_to_kg | Anomaly F1; AUROC; AUPRC; root-cause Hit@k | P0 |

### causal_rca_baselines

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E3.1 | `lagged_correlation_rca` | correlation_baseline | none | Root-cause Hit@1/3/5; MRR; causal direction accuracy | P0 |
| AT-E3.2 | `granger_graph_rca` | causal_time_series | causal_edges_as_soft_prior | Root-cause Hit@1/3/5; MRR; causal direction accuracy | P0 |
| AT-E3.3 | `pcmci_or_notears_rca` | causal_discovery | learned_graph_compared_with_mechanism_kg | Root-cause Hit@1/3/5; MRR; causal direction accuracy | P0 |
| AT-E3.4 | `pyrca_causal_graph_scoring` | rca_library_baseline | expert_or_learned_causal_graph | Root-cause Hit@1/3/5; MRR; causal direction accuracy | P0 |
| AT-E3.5 | `dowhy_counterfactual_rca` | counterfactual_causal_inference | kg_path_as_structural_prior | Root-cause Hit@1/3/5; MRR; causal direction accuracy | P0 |
| AT-E3.6 | `neural_granger_aerca_style_rca` | neural_causal_rca | kg_edges_as_regularizer | Root-cause Hit@1/3/5; MRR; causal direction accuracy | P0 |

### kg_reasoning_for_traceability

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E4.1 | `exact_schema_path_search` | symbolic_kg_reasoning | hard KG constraints | Trace path Hit@k; path NDCG; explanation completeness | P0 |
| AT-E4.2 | `personalized_pagerank_on_kg` | graph_walk_reasoning | weighted mechanism graph | Trace path Hit@k; path NDCG; explanation completeness | P0 |
| AT-E4.3 | `kg_embedding_link_prediction` | embedding_kg_reasoning | TransE/RotatE/ComplEx style embeddings | Trace path Hit@k; path NDCG; explanation completeness | P0 |
| AT-E4.4 | `relational_gnn_trace_ranker` | gnn_kg_reasoning | R-GCN/GAT over mechanism-instance graph | Trace path Hit@k; path NDCG; explanation completeness | P0 |
| AT-E4.5 | `temporal_kg_path_ranker` | temporal_kg_reasoning | time-window constrained mechanism paths | Trace path Hit@k; path NDCG; explanation completeness | P0 |
| AT-E4.6 | `counterfactual_kg_path_ranker` | causal_kg_reasoning | path intervention and do-calculus inspired scoring | Trace path Hit@k; path NDCG; explanation completeness | P0 |

### llm_and_graphrag_traceability

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E5.1 | `llm_zero_shot_rca` | llm_only | none | Answer faithfulness; root-cause Hit@k; action recommendation accuracy | P1 |
| AT-E5.2 | `text_rag_rca` | text_rag | retrieves raw cases/documents | Answer faithfulness; root-cause Hit@k; action recommendation accuracy | P1 |
| AT-E5.3 | `schema_rag_rca` | schema_rag | retrieves schema and labels | Answer faithfulness; root-cause Hit@k; action recommendation accuracy | P1 |
| AT-E5.4 | `graph_rag_rca` | graph_rag | retrieves KG communities/paths | Answer faithfulness; root-cause Hit@k; action recommendation accuracy | P0 |
| AT-E5.5 | `lightrag_style_dual_level_rca` | dual_level_graph_rag | low-level and high-level KG retrieval | Answer faithfulness; root-cause Hit@k; action recommendation accuracy | P0 |
| AT-E5.6 | `hipporag_style_ppr_rca` | memory_graph_rag | PPR over KG memory | Answer faithfulness; root-cause Hit@k; action recommendation accuracy | P1 |
| AT-E5.7 | `agentic_kg_rca` | llm_agent | tool calls to graph search and case retrieval | Answer faithfulness; root-cause Hit@k; action recommendation accuracy | P0 |

### proposed_fusion_variants

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E6.1 | `late_fusion_detector_kg` | proposed_or_ablation | core component | Root-cause Hit@k; trace path F1; recommendation acceptability | P0 |
| AT-E6.2 | `early_fusion_kg_regularized_detector` | proposed_or_ablation | core component | Root-cause Hit@k; trace path F1; recommendation acceptability | P0 |
| AT-E6.3 | `plm_aligned_event_to_kg_mapper` | proposed_or_ablation | core component | Root-cause Hit@k; trace path F1; recommendation acceptability | P0 |
| AT-E6.4 | `llm_path_adjudicator` | proposed_or_ablation | core component | Root-cause Hit@k; trace path F1; recommendation acceptability | P0 |
| AT-E6.5 | `kg_counterfactual_verifier` | proposed_or_ablation | core component | Root-cause Hit@k; trace path F1; recommendation acceptability | P0 |
| AT-E6.6 | `full_plm_llm_kg_traceability` | proposed_or_ablation | core component | Root-cause Hit@k; trace path F1; recommendation acceptability | P0 |

### component_ablation_and_sanity_checks

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E7.1 | `no_mechanism_kg` | ablation | varies_by_ablation | Trace path F1; unsupported cause rate; hard-negative accuracy | P0 |
| AT-E7.2 | `no_plm_alignment` | ablation | varies_by_ablation | Trace path F1; unsupported cause rate; hard-negative accuracy | P0 |
| AT-E7.3 | `no_llm_adjudication` | ablation | varies_by_ablation | Trace path F1; unsupported cause rate; hard-negative accuracy | P0 |
| AT-E7.4 | `no_hard_negative_guard` | ablation | varies_by_ablation | Trace path F1; unsupported cause rate; hard-negative accuracy | P0 |
| AT-E7.5 | `no_temporal_gate` | ablation | varies_by_ablation | Trace path F1; unsupported cause rate; hard-negative accuracy | P0 |
| AT-E7.6 | `no_evidence_span` | ablation | varies_by_ablation | Trace path F1; unsupported cause rate; hard-negative accuracy | P0 |
| AT-E7.7 | `randomized_kg_edges` | ablation | varies_by_ablation | Trace path F1; unsupported cause rate; hard-negative accuracy | P0 |

### low_resource_transfer_and_robustness

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E8.1 | `label_budget_curve` | robustness_protocol | fixed_or_incrementally_updated_kg | Area under low-resource curve; transfer Hit@k; robustness degradation | P1 |
| AT-E8.2 | `new_steel_grade_transfer` | robustness_protocol | fixed_or_incrementally_updated_kg | Area under low-resource curve; transfer Hit@k; robustness degradation | P1 |
| AT-E8.3 | `process_stage_transfer` | robustness_protocol | fixed_or_incrementally_updated_kg | Area under low-resource curve; transfer Hit@k; robustness degradation | P1 |
| AT-E8.4 | `missing_sensor_stress` | robustness_protocol | fixed_or_incrementally_updated_kg | Area under low-resource curve; transfer Hit@k; robustness degradation | P1 |
| AT-E8.5 | `noisy_weak_label_stress` | robustness_protocol | fixed_or_incrementally_updated_kg | Area under low-resource curve; transfer Hit@k; robustness degradation | P1 |
| AT-E8.6 | `time_shift_stress` | robustness_protocol | fixed_or_incrementally_updated_kg | Area under low-resource curve; transfer Hit@k; robustness degradation | P1 |

### human_and_operational_evaluation

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E9.1 | `blind_expert_pairwise_ranking` | human_evaluation | shown_as_path_and_evidence | expert acceptability; diagnosis time; recommendation usefulness | P1 |
| AT-E9.2 | `trace_path_acceptability_audit` | human_evaluation | shown_as_path_and_evidence | expert acceptability; diagnosis time; recommendation usefulness | P1 |
| AT-E9.3 | `action_suggestion_audit` | human_evaluation | shown_as_path_and_evidence | expert acceptability; diagnosis time; recommendation usefulness | P1 |
| AT-E9.4 | `operator_time_to_diagnosis` | human_evaluation | shown_as_path_and_evidence | expert acceptability; diagnosis time; recommendation usefulness | P1 |

### cost_safety_and_online_readiness

| ID | Method | Baseline family | KG usage | Primary metrics | Priority |
|---|---|---|---|---|---|
| AT-E10.1 | `latency_token_budget` | deployment_readiness | audited_or_incremental_kg | latency; token/record; unsupported output rate | P1 |
| AT-E10.2 | `incremental_kg_update` | deployment_readiness | audited_or_incremental_kg | latency; token/record; unsupported output rate | P1 |
| AT-E10.3 | `adversarial_hard_negative_cases` | deployment_readiness | audited_or_incremental_kg | latency; token/record; unsupported output rate | P1 |
| AT-E10.4 | `evidence_faithfulness_check` | deployment_readiness | audited_or_incremental_kg | latency; token/record; unsupported output rate | P1 |

## Recommended Execution Order

1. Build a small reviewed traceability benchmark from Baosteel weak labels: defect type, top process observations, root-cause group, accepted trace path, recommended action.
2. Run AT-E1 and AT-E2 to establish non-KG and detector backbone baselines.
3. Run AT-E3 and AT-E4 to compare causal RCA and KG reasoning methods.
4. Run AT-E5 to compare LLM-only, text RAG, GraphRAG, LightRAG-style, HippoRAG-style, and agentic KG RCA.
5. Run AT-E6 and AT-E7 to prove the proposed PLM-LLM-KG fusion and component necessity.
6. Run AT-E8 to show low-resource and cross-condition robustness.
7. Run AT-E9 and AT-E10 only after automatic metrics are stable, because they require expert time and deployment-style measurements.

## Core Metrics

- Detection: AUROC, AUPRC, anomaly F1.
- Localization: root-cause Hit@1/3/5, MRR, NDCG.
- Traceability: trace path F1, path hit rate, explanation completeness, causal direction accuracy.
- Faithfulness: unsupported edge rate, evidence span coverage, hallucination rate, hard-negative accuracy.
- Utility: expert acceptability, recommendation usefulness, diagnosis time reduction.
- Cost: latency, token/record, graph update time, memory footprint.

## Paper-Strength Claims Enabled

- The mechanism KG improves anomaly traceability beyond feature attribution and case retrieval.
- PLM alignment is useful because it maps noisy event text and feature names to mechanism nodes.
- LLM prompt-atom adjudication is useful because it rejects plausible but unsupported trace paths.
- Graph reasoning is useful because it converts extracted mechanism knowledge into causal paths and optimization suggestions.
- The system remains robust under low labels, unseen conditions, missing sensors, and noisy weak labels.

## Reference Anchors

- GraphRAG and graph-enhanced retrieval motivate graph-based retrieval and generation baselines.
- LightRAG motivates dual-level graph/vector retrieval and incremental update baselines.
- HippoRAG motivates PPR-style KG memory retrieval baselines.
- TranAD, MTAD-GAT, and GDN motivate strong multivariate time-series anomaly backbones.
- PyRCA, neural Granger RCA, counterfactual RCA, and DoWhy motivate causal RCA baselines.
