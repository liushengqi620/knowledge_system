# LLM Condition Verifier Validation-Admission Findings

Date: 2026-06-20

## Status

The LLM verifier has been moved from an independent edge source to a conditional verifier over existing expert mechanism edges.
It now creates candidate path overlay only when all three conditions hold:

- the edge is an existing expert edge verified by the LLM condition verifier;
- the edge has train-only data support;
- the overlay passes validation-gain admission before deployment.

This keeps LLM evidence out of the final graph unless it is supported by data and validation behavior.

## SKAB Formal Evidence

Formal strong anchor:

| Branch | Seeds | Mean Macro-F1 | Status |
|---|---:|---:|---|
| `skab_strong_anchor_w48_e40` | 42, 43, 44 | 0.8457 | primary SKAB anchor |
| `skab_llm_condition_candidate_gate_valadm001_w005_c010_w48_e40` | 42, 43, 44 | 0.8308 | validation-admission/no-gain ablation |

Per-seed LLM verifier validation-admission:

| Seed | Test Macro-F1 | Validation Decision | Validation Gain |
|---:|---:|---|---:|
| 42 | 0.8406 | baseline | -0.0013 |
| 43 | 0.8204 | baseline | -0.0040 |
| 44 | 0.8314 | baseline | -0.0707 |

## Interpretation

The revised implementation fixes the earlier `missing_candidate_prior` failure: the verifier now constructs nonzero candidate overlays (`adjusted_edges=3`, `verified_expert_candidate_edges=3` in SKAB).
However, validation-gain admission rejects the overlay for all three formal SKAB seeds.

Therefore, the current LLM verifier should not be claimed as a performance-improving component on SKAB.
It is valid safety evidence for the paper story: unreliable language-derived mechanism evidence is admitted only when validation supports it, and otherwise the method blocks negative transfer.

## Next Method Step

To turn LLM evidence into a positive contribution, the verifier must become more condition-specific:

- match expert edges to operating regimes, residual states, and anomaly phases rather than only source-target pairs;
- use per-regime verifier features as path evidence instead of a global candidate overlay;
- require validation-gain admission at the regime/path level rather than at the whole-matrix level.
