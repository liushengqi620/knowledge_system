# SKAB Strong-Protocol Recheck Findings

Date: 2026-06-20

## Why The Recent Smoke Scores Were Low

The recent verifier and algorithm-edge smoke runs used a small, non-final protocol:

- `window_size=16`
- `hidden_dim=16/32`
- `max_rows_per_split=400` or `2000`
- `epochs=1` or `5`
- extra algorithmic edge candidate admission in several variants

Those runs are useful for mechanism debugging, but they are not comparable with the earlier SKAB high-score evidence.

The earlier high-score SKAB setting uses a stronger temporal/path protocol:

- `window_size=48`
- `hidden_dim=64`
- `max_paths=16`
- about `8000/6530/8000` train/val/test samples
- `epochs=40`
- no algorithmic edge prior in the highest `prior-none` run

## Existing High-Score Evidence

Located evidence:

- `knowledge_exports/ms_gse_rpf/ms_gse_rpf_skab_anomaly_full_prior-none_seed42.json`
  - Macro-F1: `0.8682`
  - Balanced accuracy: `0.8665`
  - Positive precision: `0.8630`
  - Positive recall: `0.8311`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_validation_admission/.../selected_runs`
  - 3-seed mean Macro-F1 around `0.8307`
  - Max seed Macro-F1 `0.8507`

## Current-Code Recheck

Command family:

```text
run_public_ms_gse_rpf_experiment.py
  --dataset skab --variant full --seeds 42
  --hidden-dim 64 --window-size 48 --max-rows-per-split 8000
  --epochs 40 --batch-size 256
  --graph-top-k 4 --max-paths 16
  --forecast-weight 0.05 --graph-weight 0.02
  --evidence-prior-mode none --prior-strength 0
```

Current-code result:

- `knowledge_exports/skab_strong_protocol_recheck/current_full_w48_e40/...seed42.json`
  - Macro-F1: `0.8368`
  - Balanced accuracy: `0.8357`

This confirms the strong protocol is still far above the verifier smoke runs, but current code is below the older `0.8682` seed42 record. Treat the older high-score run as existing evidence, but re-run a formal 3-seed strong protocol before making final AAAI claims.

## Algorithmic Conclusions

- `window_size=48` is a core SKAB requirement; short-window smoke underestimates the model.
- `edge_pool`, `edge_sieve`, and `edge_guarded_lattice` candidate priors are not automatically beneficial for SKAB under the small smoke protocol.
- `temporal_mixer` did not change 1-epoch or 5-epoch SKAB smoke results.
- One-class posterior fusion is the only smoke enhancement with a positive direction, but only for one seed.
- The current LLM verifier `candidate_gate` is safe but too weak because SKAB has only 6 expert edges and 6 verifier records.

## Next Protocol Decision

For SKAB paper results:

1. Use the strong temporal/path protocol (`window=48`, `hidden=64`, `max_paths=16`, `40 epochs`) as the main branch.
2. Treat `candidate_gate` LLM verifier as a reliability/explanation branch unless formal 3-seed strong protocol proves a metric gain.
3. Keep `class_evidence` verifier and independent LLM edges as instability/ablation controls.
4. Do not use low-row smoke scores in final tables.
