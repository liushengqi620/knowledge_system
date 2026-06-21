# Dataset Policy Revision - 2026-06-20

## Core Decision

External expert and LLM edges should not intervene in the early graph structure by default. The main graph should be driven by train-only algorithmic evidence; expert and LLM evidence should move to later mechanisms such as RPF candidate admission, path reliability calibration, path consistency, and interpretation certificates. This avoids low-quality external edges distorting the dynamic graph before the model has learned dataset-specific temporal structure.

## Dataset-Specific Direction

### SKAB

Expert mechanism evidence is useful on SKAB, but the current positive result is not evidence for a strong early expert graph prior. The best run used expert evidence with `prior_strength=0`, so expert knowledge mostly helped as RPF/path-side evidence rather than as a hard graph rewrite. The next SKAB main protocol should keep expert evidence late and auditable, then validate whether candidate admission and prototype posterior fusion stabilize seeds 43/44.

Recommended comparable rerun:

```powershell
$env:PYTHONPATH='Scripts'; $env:KMP_DUPLICATE_LIB_OK='TRUE'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset skab --variant full --seeds 42,43,44 --output-dir C:\kg_runs\skab_late_expert_policy `
  --device cuda --hidden-dim 64 --window-size 48 --max-rows-per-split 8000 `
  --graph-top-k 8 --max-paths 16 --evidence-prior-mode expert --prior-strength 0 `
  --use-prototype-posterior-fusion --prototype-fusion-max-blend 0.30 `
  --prototype-fusion-blend-steps 7 --prototype-fusion-temperature-grid 0.25,0.50,1.00,2.00 `
  --prototype-fusion-min-val-gain 0.003
```

### C-MAPSS

C-MAPSS must return to the original RUL prediction task. The previous `degradation_stage_id` classification protocol is only an auxiliary diagnostic because the stage labels are derived and lose regression fidelity. The implementation now supports `--cmapss-target rul`; this keeps degradation stage labels as auxiliary training/diagnostic labels while making RUL MAE/RMSE/Score the primary output.

Smoke verified:

- output dir: `C:\kg_runs\cmapss_rul_protocol_smoke`
- primary metric family: `rul_regression`
- automatic health/RUL auxiliary weight: `1.0`
- smoke-only result with 400 rows and 1 epoch: RMSE `91.8433`, MAE `67.4790`

Recommended full RUL protocol seed sweep:

```powershell
$env:PYTHONPATH='Scripts'; $env:KMP_DUPLICATE_LIB_OK='TRUE'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset cmapss --cmapss-target rul --variant full --seeds 42,43,44 `
  --output-dir C:\kg_runs\cmapss_original_rul_main `
  --device cuda --hidden-dim 64 --window-size 64 --max-rows-per-split 8000 `
  --graph-top-k 8 --max-paths 16 --evidence-prior-mode none --prior-strength 0 `
  --health-aux-weight 1.0 --health-rul-cap 125 `
  --use-regime-prototype-residuals --regime-prototype-k 6 `
  --use-task-salience --salience-mode class_lifecycle --algorithmic-evidence-top-k 8 `
  --protect-order-anchor-path-nodes
```

### TEP

TEP should mainly optimize algorithmic temporal-lag structure. Expert/LLM corrections should be weakened or disabled because raw mechanism/LLM edges are likely low quality for this benchmark and can conflict with fault-specific process delays. The main path should use lagged algorithmic edge candidates, stable lag evidence, and proposal consistency.

Recommended TEP algorithmic-lag run:

```powershell
$env:PYTHONPATH='Scripts'; $env:KMP_DUPLICATE_LIB_OK='TRUE'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset tep --variant full --seeds 42,43,44 --output-dir C:\kg_runs\tep_algorithmic_lag_policy `
  --device cuda --hidden-dim 64 --window-size 64 --max-rows-per-split 8000 `
  --graph-top-k 8 --max-paths 16 --evidence-prior-mode none --prior-strength 0 `
  --algorithmic-edge-prior-mode edge_dual_lattice --algorithmic-edge-prior-top-k 20 `
  --algorithmic-edge-prior-group-top-k 4 --algorithmic-edge-prior-max-lag 8 `
  --algorithmic-edge-prior-strength 0.05 --algorithmic-edge-prior-lag-weight 0.55 `
  --use-stable-path-evidence --stable-path-evidence-mode static_lag `
  --stable-path-evidence-max-lag 8 --stable-path-evidence-min-vote-fraction 0.75 `
  --use-candidate-prior-admission --candidate-prior-admission-support-mode relative_evidence `
  --use-path-proposal-consistency --path-proposal-consistency-support-mode evidence_admit `
  --path-proposal-consistency-strength 0.35 --path-proposal-consistency-floor 0.10
```

## Paper Framing Change

The algorithm should be described as a dataset-adaptive path fusion framework:

1. Train-only algorithmic evidence builds the main temporal/spatial candidate structure.
2. Expert and LLM evidence enter as late-stage candidate priors, calibration signals, or interpretation constraints only when data support admits them.
3. RPF/path reliability and consistency modules perform final fusion, so the innovation is not a classifier choice but a controlled evidence-admission and path-fusion mechanism.

