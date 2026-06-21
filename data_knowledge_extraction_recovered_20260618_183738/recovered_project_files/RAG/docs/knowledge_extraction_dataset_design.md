# Knowledge Extraction Dataset Design

## 1. Design Goal

The dataset should support a deeply fused PLM + prompt-engineering workflow, not only a final NER/RE benchmark.

The data must support these stages:

```text
raw industrial text
  -> PLM candidate generation
  -> prompt-atom compiler
  -> LLM constrained adjudication
  -> gold annotation / active learning
  -> PLM training and evaluation
```

Therefore, the raw dataset is designed as a multi-layer record. It keeps the original text stable, while allowing gold labels, weak labels, PLM candidates, and LLM adjudication decisions to be added without rewriting the source text.

## 2. File Layout

Recommended layout:

```text
data/
  mechanism_kg/
    raw_texts/
    annotations/
      train.jsonl
      dev.jsonl
      test.jsonl
    candidates/
    adjudication/
    graph/
  baosteel_knowledge_extraction/
    records.jsonl
    manifest.json
    preview.json
    splits/
      train.jsonl
      dev.jsonl
      test.jsonl
    plm/
      baosteel_plm_train_pool.json
      relation_type_id_map.json
  raw/
    continuous_casting_raw.jsonl
    electrochemistry_raw.jsonl
  annotations/
    continuous_casting_gold.jsonl
    electrochemistry_gold.jsonl
  candidates/
    continuous_casting_plm_candidates.jsonl
  adjudication/
    continuous_casting_llm_adjudication.jsonl
  splits/
    continuous_casting/
      train.json
      dev.json
      test.json
      low_resource_10.json
      low_resource_50.json
  schema/
    knowledge_extraction_record.schema.json
```

For schema smoke tests, a single JSON list can also be used:

```text
data/examples/continuous_casting_seed.json
```

The seed file is not the experiment dataset. For the current mechanism-layer KG experiment, the primary dataset should be built from papers, process manuals, expert rules, and defect mechanism reports.

The processed Baosteel dataset is not used in the current mechanism-layer experiment. It is reserved for later instance-layer graph attachment or quality-traceability application validation:

```powershell
python experiments/build_baosteel_knowledge_extraction_dataset.py --output-dir data/baosteel_knowledge_extraction --top-features 8
```

## 3. Core Record

Each raw record represents one stable extraction unit. The unit can be a sentence, paragraph, process note, alarm description, experiment sentence, or manually selected evidence window.

Required fields:

| Field | Type | Purpose |
|---|---|---|
| `record_id` | string | Stable unique ID. |
| `domain` | string | Domain such as `continuous_casting` or `electrochemistry`. |
| `language` | string | `zh`, `en`, or `mixed`. |
| `text` | string | Original text. Never rewrite after ID assignment. |
| `source` | object | Source metadata. |
| `task_scope` | array | Supported tasks for this record. |
| `annotation_status` | string | `raw`, `weak_labeled`, `gold_labeled`, `reviewed`. |

Recommended source fields:

| Field | Type | Purpose |
|---|---|---|
| `source_id` | string | Original document or system ID. |
| `source_type` | string | `process_log`, `paper`, `manual`, `alarm_report`, `lab_record`. |
| `process_stage` | string | Industrial stage, such as `tundish`, `mold`, or `heat_transfer`. |
| `timestamp` | string/null | ISO timestamp if available. |
| `split_group` | string/null | Group key to avoid leakage, such as heat ID, paper ID, run ID. |

## 4. Annotation Layers

### 4.1 Entities

Entities use character offsets in the exact `text` string.

Required fields:

| Field | Type | Purpose |
|---|---|---|
| `entity_id` | string | Local ID within the record. |
| `text` | string | Surface form. |
| `type` | string | Entity type. |
| `start` | integer | Inclusive char offset. |
| `end` | integer | Exclusive char offset. |
| `source` | string | `gold`, `plm_candidate`, `llm_candidate`, `weak_rule`. |
| `confidence` | number/null | Confidence for non-gold labels. |

Recommended continuous-casting entity types:

| Type | Meaning |
|---|---|
| `ProcessParameter` | Process variable, e.g. casting speed, mold level. |
| `EquipmentState` | Equipment or process state. |
| `QualityDefect` | Defect or abnormal quality outcome. |
| `MaterialState` | Slag, steel, powder, inclusion, or chemical state. |
| `Operation` | Control or corrective operation. |
| `ProductPart` | Slab, billet, strand, surface, corner. |
| `QualityIndicator` | Measured quality or risk index. |

