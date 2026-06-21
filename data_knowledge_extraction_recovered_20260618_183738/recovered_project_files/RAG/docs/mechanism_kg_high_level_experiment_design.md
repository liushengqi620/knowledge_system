# Mechanism-Layer Knowledge Graph Extraction: High-Level Experiment Design

## 1. Correct Scope

This part of the project studies mechanism-layer knowledge graph extraction.
It does not use processed Baosteel production records as the main data source.

Correct data boundary:

| Layer | Data Source | Use in This Experiment |
|---|---|---|
| Mechanism layer | papers, process manuals, expert rules, defect mechanism reports | primary source |
| Instance layer | processed Baosteel production and traceability records | not used |
| Application layer | Baosteel quality traceability scenarios | downstream validation only |

The target output is a mechanism knowledge graph describing how process
parameters, equipment states, material states, defect mechanisms, quality
defects, process stages, and control actions are connected.

## 2. Paper-Level Claim

Main claim:

```text
A PLM-guided prompt-atom adjudication framework improves low-resource
mechanism-layer knowledge graph extraction by using PLM models for stable
candidate generation, uncertainty estimation, evidence-window selection, and
prompt-atom routing, while using LLMs only for constrained adjudication of
high-risk candidates.
```

This is stronger than a token-saving claim. The PLM is not just a cheaper LLM
replacement. It controls which candidate triples are worth adjudicating, which
evidence span should be shown, and which prompt constraints should be activated.

## 3. Task Definition

Given a sentence or paragraph from mechanism-level industrial documents,
extract:

```text
entities + relations + relation direction + evidence span
```

Each valid relation is represented as:

```text
(head entity, relation type, tail entity, evidence span, source document)
```

Unsupported but plausible triples must be rejected. This is essential because
mechanism-layer texts often contain nearby entities without stating a real
causal or control relation.

## 4. Mechanism KG Schema

### Entity Types

| Entity Type | Meaning | Examples |
|---|---|---|
| `ProcessParameter` | process variable or operating parameter | casting speed, superheat, secondary cooling intensity |
| `EquipmentState` | equipment condition or operating state | mold level fluctuation, stopper opening abnormality |
| `MaterialState` | steel, slag, inclusion, solidification, or thermal state | slag entrapment, uneven solidification |
| `DefectMechanism` | intermediate physical mechanism | lubrication failure, heat transfer imbalance |
| `QualityDefect` | final or observed quality defect | longitudinal crack, surface crack, inclusion defect |
| `ControlAction` | intervention, adjustment, or prevention action | reduce casting speed, stabilize mold level |
| `ProcessStage` | process location or stage | tundish, mold, secondary cooling zone |

### Relation Types

| Relation Type | Meaning | Direction |
|---|---|---|
| `cause` | one state/mechanism directly causes another | cause -> effect |
| `affect` | influence relation without strict causality | factor -> affected object |
| `increase_risk_of` | raises probability of defect or mechanism | risk factor -> risk target |
| `suppress` | inhibits or reduces risk/mechanism | action/state -> inhibited target |
| `improve` | improves process state or quality | action -> improved target |
| `located_at` | entity occurs at process stage | entity -> stage |
| `controlled_by` | parameter/state is controlled by an action | controlled entity -> control action |
| `indicates` | observable indicator reflects hidden state/mechanism | indicator -> state/mechanism |
| `no_relation` | hard negative pair with no supported relation | undirected |

## 5. Proposed Method

The proposed framework is:

```text
mechanism text
  -> PLM candidate generator
  -> PLM uncertainty estimator
  -> prompt atom selector
  -> LLM constrained adjudicator
  -> graph canonicalization and conflict checking
```

### 5.1 PLM Candidate Generator

PLM modules:

| Module | Suggested Model | Output |
|---|---|---|
| NER | Chinese MacBERT/BERT + CRF | entity spans and entity types |
| RE | CasRel/TPLinker/GPLinker/pair classifier | candidate relation triples |
| Evidence scorer | cross-encoder or relation classifier head | evidence sentence/window score |
| Uncertainty estimator | entropy, margin, MC dropout, calibration head | uncertainty type |

PLM candidate example:

```json
{
  "candidate_id": "c17",
  "candidate_type": "relation",
  "payload": {
    "head_text": "结晶器液位波动",
    "relation_type": "cause",
    "tail_text": "保护渣卷入"
  },
  "confidence": 0.61,
  "uncertainty_type": "direction_conflict",
  "evidence_window": {"start": 0, "end": 31},
  "prompt_atoms": ["relation_direction", "evidence_span", "hallucination_guard"]
}
```

### 5.2 Prompt Atom Selector

Prompt atoms are functional prompt constraints. They should be selected per
candidate, not pasted into every prompt.

| PLM Signal | Recommended Prompt Atoms |
|---|---|
| low entity-boundary margin | `entity_boundary`, `evidence_span` |
| entity type confusion | `schema_constraint`, `entity_type_constraint` |
| relation type confusion | `schema_constraint`, `relation_type_constraint` |
| direction margin is low | `relation_direction`, `mechanism_chain` |
| evidence score is low | `evidence_span`, `hallucination_guard` |
| candidate is plausible but unsupported | `negative_relation`, `hallucination_guard` |
| multi-hop mechanism chain detected | `mechanism_chain`, `relation_direction` |

The first implementation can be rule-based. The paper-level version should
include a learned multi-label atom selector trained from adjudication outcomes.

