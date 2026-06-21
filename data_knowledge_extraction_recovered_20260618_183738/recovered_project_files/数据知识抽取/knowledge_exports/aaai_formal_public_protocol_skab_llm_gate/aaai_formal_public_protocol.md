# AAAI Formal Public Benchmark Protocol

This file separates formal paper runs from smoke/debug runs.

## Invariants

- SKAB paper results use window_size=48, hidden_dim=64, max_paths=16, epochs=40.
- C-MAPSS paper results use original RUL regression as the primary task.
- LLM verifier branches must not add independent graph edges to the main candidate set.
- Smoke runs are debugging evidence only and must not be mixed into final tables.

## Runs

| Name | Dataset | Role | Metric | Status | Completed | Command |
|---|---|---|---|---|---:|---|
| skab_llm_condition_candidate_gate | skab | LLM verifier reliability branch | macro_f1 | formal_required_for_llm_claim | 3/3 | `python -B 'Scripts\run_public_ms_gse_rpf_experiment.py' --ready-root knowledge_exports/public_benchmark_ready_llm_live_skab --dataset skab --seeds 42,43,44 --output-dir 'knowledge_exports\aaai_formal_public_runs\skab_llm_condition_candidate_gate_w48_e40' --device cpu --variant full --hidden-dim 64 --window-size 48 --max-rows-per-split 8000 --epochs 40 --batch-size 256 --graph-top-k 4 --max-paths 16 --forecast-weight 0.05 --graph-weight 0.02 --evidence-prior-mode none --prior-strength 0 --use-llm-expert-condition-verifier --llm-condition-verifier-target candidate_gate --llm-condition-verifier-weight 0.20 --llm-condition-verifier-min-data-support 0.05 --llm-condition-verifier-floor 0.10` |

## Current Status

- skab_llm_condition_candidate_gate: complete=True, missing=[], macro_f1_mean=0.8457.