Recommended electrochemistry entity types:

| Type | Meaning |
|---|---|
| `MATERIAL` | Material or compound. |
| `VALUE` | Measurement value. |
| `PROPERTY` | Capacity, voltage, conductivity, etc. |
| `CONDITION` | Test or synthesis condition. |

### 4.2 Relations

Relations connect entity IDs and must include evidence.

Required fields:

| Field | Type | Purpose |
|---|---|---|
| `relation_id` | string | Local ID within the record. |
| `type` | string | Relation type. |
| `head` | string | Source entity ID. |
| `tail` | string | Target entity ID. |
| `direction` | string | `head_to_tail`, `tail_to_head`, or `undirected`. |
| `evidence_span` | object | Character span supporting the relation. |
| `source` | string | `gold`, `plm_candidate`, `llm_candidate`, `weak_rule`. |
| `confidence` | number/null | Confidence for non-gold labels. |

Recommended continuous-casting relation types:

| Type | Meaning |
|---|---|
| `cause` | Cause-to-effect mechanism relation. |
| `affect` | Influence relation without strict causal claim. |
| `control` | Operation controls parameter/state. |
| `improve` | Corrective action improves defect/risk. |
| `located_at` | Defect/state located at process stage or product part. |
| `has_parameter` | Equipment or process stage has parameter. |
| `associated_with` | Weak association, not causal. |

Recommended electrochemistry relation types:

| Type | Meaning |
|---|---|
| `Voltage` | Material-value voltage relation. |
| `Capacity` | Material-value capacity relation. |
| `Coulombic Efficiency` | Material-value efficiency relation. |
| `Energy` | Material-value energy relation. |
| `Conductivity` | Material-value conductivity relation. |
| `no_relation` | Explicit hard negative. |

## 5. PLM Candidate Layer

PLM should not only output final labels. It should output structured candidate states that the prompt compiler can use.

Candidate fields:

| Field | Type | Purpose |
|---|---|---|
| `candidate_id` | string | Stable candidate ID. |
| `candidate_type` | string | `entity`, `relation`, or `evidence_window`. |
| `payload` | object | Entity span or relation pair. |
| `confidence` | number | PLM confidence. |
| `uncertainty_type` | string | `low_confidence`, `boundary_conflict`, `direction_conflict`, `schema_conflict`. |
| `evidence_window` | object | Text window sent to LLM. |
| `prompt_atoms` | array | Prompt atoms recommended by PLM. |

This layer is the key to deeper PLM + prompt fusion. PLM does not merely verify LLM output after the fact; it decides which candidates, windows, and prompt atoms the LLM will see.

## 6. LLM Adjudication Layer

LLM output should be stored as decisions over PLM candidates, not as uncontrolled free-form extraction.

Decision fields:

| Field | Type | Purpose |
|---|---|---|
| `candidate_id` | string | Candidate being judged. |
| `decision` | string | `accept`, `reject`, `correct`, `add_missing`. |
| `corrected_payload` | object/null | Corrected entity or relation. |
| `evidence_span` | object | Evidence used by LLM. |
| `reject_reason` | string/null | Required for rejected candidates. |
| `prompt_atoms_used` | array | Prompt atoms used in this decision. |
| `llm_model` | string | LLM model ID. |
| `llm_confidence` | number/null | Optional calibrated confidence. |

## 7. Split Rules

Use group-aware splitting to avoid leakage.

Recommended split keys:

- Industrial logs: heat ID, cast sequence ID, production date, plant line.
- Papers: paper ID or DOI.
- Experiment records: experiment batch ID.

Default split:

```text
train: 80%
dev:   10%
test:  10%
```

Low-resource subsets are sampled only from `train`:

```text
10% train labels
50% train labels
100% train labels
```

The test set must never be used for prompt atom updates, PLM threshold tuning, or LLM example selection.

## 8. Annotation Policy

### Entity Boundary

Use the shortest complete phrase that preserves technical meaning.

Good:

```text
结晶器液位波动
```

Bad:

```text
液位
```

unless the text only states `液位` and no modifier is present.

### Relation Direction

For mechanism relations, head should be the cause and tail should be the effect.

Example:

```text
保护渣熔化不均 -> cause -> 表面裂纹风险
```

### Evidence Requirement