### 5.3 LLM Constrained Adjudicator

The LLM should not perform free extraction in the proposed method. It receives:

- original evidence window
- one or a small batch of PLM candidates
- schema constraints
- PLM-selected prompt atoms
- required JSON output format

Allowed decisions:

```text
accept
reject
correct
add_missing
```

This makes LLM behavior auditable and allows LLM decisions to become training
signals for later PLM improvement.

## 6. Dataset Construction

### Source Corpus

Use mechanism-level textual sources:

| Source Type | Examples |
|---|---|
| Academic papers | continuous casting quality defects, mold flux, solidification, heat transfer |
| Technical manuals | casting process control, defect prevention, process parameter rules |
| Expert rules | cause-action rules, abnormal mechanism summaries |
| Defect analysis reports | mechanism descriptions and control recommendations |

Do not use processed Baosteel production rows in this part.

### Annotation Units

Each record should be one of:

- mechanism sentence
- relation-rich paragraph
- expert rule line
- defect mechanism description

Recommended gold scale:

| Split | Records | Use |
|---|---:|---|
| Train | 300-500 | PLM fine-tuning and learned atom selector |
| Dev | 100 | threshold, routing, and prompt-atom selection |
| Test | 200 | final held-out reporting |
| Unlabeled/weak pool | 1,000-5,000 | LLM adjudication, active learning, distillation |
| Hard negatives | 100-300 | hallucination suppression and no-relation evaluation |

Split by source document, not by sentence. A paper or manual section must not
appear in both training and test sets.

## 7. Experiments

### E1 Main Effectiveness

Compare:

| Method | Description |
|---|---|
| Rule-based | dictionaries and relation templates |
| PLM-only | BERT/MacBERT NER + supervised RE |
| LLM zero-shot | full extraction with no examples |
| LLM few-shot | full extraction with fixed examples |
| PLM -> LLM cascade | PLM candidates, LLM adjudication, no atom routing |
| Proposed | PLM candidates + uncertainty + prompt atoms + constrained LLM adjudication |

Metrics:

```text
Entity F1
Relation F1
Triple F1
Evidence F1
Direction Accuracy
Hallucination Rate
Invalid Output Rate
Token / record
Inference Time / record
```

Primary expected evidence:

```text
Proposed improves Relation/Triple F1 and reduces hallucination compared with
LLM-only and simple PLM -> LLM cascade, while using fewer prompt tokens than
full-prompt LLM extraction.
```

### E2 Low-Resource Study

Gold training budgets:

```text
50 / 100 / 300 / 500 records
```

Compare:

```text
PLM-only
LLM few-shot
PLM -> LLM cascade
Proposed
```

Report curves for:

```text
Triple F1
Relation F1
Hallucination Rate
LLM token cost
```

### E3 Prompt Atom Ablation

Compare atom policies:

| Setting | Meaning |
|---|---|
| No atom | only minimal schema and candidate |
| Full prompt | every atom used for every candidate |
| Random atom | same atom count as proposed, randomly selected |
| Rule atom | hand-written uncertainty-to-atom mapping |
| PLM-learned atom | learned multi-label selector |
| Proposed full | learned selector plus uncertainty routing |

This experiment is necessary to show that prompt atoms are not decorative.

### E4 PLM Role Ablation

Compare routing and candidate-selection policies:

| Setting | Meaning |
|---|---|
| Random router | random candidates sent to LLM |
| Rule router | keyword/schema rule routing |
| Confidence-only router | route by confidence threshold |
| Uncertainty router | route by calibrated uncertainty type |
| Proposed full router | uncertainty + evidence + atom recommendation |

This answers why PLM is needed instead of rules, random routing, or pure LLM.

### E5 Feedback and Distillation

Iterative setting:

```text
Round 0: initial PLM trained on gold train
Round 1: add LLM accepted/corrected/rejected candidates
Round 2: add second-pass adjudication feedback
```

Report:

```text
PLM-only F1 after each round
candidate precision/recall
LLM call rate
hard-negative rejection accuracy
```

### E6 Graph-Level Evaluation

Extraction metrics are not enough for a KG paper. Also report:

```text
node duplicate rate
relation conflict rate
direction conflict rate
isolated node ratio
mechanism chain completeness
expert acceptability score
```

Mechanism chain example:

```text
过热度偏低 -> 保护渣熔化不充分 -> 润滑不足 -> 表面裂纹风险
```

## 8. Publication-Quality Controls

Required controls:

- document-level split to avoid leakage
- held-out test set used once
- all prompt updates selected on dev only
- every table row generated by a recorded command
- three seeds for PLM training where applicable
- paired bootstrap or approximate randomization for main F1 comparisons
- manual audit of hallucination cases
- separate reporting for exact relation match and relaxed semantic match

## 9. Expected Paper Structure

Suggested structure:

```text
1. Introduction
2. Related Work
3. Mechanism-Layer KG Extraction Task
4. PLM-Guided Prompt-Atom Adjudication
5. Dataset and Annotation Protocol
6. Experimental Setup
7. Results and Analysis
8. Graph-Level Case Study
9. Limitations and Conclusion
```

The strongest paper contribution should be framed as:

```text
PLM-guided prompt atom routing converts open-ended LLM extraction into a
candidate-level constrained adjudication process, improving reliability and
cost-effectiveness for low-resource industrial mechanism KG construction.
```

