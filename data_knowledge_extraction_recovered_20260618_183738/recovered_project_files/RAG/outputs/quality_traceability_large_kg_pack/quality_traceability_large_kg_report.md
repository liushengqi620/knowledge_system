# Quality Traceability Large KG Pack

## Scope

This pack defines a large-KG structure that can later absorb quality-traceability instance data. The current mechanism extraction experiment does not use processed Baosteel production rows as its primary source.

## KG Layers

- `mechanism`: Text-extracted mechanism entities, relations, chains, and control actions.
- `instance`: Future production batches/events/observations attached to the mechanism graph.
- `evidence`: Source text, extraction confidence, prompt atoms, adjudication, and review metadata.
- `application`: Quality traceability queries, paths, warnings, and recommended actions.

## Seed Graph Scale

- Schema nodes: 16
- Schema edges: 11
- Mechanism nodes: 3554
- Mechanism edges: 1777
- Total nodes: 3570
- Total edges: 1788

## Extraction Metrics

| Method | Entity F1 | Relation F1 | Triple F1 | Hallucination Rate | Hard Negative Accuracy |
|---|---:|---:|---:|---:|---:|
| `rule_based` | 0.0443 | 0.0056 | 0.0056 | 0.8333 | 1.0 |
| `plm_candidate_proxy` | 1.0 | 0.9426 | 0.9426 | 0.1086 | 0.0851 |
| `proposed_atom_adjudication_proxy` | 1.0 | 1.0 | 1.0 | 0.0 | 1.0 |

## Evidence Summary

- Best seed method: `proposed_atom_adjudication_proxy`
- Proposed vs candidate Triple F1 delta: `0.0574`
- Proposed vs candidate hallucination-rate reduction: `0.1086`

## Extraction Experiment Protocol

| ID | Track | Status | Primary Metrics |
|---|---|---|---|
| `QKG-E0` | completed_seed_evidence | completed_seed_proxy | Entity F1; Relation F1; Triple F1; Hallucination Rate; Hard Negative Accuracy |
| `QKG-E1` | main_extraction_effectiveness | planned_paper_scale | Entity F1; Relation F1; Triple F1; Evidence F1; Direction Accuracy |
| `QKG-E2` | low_resource_extraction | planned_paper_scale | Triple F1; low-resource area under curve; Token/record; Time/record |
| `QKG-E3` | plm_prompt_fusion_ablation | planned_paper_scale | Triple F1; hallucination rate; LLM call precision; Token/record |
| `QKG-E4` | hard_negative_and_hallucination | planned_paper_scale | Hard Negative Accuracy; Unsupported Triple Rate; Hallucination Rate |
| `QKG-E5` | graph_level_quality | planned_paper_scale | node duplicate rate; relation conflict rate; mechanism-chain completeness; expert acceptability |
| `QKG-E6` | traceability_attachment_validation | planned_downstream_validation | trace path hit rate; explanation completeness; expert acceptability; case retrieval precision |
| `QKG-E7` | frontier_baseline_comparison | planned_paper_scale | Entity F1; Relation F1; Triple F1; Evidence F1; Invalid Output Rate |

## Downstream Traceability Hook

- Existing Baosteel instance pool records: `104436`
- Position: downstream instance-layer attachment and application validation only.

## Required Paper-Scale Experiments

1. Replace generated seed data with a document-split corpus from papers/manuals/expert rules.
2. Replace deterministic proxy candidate generation with real PLM NER/RE/evidence models.
3. Replace deterministic proxy adjudication with a real constrained LLM backend.
4. Report main effectiveness, low-resource, prompt-atom ablation, PLM role ablation, and graph-level evaluation.
5. Use Baosteel or other production data only after mechanism KG extraction, as instance-layer traceability validation.