Every gold relation must have an evidence span. If the relation is plausible but not stated or strongly implied in text, mark it as `associated_with` or reject it.

### Negative Examples

Include hard negatives:

- Same sentence, two entities, no valid relation.
- Reversed causal direction.
- Entity pair has plausible domain relation but no textual evidence.
- Relation type correct, but endpoint entity type illegal.

These examples are important for PLM hallucination suppression and LLM adjudication.

## 9. Minimum Dataset Size

For the first complete experiment:

| Split | Records | Notes |
|---|---:|---|
| Gold train | 300-500 | Enough for a small PLM verifier. |
| Gold dev | 50-100 | Threshold and prompt tuning only. |
| Gold test | 100-200 | Final reporting only. |
| Weak/LLM candidate pool | 1,000-5,000 | For active learning and distillation. |

If annotation budget is limited, prioritize relation-rich records instead of random sentences.

## 10. Conversion to Existing PLM Format

The current PLM matrix expects a JSON list with this minimal shape:

```json
{
  "id": "cc-0001",
  "text": "...",
  "ner": {
    "text": "...",
    "labels": ["O", "B-ProcessParameter"],
    "entities": [
      {"text": "...", "type": "...", "start": 0, "end": 2}
    ]
  },
  "re": {
    "text": "...",
    "entity_pairs": [[0, 2, 5, 8]],
    "relations": [0],
    "dependency_graph": {"nodes": [], "edges": []}
  }
}
```

The richer raw record should be converted into this minimal format for baseline PLM training. The richer format should remain the source of truth.

## 11. Mechanism-Layer KG Dataset

The primary dataset for the current research stage is a mechanism-layer text corpus. It should not be built from processed Baosteel production rows.

Input sources:

| Source | Role |
|---|---|
| Academic papers | Extract mechanism triples about process variables, material states, defect mechanisms, and quality defects. |
| Process manuals | Extract stable schema knowledge, control actions, and process-stage constraints. |
| Expert rules | Extract high-confidence causal/control relations and hard-negative constraints. |
| Defect mechanism reports | Extract relation-rich descriptions and mechanism chains. |

Generated outputs:

| Output | Purpose |
|---|---|
| `data/mechanism_kg/annotations/train.jsonl` | Gold training records for PLM fine-tuning and atom selector learning. |
| `data/mechanism_kg/annotations/dev.jsonl` | Development records for thresholds, routing, and prompt tuning. |
| `data/mechanism_kg/annotations/test.jsonl` | Held-out reporting set. |
| `data/mechanism_kg/candidates/*.jsonl` | PLM candidates, uncertainty states, and recommended prompt atoms. |
| `data/mechanism_kg/adjudication/*.jsonl` | LLM accept/reject/correct/add_missing decisions. |
| `data/mechanism_kg/graph/*.json` | Canonicalized mechanism graph nodes, relations, chains, and conflict reports. |

Recommended generated scale:

| Part | Records |
|---|---:|
| Gold train | 300-500 |
| Gold dev | 100 |
| Gold test | 200 |
| Weak/unlabeled mechanism text pool | 1,000-5,000 |
| Hard negative records | 100-300 |

Important label policy:

- Mechanism triples require textual evidence.
- Use `cause` only when the text states or strongly implies a cause-to-effect mechanism.
- Use `affect` when the text states influence but not strict causality.
- Use `no_relation` for plausible but unsupported pairs to suppress LLM hallucination.
- Split by source document to prevent leakage across train/dev/test.

## 12. Baosteel Dataset Position

The processed Baosteel dataset is useful, but it belongs to later instance-layer
or application-layer work:

```text
mechanism KG extracted from text
  -> attach production batches/events as instances
  -> run quality traceability or case-study validation
```

It should not be used as the primary dataset for the mechanism-layer extraction experiments.

## 13. Legacy Continuous-Casting Fixture

Keep `continuous_casting` because it is aligned with the existing FSDV-EAPA prompt atom design and remains useful as a small schema/prompt fixture.

Initial schema:

```text
Entity types:
  ProcessParameter
  EquipmentState
  QualityDefect
  MaterialState
  Operation
  ProductPart
  QualityIndicator

Relation types:
  cause
  affect
  control
  improve
  located_at
  has_parameter
  associated_with
  no_relation
```

Initial task definition:

```text
Given a continuous-casting text segment, extract process-relevant entities,
relations, relation direction, and evidence spans. Reject unsupported triples.
```
