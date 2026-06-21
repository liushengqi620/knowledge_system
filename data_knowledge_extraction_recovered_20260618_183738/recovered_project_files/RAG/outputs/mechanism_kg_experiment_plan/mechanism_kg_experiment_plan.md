# Mechanism KG Experiment Matrix

This matrix is for mechanism-layer knowledge graph extraction from papers, manuals, expert rules, and defect mechanism documents. It does not use processed Baosteel production data.

## Summary

- Total experiment rows: 47
- Tracks: feedback_distillation, frontier_extraction_baselines, graph_level_evaluation, low_resource, main_effectiveness, plm_role_ablation, prompt_atom_ablation
- Primary held-out dataset: `mechanism_text_gold_split_by_document`

## Tracks

### main_effectiveness

| ID | RQ | Method | Setting | Priority |
|---|---|---|---|---|
| E1.1 | RQ1 | `rule_based` | dictionary and pattern rules | P0 |
| E1.2 | RQ1 | `plm_only` | BERT/MacBERT NER + supervised RE | P0 |
| E1.3 | RQ1 | `llm_zero_shot` | zero-shot full extraction | P0 |
| E1.4 | RQ1 | `llm_few_shot` | few-shot full extraction | P0 |
| E1.5 | RQ1 | `plm_llm_cascade` | PLM candidates + LLM adjudication without atom routing | P0 |
| E1.6 | RQ1 | `proposed` | PLM-guided prompt-atom LLM adjudication | P0 |

### low_resource

| ID | RQ | Method | Setting | Priority |
|---|---|---|---|---|
| E2.50.1 | RQ2 | `plm_only` | 50 gold training records | P1 |
| E2.50.2 | RQ2 | `llm_few_shot` | 50 gold training records | P1 |
| E2.50.3 | RQ2 | `plm_llm_cascade` | 50 gold training records | P1 |
| E2.50.4 | RQ2 | `proposed` | 50 gold training records | P1 |
| E2.100.1 | RQ2 | `plm_only` | 100 gold training records | P0 |
| E2.100.2 | RQ2 | `llm_few_shot` | 100 gold training records | P0 |
| E2.100.3 | RQ2 | `plm_llm_cascade` | 100 gold training records | P0 |
| E2.100.4 | RQ2 | `proposed` | 100 gold training records | P0 |
| E2.300.1 | RQ2 | `plm_only` | 300 gold training records | P0 |
| E2.300.2 | RQ2 | `llm_few_shot` | 300 gold training records | P0 |
| E2.300.3 | RQ2 | `plm_llm_cascade` | 300 gold training records | P0 |
| E2.300.4 | RQ2 | `proposed` | 300 gold training records | P0 |
| E2.500.1 | RQ2 | `plm_only` | 500 gold training records | P1 |
| E2.500.2 | RQ2 | `llm_few_shot` | 500 gold training records | P1 |
| E2.500.3 | RQ2 | `plm_llm_cascade` | 500 gold training records | P1 |
| E2.500.4 | RQ2 | `proposed` | 500 gold training records | P1 |

### prompt_atom_ablation

| ID | RQ | Method | Setting | Priority |
|---|---|---|---|---|
| E3.1 | RQ3 | `no_atom` | minimal schema and candidate only | P0 |
| E3.2 | RQ3 | `full_prompt` | all atoms inserted for every candidate | P0 |
| E3.3 | RQ3 | `random_atom` | random atoms with same count as proposed | P0 |
| E3.4 | RQ3 | `rule_atom` | hand-written uncertainty-to-atom mapping | P0 |
| E3.5 | RQ3 | `plm_learned_atom` | learned multi-label atom selector | P0 |
| E3.6 | RQ3 | `proposed_full` | learned selector plus uncertainty routing | P0 |

### plm_role_ablation

| ID | RQ | Method | Setting | Priority |
|---|---|---|---|---|
| E4.1 | RQ4 | `random_router` | randomly route candidates to LLM | P1 |
| E4.2 | RQ4 | `rule_router` | keyword/schema rules decide LLM calls | P1 |
| E4.3 | RQ4 | `confidence_only_router` | single confidence threshold | P1 |
| E4.4 | RQ4 | `uncertainty_router` | calibrated uncertainty type controls routing | P1 |
| E4.5 | RQ4 | `proposed_full_router` | uncertainty + evidence + atom routing | P1 |

### feedback_distillation

| ID | RQ | Method | Setting | Priority |
|---|---|---|---|---|
| E5.1 | RQ5 | `round_0` | initial PLM trained only on gold train | P2 |
| E5.2 | RQ5 | `round_1` | add LLM accepted/corrected/rejected candidates | P2 |
| E5.3 | RQ5 | `round_2` | second feedback iteration | P2 |

### graph_level_evaluation

| ID | RQ | Method | Setting | Priority |
|---|---|---|---|---|
| E6.1 | RQ6 | `graph_exact` | strict graph assembly with exact surface forms | P1 |
| E6.2 | RQ6 | `graph_canonicalized` | canonicalized graph assembly with alias merging | P1 |
| E6.3 | RQ6 | `expert_audit` | manual expert audit of sampled triples and chains | P1 |

### frontier_extraction_baselines

| ID | RQ | Method | Setting | Priority |
|---|---|---|---|---|
| E7.1 | RQ7 | `gliner_zero_shot_ner_pair_re` | GLiNER-style generalist zero-shot NER plus a lightweight pairwise relation classifier | P0 |
| E7.2 | RQ7 | `instructuie_instruction_tuned` | instruction-tuned unified IE model with task-specific extraction instructions | P1 |
| E7.3 | RQ7 | `gollie_guideline_following` | guideline-following zero-shot IE model using detailed annotation guidelines | P0 |
| E7.4 | RQ7 | `code4uie_retrieval_code_generation` | retrieval-augmented code-style schema generation with similar examples | P0 |
| E7.5 | RQ7 | `knowcoder_code_schema_uie` | code-style universal IE model with schema library and schema-following training | P1 |
| E7.6 | RQ7 | `deepke_llm_kgc_adapter` | DeepKE-style toolkit baseline with NER/RE/LLM knowledge extraction adapters | P1 |
| E7.7 | RQ7 | `constrained_json_llm` | LLM extraction with JSON schema or grammar-constrained decoding | P1 |
| E7.8 | RQ7 | `retrieval_augmented_schema_prompt` | LLM prompt with retrieved mechanism examples and schema snippets | P1 |

## Recommended Execution Order

1. Build and validate the mechanism-text gold dataset with document-level splits.
2. Run E1 main effectiveness baselines.
3. Run E3 prompt-atom ablation using the best E1 PLM checkpoint.
4. Run E2 low-resource curves for 100 and 300 labels first, then 50 and 500.
5. Run E4 PLM role ablation after routing thresholds are selected on dev.
6. Run E6 graph-level evaluation on the best extractor output.
7. Run E5 feedback/distillation if time permits.

## Paper Evidence Gate

A result row is publishable only when the command, dataset split, seed, model checkpoint, prompt version, output file, and test metric source are recorded.
