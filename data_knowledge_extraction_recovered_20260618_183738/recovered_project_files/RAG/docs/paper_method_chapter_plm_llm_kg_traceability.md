# Method: PLM-LLM-KG Fusion for Mechanism-Level Knowledge Extraction and Anomaly Traceability

## 1. Problem Definition

This study targets mechanism-level knowledge extraction for continuous-casting quality analysis and its downstream use in anomaly traceability. Given technical mechanism text, weakly labeled process observations, and a mechanism knowledge graph, the goal is to construct an evidence-backed traceability model that returns:

- candidate root-cause categories,
- mechanism trace paths,
- supporting evidence,
- and recommended process checks or actions.

The task is different from direct production-log classification. The mechanism KG is first extracted from mechanism text and expert rules, then attached to downstream anomaly traceability as an explanation and reasoning layer.

## 2. Overall Framework

The proposed framework contains four modules:

1. **Mechanism knowledge extraction**: extract entities and relations from mechanism text, including nested entities, implicit causal relations, and hard-negative no-relation pairs.
2. **PLM-assisted prompt atom selection**: use a lightweight PLM to recommend prompt atoms and candidate spans, reducing repeated LLM calls and improving constraint consistency.
3. **LLM adjudication and KG construction**: use structured prompts to verify entity boundaries, relation direction, evidence spans, and schema constraints.
4. **KG-enhanced anomaly traceability**: align process observations to KG nodes, retrieve mechanism paths, and rerank root-cause candidates with explanation quality.

The fusion is not a loose cascade. The PLM supplies low-cost local signals, the LLM performs schema-aware adjudication, and the KG constrains the downstream traceability path.

## 3. Mechanism Knowledge Graph Construction

The mechanism KG is represented as:

\[
G=(V,E)
\]

where each node \(v \in V\) belongs to a typed schema, including `ProcessParameter`, `EquipmentState`, `MaterialState`, `DefectMechanism`, `QualityDefect`, `ControlAction`, and `ProcessStage`. Each relation \(e \in E\) is selected from a controlled relation set:

\[
R=\{cause, affect, increase\_risk\_of, indicates, improve, suppress, located\_at\}
\]

Each extracted relation stores:

- head and tail entity,
- relation type,
- direction,
- evidence span,
- confidence,
- prompt atoms used during extraction,
- and review state.

This design ensures that downstream traceability does not only output a label, but also returns a reproducible mechanism path.

## 4. PLM-Assisted Prompt Atom Recommendation

The PLM is used as a lightweight local selector rather than as the final extractor. For each input sentence or case description, the PLM estimates which prompt atoms are needed:

\[
A(x)=\{a_1,a_2,\dots,a_k\}
\]

where each atom corresponds to one extraction constraint, such as:

- evidence-span grounding,
- mechanism-chain constraint,
- relation-direction constraint,
- schema-type constraint,
- hard-negative verification,
- nested-entity boundary preservation.

The selected prompt atoms are then injected into the LLM adjudication prompt. This reduces token consumption because the LLM receives only the constraints relevant to the current sample, while preserving the LLM's flexibility for difficult cases.

The PLM is therefore responsible for:

- candidate span proposal,
- prompt atom recommendation,
- low-cost filtering of easy negative pairs,
- and routing samples to LLM adjudication only when needed.

## 5. LLM-Based Structured Adjudication

The LLM performs constrained verification rather than unconstrained generation. For each candidate entity or relation, the LLM must output a structured record:

```json
{
  "decision": "accept/reject/revise",
  "entity_or_relation": "...",
  "schema_type": "...",
  "evidence_span": "...",
  "direction": "head_to_tail",
  "reason": "..."
}
```

The adjudication step is guided by prompt atoms recommended by the PLM. A candidate relation is accepted only when:

1. the head and tail entities match the schema,
2. the direction is supported by the evidence span,
3. the relation belongs to the controlled relation set,
4. no hard-negative cue invalidates the relation.

This makes the LLM part of a structured extraction pipeline rather than an open-ended generator.

## 6. KG-Enhanced Anomaly Traceability

For a downstream anomaly event \(q\), the system extracts feature tokens, defect tokens, process-stage tokens, and candidate root-cause labels. Each candidate label \(y\) receives a score from four sources:

\[
S(y|q)=\lambda_1 S_{PLM}(y|q)+\lambda_2 S_{group}(y|q)+\lambda_3 S_{anchor}(y|q)+\lambda_4 S_{KG}(y|q)
\]

where:

- \(S_{PLM}\) is the feature-name or local classifier score,
- \(S_{group}\) is the feature-group prior,
- \(S_{anchor}\) is the mechanism anchor matching score,
- \(S_{KG}\) is the graph-path reasoning score.

