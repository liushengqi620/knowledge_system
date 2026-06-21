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
| skab_strong_anchor | skab | main SKAB anchor protocol | macro_f1 | formal_required | 0/3 | `python -B 'Scripts\run_public_ms_gse_rpf_experiment.py' --ready-root knowledge_exports/public_benchmark_ready --dataset skab --seeds 42,43,44 --output-dir 'C:\Users\CPILAB\Documents\xwechat_files\wxid_fn3terjpgaio22_c340\msg\file\2026-06\codex_recovery\data_knowledge_extraction_recovered_20260618_183738\recovered_project_files\数据知识抽取\knowledge_exports\aaai_formal_public_runs\skab_strong_anchor_w48_e40' --device cpu --variant full --hidden-dim 64 --window-size 48 --max-rows-per-split 8000 --epochs 40 --batch-size 256 --graph-top-k 4 --max-paths 16 --forecast-weight 0.05 --graph-weight 0.02 --evidence-prior-mode none --prior-strength 0` |

## Current Status

- skab_strong_anchor: complete=False, missing=[42, 43, 44], macro_f1_mean=n/a.
