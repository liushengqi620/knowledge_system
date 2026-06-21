# Frontier Knowledge Extraction Baselines

This note records the frontier comparison groups added to the mechanism-layer KG experiment matrix.

## Baseline Groups

| Method ID | Role in This Project | Primary Reference |
|---|---|---|
| `gliner_zero_shot_ner_pair_re` | Generalist zero-shot NER candidate generator, followed by a lightweight pairwise RE classifier. | GLiNER, NAACL 2024: https://aclanthology.org/2024.naacl-long.300/ |
| `instructuie_instruction_tuned` | Instruction-tuned unified information extraction baseline. | InstructUIE: https://arxiv.org/abs/2304.08085 |
| `gollie_guideline_following` | Guideline-following zero-shot IE baseline using detailed annotation guidelines. | GoLLIE: https://arxiv.org/abs/2310.03668 |
| `code4uie_retrieval_code_generation` | Retrieval-augmented code-style schema extraction baseline. | Code4UIE: https://arxiv.org/abs/2311.02962 |
| `knowcoder_code_schema_uie` | Code-schema universal IE model baseline. | KnowCoder, ACL 2024: https://aclanthology.org/2024.acl-long.475/ |
| `deepke_llm_kgc_adapter` | External toolkit baseline for NER/RE/LLM KG construction adapters. | DeepKE, EMNLP 2022 Demo: https://aclanthology.org/2022.emnlp-demos.10/ |
| `constrained_json_llm` | LLM baseline with JSON schema or grammar-constrained structured output. | LLMs for Generative IE survey: https://arxiv.org/html/2312.17617v3 |
| `retrieval_augmented_schema_prompt` | Static LLM prompting strengthened with retrieved mechanism examples and schema snippets. | Code4UIE retrieval framing: https://arxiv.org/abs/2311.02962 |

## Why These Groups Matter

- Generalist NER baselines test whether compact universal extractors can replace domain PLM NER under low labels.
- Guideline-following IE tests whether annotation guidelines alone can give strong zero-shot extraction.
- Code-generation IE tests whether Python-class schema representations improve structured KG output.
- Constrained JSON generation tests whether format constraints reduce invalid outputs and hallucinated triples.
- Retrieval-augmented prompting tests whether similar mechanism examples improve evidence grounding.
- DeepKE provides a reproducible external toolkit anchor for reviewer-facing comparisons.

## Required Reporting

Every frontier baseline must report:

- exact model or toolkit version
- prompt/schema version
- adapter command
- train/dev/test split IDs
- random seed where applicable
- raw prediction file
- schema-validity rate
- Entity F1, Relation F1, Triple F1, Evidence F1
- hallucination rate and invalid output rate