The final method uses an explanation-aware reranker:

\[
S_{final}(y|q)=S(y|q)+\alpha Q(p_y)
\]

where \(p_y\) is the best KG trace path for candidate \(y\), and \(Q(p_y)\) measures whether the path has evidence, valid causal relations, feature overlap, and label-mechanism overlap.

## 7. Trace Path Quality

For each returned path, the system computes a path-quality proxy:

\[
Q(p)=\frac{1}{5}(I_{evidence}+I_{relation}+I_{feature}+I_{label}+I_{causal})
\]

where:

- \(I_{evidence}\): all path edges have textual evidence,
- \(I_{relation}\): all relations belong to traceability-valid relation types,
- \(I_{feature}\): at least one path node overlaps with observed features,
- \(I_{label}\): at least one path node overlaps with the candidate root cause,
- \(I_{causal}\): the path contains causal or risk-increasing semantics.

The paper-demo experiment reports explanation coverage, average path quality, and faithful path rate in addition to Hit@k and Macro F1.

## 8. Integration With The Anomaly Traceability System

The mechanism KG is integrated into the anomaly traceability system through an adapter layer:

- adapter source: `溯源系统/src/mechanism_kg_traceability_adapter.py`
- command entry: `溯源系统/integrate_mechanism_kg.py`
- generated rule pack: `溯源系统/outputs/mkg_adapter/mechanism_traceability_rules.json`
- generated Neo4j import script: `溯源系统/outputs/mkg_adapter/mechanism_traceability_seed.cypher`

The adapter converts mechanism KG edges into traceability rules:

```json
{
  "cause": "nonuniform shell growth",
  "defect": "surface crack risk",
  "solution": "Inspect and suppress upstream factor: nonuniform shell growth",
  "relation": "increase_risk_of",
  "confidence": 0.78,
  "evidence": "nonuniform shell growth increases risk of surface crack risk."
}
```

In the current run, the adapter exports 535 mechanism traceability rules. These rules can be consumed as JSON by the traceability service or imported into Neo4j through the generated Cypher file.

## 9. Experimental Design

The paper-demo experiment contains four leakage-controlled settings:

| Setting | Description |
|---|---|
| `full_weak_label_masked_text` | full weak-label test set with label text masked |
| `balanced_label_masked_text` | balanced subset with label text masked |
| `balanced_group_only` | feature names masked, only feature groups retained |
| `balanced_feature_anonymized` | both feature names and groups masked |

The compared methods include:

- label-prior majority,
- feature-group prior,
- feature-name naive Bayes,
- KG anchor reasoning,
- KG path reasoning,
- score fusion,
- proposed explainable reranking.

On the balanced label-masked setting, `kg_path_reasoning` reaches 0.8478 explanation coverage and 0.7506 average path quality. The proposed explainable reranker keeps the weak-label Hit@1 at 1.0000 while increasing explanation coverage to 0.5579 and path quality to 0.5255. These results show that the KG contributes an explanation layer beyond feature-only classification.

## 10. Technical Precheck And Expert Audit

A blinded audit file is generated for human review:

- `outputs/traceability_paper_evidence_pack/expert_audit_blind.csv`

To support internal debugging, an assistant technical precheck was also produced:

- `outputs/traceability_assistant_precheck/assistant_technical_audit.csv`
- scored evidence pack: `outputs/tace_ai_pack`

The assistant precheck is not independent expert validation. It uses weak-label consistency and path-quality heuristics to identify likely failure modes. The current precheck gives:

| Dimension | Mean Score | Usable Acceptance |
|---|---:|---:|
| Root-cause correctness | 1.0000 | 1.0000 |
| Trace-path plausibility | 0.2250 | 0.2250 |
| Action usefulness | 0.2250 | 0.2250 |

This indicates that the current system can rank weak-label root causes, but its trace paths and action recommendations still require stronger feature-to-KG alignment and human review before final paper claims.

## 11. Methodological Claim

The proposed method improves industrial knowledge extraction and anomaly traceability by combining:

- PLM efficiency for local candidate selection and prompt atom recommendation,
- LLM flexibility for schema-aware adjudication,
- and KG reasoning for evidence-backed root-cause paths.

The central contribution is not merely higher weak-label classification accuracy. The main value is a traceable and auditable reasoning chain from abnormal process observations to mechanism paths and process actions.

## 12. Current Limitation

The current weak-label experiments are sufficient for a paper-level method demonstration, but not sufficient for a final production root-cause claim. The next required step is independent expert review of the blinded audit file and targeted optimization of low-quality trace paths.
