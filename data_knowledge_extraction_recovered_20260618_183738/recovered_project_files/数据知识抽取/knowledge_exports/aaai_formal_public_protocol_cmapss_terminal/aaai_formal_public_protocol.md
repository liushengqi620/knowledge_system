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
| cmapss_original_rul_anchor | cmapss | C-MAPSS original RUL protocol | rul_rmse | formal_required | 3/3 | `'C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe' -B 'Scripts\run_public_ms_gse_rpf_experiment.py' --ready-root knowledge_exports/public_benchmark_ready --dataset cmapss --seeds 42,43,44 --output-dir 'knowledge_exports\aaai_formal_public_runs\cmapss_original_rul_terminal_anchor_w48_e20' --device cuda --variant full --cmapss-target rul --hidden-dim 64 --window-size 48 --max-rows-per-split 12000 --epochs 20 --batch-size 256 --graph-top-k 4 --max-paths 16 --forecast-weight 0.10 --graph-weight 0.02 --health-aux-weight 0.20 --health-rul-cap 125 --evidence-prior-mode none --prior-strength 0` |
| cmapss_rul_direct_regime_tempmix | cmapss | C-MAPSS RUL enhanced backbone | rul_rmse | formal_required_for_cmapss_claim | 3/3 | `'C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe' -B 'Scripts\run_public_ms_gse_rpf_experiment.py' --ready-root knowledge_exports/public_benchmark_ready --dataset cmapss --seeds 42,43,44 --output-dir 'knowledge_exports\aaai_formal_public_runs\cmapss_rul_direct_regime_tempmix_w80_e20' --device cuda --variant full --cmapss-target rul --hidden-dim 64 --window-size 80 --max-rows-per-split 12000 --epochs 20 --batch-size 256 --graph-top-k 4 --max-paths 16 --forecast-weight 0.10 --graph-weight 0.02 --health-aux-weight 0.20 --rul-loss-weight 1.0 --health-rul-cap 125 --use-regime-prototype-residuals --regime-prototype-k 6 --regime-healthy-stage-max 0 --use-temporal-mixer --temporal-mixer-depth 3 --evidence-prior-mode none --prior-strength 0` |

## Current Status

- cmapss_original_rul_anchor: complete=True, missing=[], rul_rmse_mean=31.2345.
- cmapss_rul_direct_regime_tempmix: complete=True, missing=[], rul_rmse_mean=23.7100.
