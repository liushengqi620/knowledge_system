# AAAI Formal Public Benchmark Protocol

This file separates formal paper runs from smoke/debug runs.

## Invariants

- SKAB paper results use window_size=48, hidden_dim=64, max_paths=16, epochs=40.
- C-MAPSS paper results use original RUL regression with terminal test-unit evaluation as the primary task.
- LLM verifier branches must not add independent graph edges to the main candidate set.
- Smoke runs are debugging evidence only and must not be mixed into final tables.

## Runs

| Name | Dataset | Role | Metric | Status | Completed | Command |
|---|---|---|---|---|---:|---|
| skab_strong_anchor | skab | main SKAB anchor protocol | macro_f1 | formal_required | 3/3 | `'C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe' -B 'Scripts\run_public_ms_gse_rpf_experiment.py' --ready-root knowledge_exports/public_benchmark_ready --dataset skab --seeds 42,43,44 --output-dir 'C:\Users\CPILAB\Documents\xwechat_files\wxid_fn3terjpgaio22_c340\msg\file\2026-06\codex_recovery\data_knowledge_extraction_recovered_20260618_183738\recovered_project_files\数据知识抽取\knowledge_exports\aaai_formal_public_runs\skab_strong_anchor_w48_e40' --device cuda --variant full --hidden-dim 64 --window-size 48 --max-rows-per-split 8000 --epochs 40 --batch-size 256 --graph-top-k 4 --max-paths 16 --forecast-weight 0.05 --graph-weight 0.02 --evidence-prior-mode none --prior-strength 0` |
| skab_llm_condition_candidate_gate | skab | LLM verifier reliability branch | macro_f1 | formal_required_for_llm_claim | 3/3 | `'C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe' -B 'Scripts\run_public_ms_gse_rpf_experiment.py' --ready-root knowledge_exports/public_benchmark_ready_llm_live_skab --dataset skab --seeds 42,43,44 --output-dir 'C:\Users\CPILAB\Documents\xwechat_files\wxid_fn3terjpgaio22_c340\msg\file\2026-06\codex_recovery\data_knowledge_extraction_recovered_20260618_183738\recovered_project_files\数据知识抽取\knowledge_exports\aaai_formal_public_runs\skab_llm_condition_candidate_gate_valadm001_w005_c010_w48_e40' --device cuda --variant full --hidden-dim 64 --window-size 48 --max-rows-per-split 8000 --epochs 40 --batch-size 256 --graph-top-k 4 --max-paths 16 --forecast-weight 0.05 --graph-weight 0.02 --evidence-prior-mode none --prior-strength 0 --use-llm-expert-condition-verifier --llm-condition-verifier-target candidate_gate --llm-condition-verifier-weight 0.05 --llm-condition-verifier-min-data-support 0.05 --llm-condition-verifier-floor 0.10 --use-candidate-prior-admission --candidate-prior-admission-target proposal_feature --candidate-prior-admission-support-mode absolute --candidate-prior-admission-scale 0.50 --candidate-coverage-fraction 0.10 --use-llm-condition-verifier-validation-admission --llm-condition-verifier-min-val-gain 0.01` |

## Current Status

- skab_strong_anchor: complete=True, missing=[], macro_f1_mean=0.8193.
- skab_llm_condition_candidate_gate: complete=True, missing=[], macro_f1_mean=0.8209.
