# AAAI Missing Ablation Execution Plan

- Status: complete
- Scope: Final AAAI ablation table gaps
- Seeds: 42, 43, 44
- Completion rule: A row becomes final-paper evidence only after matched three-seed metrics, copied raw artifacts, and a one-mechanism intervention audit are present.

## Guardrail

Commands are execution templates tied to existing experiment entry points. Before a long run, verify each flag is supported by the local parser; unsupported switches must be implemented as narrow experiment-branch flags rather than silently changing another mechanism.

## Closed Rows

- No counterfactual guard: complete_seed_level_evidence
  - Artifact: `knowledge_exports/aaai_missing_ablation_runs/skab_cf_subset_formal_summary/skab_cf_subset_formal_summary.json`
  - Note: Matched CF/no-CF three-seed SKAB formal summary is complete; the effect is non-differential and should be reported as a reliability/interpretability guard.
- No tail safety: complete_policy_replay
  - Artifact: `knowledge_exports/aaai_missing_ablation_runs/skab_tail_safety_policy_replay/skab_tail_safety_policy_replay.json`
  - Note: Matched H_k policy replay complete; no final-protocol admissions changed because low-tail safety was already satisfied.
- No complexity penalty: complete_seed_level_evidence
  - Artifact: `knowledge_exports/aaai_missing_ablation_runs/skab_no_complexity_full/mechanism_gate_ablation_matrix.json`
  - Note: Matched complexity-guarded/no-complexity three-seed rows are present.
