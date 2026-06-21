# Mechanism Gate Ablation Matrix

This protocol isolates whether expert mechanism evidence helps because it is admitted by data-supported gates, rather than because raw edges are injected into the graph. Missing rows are not evidence.

- output root: `knowledge_exports\aaai_missing_ablation_runs\skab_no_complexity_smoke`
- primary dataset: `SKAB`
- certificate: validation gain, seed-level safety, low-tail F1 safety, and path-overlap diagnostics

## Variants

| Variant | Role | Claim | Command |
|---|---|---|---|
| no_mechanism | baseline | No expert mechanism evidence is available to RPF or the graph. | `python -B 'Scripts\run_public_ms_gse_rpf_experiment.py' --dataset skab --variant full --seeds 42 --output-dir 'knowledge_exports\aaai_missing_ablation_runs\skab_no_complexity_smoke\no_mechanism' --device cuda --hidden-dim 16 --window-size 16 --max-rows-per-split 400 --epochs 1 --batch-size 128 --graph-top-k 4 --max-paths 8 --forecast-weight 0.05 --graph-weight 0.02 --use-prototype-posterior-fusion --prototype-fusion-max-blend 0.30 --prototype-fusion-blend-steps 7 --prototype-fusion-temperature-grid 0.25,0.50,1.00,2.00 --prototype-fusion-min-val-gain 0.003 --evidence-prior-mode none --prior-strength 0` |
| expert_llm_candidate_data_gate_no_complexity | no_complexity_penalty | Expert and LLM candidate families keep the same data-support admission, but source-family complexity scaling is disabled. | `python -B 'Scripts\run_public_ms_gse_rpf_experiment.py' --dataset skab --variant full --seeds 42 --output-dir 'knowledge_exports\aaai_missing_ablation_runs\skab_no_complexity_smoke\expert_llm_candidate_data_gate_no_complexity' --device cuda --hidden-dim 16 --window-size 16 --max-rows-per-split 400 --epochs 1 --batch-size 128 --graph-top-k 4 --max-paths 8 --forecast-weight 0.05 --graph-weight 0.02 --use-prototype-posterior-fusion --prototype-fusion-max-blend 0.30 --prototype-fusion-blend-steps 7 --prototype-fusion-temperature-grid 0.25,0.50,1.00,2.00 --prototype-fusion-min-val-gain 0.003 --evidence-prior-mode expert_llm --prior-strength 0 --external-edge-candidate-only --external-candidate-families expert,llm --external-family-calibration-floor 0.10 --external-family-min-data-support 0.10 --external-candidate-llm-scale 0.70 --external-candidate-default-scale 0.85 --disable-source-complexity-penalty --candidate-coverage-fraction 0.08 --use-task-salience --salience-mode class --algorithmic-evidence-top-k 8 --use-candidate-prior-admission --candidate-prior-admission-target coverage_feature --candidate-prior-admission-support-mode relative_evidence --candidate-prior-admission-floor 0.05 --candidate-prior-admission-threshold 0.35 --candidate-prior-admission-scale 0.50` |

## Current Evidence

| Variant | Status | Runs | Test Macro-F1 | Val gain | Test gain | Low-tail val F1 gain | Path Jaccard | Source burden | Reject reasons |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| no_mechanism | baseline_complete | 1 | 0.5537 +/- 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | edges=0.0; families=0.0; disabled=0.00; llm_scale=0.70 | none |
| expert_llm_candidate_data_gate_no_complexity | rejected | 1 | 0.5975 +/- 0.0000 | -0.0283 | 0.0438 | -0.0635 | 0.0526 | edges=0.0; families=0.0; disabled=1.00; llm_scale=1.00 | mean_validation_gain_below_threshold, seed_level_validation_drop, low_tail_class_harm |

## Interpretation Rule

A mechanism-gating claim is paper-ready only if `expert_candidate_data_gate` or `expert_candidate_data_gate_consistency` is complete across the planned seeds, improves validation over `no_mechanism`, does not harm low-tail validation F1 beyond the threshold, and is better than `raw_expert_graph` or `expert_candidate_no_gate` under the same protocol.
