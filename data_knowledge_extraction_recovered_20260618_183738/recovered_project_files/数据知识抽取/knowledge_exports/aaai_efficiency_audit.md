# AAAI Efficiency Audit

- Status: `complete`

This audit separates measured efficiency evidence from legacy performance-only runs. Training time, inference throughput, and parameter count are read from seed-level JSON artifacts when available.

## Efficiency Table

| Dataset | Branch | Status | Runs | Metric | Params | Train seconds | Train samples/s | Test infer seconds | Test samples/s | Device | Paper use |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| SKAB | strong_anchor | measured | 3 | Macro-F1 0.8457 | 88716 | 340.54 | 940.6 | 2.6786 | 2988.7 | recorded-by-run | formal anomaly anchor efficiency |
| SKAB | llm_condition_candidate_gate | measured | 3 | Macro-F1 0.8457 | 88716 | 345.44 | 927.2 | 2.7298 | 2939.9 | recorded-by-run | formal LLM condition-verifier efficiency |
| C-MAPSS | original_rul_anchor | measured | 3 | RUL RMSE 31.2554 | 119183 | 62.84 | 3819.2 | 0.0732 | 9667.1 | recorded-by-run | terminal RUL anchor efficiency |
| C-MAPSS | anchorpath_bigru_cls020 | measured | 3 | RUL RMSE 20.4792 | 382162 | 147.46 | 1636.0 | 0.0872 | 8341.6 | recorded-by-run | terminal RUL proposed-branch efficiency |
| TEP | GDN20k:no_graph | measured | 3 | Target-F1 0.3293 | 17942 | 0.47 | 136393.4 | 0.0220 | 586309.7 | cuda | TEP sequence graph efficiency |
| TEP | GDN20k:residual_gated_lagged | measured | 3 | Target-F1 0.4077 | 35885 | 0.63 | 92543.4 | 0.0390 | 330096.4 | cuda | TEP sequence graph efficiency |
| TEP | MTADGAT20k:no_graph | measured | 3 | Target-F1 0.6339 | 92055 | 0.66 | 90087.9 | 0.0277 | 476639.1 | cuda | TEP sequence graph efficiency |
| TEP | MTADGAT20k:residual_gated_lagged | measured | 3 | Target-F1 0.6385 | 184111 | 1.07 | 53881.9 | 0.0505 | 254825.4 | cuda | TEP sequence graph efficiency |

## Missing Or Legacy Efficiency

- none

## Timed Rerun Commands

- `python Scripts/run_tep_sequence_graph_ablation.py --output knowledge_exports/tep_gdn_20k_e10_timed.json --model gdn --seeds 42,43,44 --max-rows 20000 --window-size 16 --hidden-dim 64 --epochs 10 --batch-size 512 --include-residual-gated --variants no_graph,residual_gated_lagged --resume --device auto`
- `python Scripts/run_tep_sequence_graph_ablation.py --output knowledge_exports/tep_mtad_20k_e10_timed.json --model mtad_gat --seeds 42,43,44 --max-rows 20000 --window-size 16 --hidden-dim 64 --epochs 10 --batch-size 512 --include-residual-gated --variants no_graph,residual_gated_lagged --resume --device auto`

## Notes

- Measured rows report values read from per-seed JSON artifacts.
- TEP GDN/MTAD full-budget efficiency is now read from timed rerun artifacts, not the legacy performance-only files.
- Smoke timing rows are omitted once full-budget timed artifacts are present.
