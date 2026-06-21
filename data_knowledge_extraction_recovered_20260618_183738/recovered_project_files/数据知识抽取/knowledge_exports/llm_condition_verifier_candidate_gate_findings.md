# LLM Expert-Condition Verifier Candidate-Gate Findings

Date: 2026-06-20

## Implementation Changes

- The runner now reads CSV files through the long-path-safe `_fs_path` helper.
- `load_knowledge_graph_prior(mode="none")` can read LLM expert-condition verifier metadata without loading expert edges as graph prior.
- Duplicate verifier hits from both `expert_edge_id` and `(source, target)` matching are deduplicated.
- Class-conditioned evidence no longer replaces algorithmic evidence support during candidate admission; both supports are fused by `max`.
- LLM verifier application is split into:
  - `candidate_gate`: main branch. It only recalibrates existing data-supported algorithmic candidate edges.
  - `class_evidence`: ablation branch. It injects verifier evidence into class/path evidence and may trigger the class router.
- The ablation matrix now treats `a4_llm_expert_condition_verifier` as `candidate_gate` with `evidence_prior_mode=none`, and keeps `a5_weak_class_condition_verifier` as the class-evidence ablation.

## SKAB Smoke Evidence

All runs below use the live SKAB verifier metadata, CPU, `hidden_dim=16`, `window_size=16`, `max_rows_per_split=400`, `epochs=1`, and seeds `41,42,43`.

| Branch | Seed 41 Macro-F1 | Seed 42 Macro-F1 | Seed 43 Macro-F1 | Mean Macro-F1 |
|---|---:|---:|---:|---:|
| A0 algorithmic only | 0.4811 | 0.5916 | 0.5576 | 0.5434 |
| A4 candidate gate | 0.4811 | 0.5940 | 0.5576 | 0.5442 |

Candidate-gate diagnostics:

- Seed 41: `adjusted_edges=2`, no metric change.
- Seed 42: `adjusted_edges=3`, Macro-F1 improves from `0.5916` to `0.5940`.
- Seed 43: `adjusted_edges=1`, no metric change.

Earlier class-evidence verifier smoke was unstable:

- Metadata-only `class_evidence` improved seed 42 slightly after evidence-support fusion, but decreased mean performance across seeds.
- Expert-candidate-plus-verifier was worse, confirming that expert/LLM should not enter as early graph candidates for SKAB.

## Interpretation

The current LLM verifier evidence is safe after moving to candidate-gate mode, but its effect is too small because only 1-3 existing candidate edges overlap the reviewed LLM verifier records. This supports the paper design direction, but not yet a strong performance claim.

Next optimization should increase verifier coverage and data overlap rather than increasing verifier weight:

- Generate more reviewed verifier records per dataset/class and require overlap with algorithmic edge-pool candidates.
- Add a validation-gain admission layer so verifier-adjusted candidates are retained only when train-validation proxy improves.
- Keep independent LLM edges and class-evidence verifier as negative/auxiliary ablations, not the main branch.
- For SKAB and C-MAPSS SOTA work, prioritize stronger algorithmic edge discovery and temporal representation; use LLM/expert evidence as reliability certification and explanation, not as a primary classifier.
