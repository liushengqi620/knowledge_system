# Redundancy-Controlled RPF Rerun Plan

This plan records the immediate reruns required after changing RPF coverage to make redundancy auditable. Hard de-duplication excludes globally selected paths and is a negative ablation. The default is soft redundancy: globally selected paths are penalized before group coverage, but not forbidden. Results produced before this patch remain diagnostic checkpoints, not final paper-table evidence.

## Invariant

- Keep `--auto-path-budget` off unless explicitly testing that ablation.
- Report `mean_path_duplicate_rate` from the result summary.
- Use `--coverage-dedup-mode soft --coverage-redundancy-penalty 0.05` as the updated default.
- Do not mix old pre-redundancy-control RPF results with new result tables.
- Use validation admission for optional salience/expert/LLM candidates; never choose candidates by test performance.

## Hydraulic Valve Default RPF

```powershell
$env:PYTHONPATH='Scripts'
$env:KMP_DUPLICATE_LIB_OK='TRUE'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset hydraulic --hydraulic-targets valve --variant full `
  --seeds 42,43,44 --window-size 48 --hidden-dim 64 --epochs 40 `
  --batch-size 256 --max-rows-per-split 8000 `
  --graph-top-k 4 --max-paths 16 `
  --forecast-weight 0.01 --graph-weight 0.002 `
  --evidence-prior-mode none --prior-strength 0.0 `
  --coverage-dedup-mode soft --coverage-redundancy-penalty 0.05 `
  --output-dir knowledge_exports\ms_gse_rpf_soft_redundancy
```

## Hydraulic Valve Salience Candidate

```powershell
$env:PYTHONPATH='Scripts'
$env:KMP_DUPLICATE_LIB_OK='TRUE'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset hydraulic --hydraulic-targets valve --variant full `
  --seeds 42,43,44 --window-size 48 --hidden-dim 64 --epochs 40 `
  --batch-size 256 --max-rows-per-split 8000 `
  --graph-top-k 4 --max-paths 16 `
  --forecast-weight 0.01 --graph-weight 0.002 `
  --evidence-prior-mode none --prior-strength 0.0 `
  --coverage-dedup-mode soft --coverage-redundancy-penalty 0.05 `
  --use-task-salience --salience-selection-strength 0.05 `
  --output-dir knowledge_exports\ms_gse_rpf_soft_redundancy_salience_s005
```

## Validation Admission

```powershell
$env:PYTHONPATH='Scripts'
python -B Scripts\summarize_ms_gse_rpf_admission.py `
  --baseline-dir knowledge_exports\ms_gse_rpf_soft_redundancy `
  --candidate salience_s005=knowledge_exports\ms_gse_rpf_soft_redundancy_salience_s005 `
  --dataset hydraulic --target valve --variant full `
  --filename-contains prior-none --n-rows-total 2205 `
  --min-val-gain 0.0 `
  --output-dir knowledge_exports\ms_gse_rpf_soft_redundancy_validation_admission\hydraulic_valve_salience_s005

python -B Scripts\summarize_ms_gse_rpf_results.py `
  --result-dir knowledge_exports\ms_gse_rpf_soft_redundancy_validation_admission\hydraulic_valve_salience_s005\selected_runs `
  --dataset hydraulic --target valve --variants full_admitted `
  --filename-contains admitted --n-rows-total 2205 `
  --output knowledge_exports\ms_gse_rpf_soft_redundancy_validation_admission\hydraulic_valve_salience_s005\selected_runs_summary.md
```

## Corrected SKAB Default RPF

```powershell
$env:PYTHONPATH='Scripts'
$env:KMP_DUPLICATE_LIB_OK='TRUE'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset skab --variant full --seeds 42,43,44 `
  --window-size 48 --hidden-dim 64 --epochs 40 `
  --batch-size 256 --max-rows-per-split 12000 `
  --graph-top-k 4 --max-paths 16 `
  --forecast-weight 0.01 --graph-weight 0.002 `
  --evidence-prior-mode none --prior-strength 0.0 `
  --coverage-dedup-mode soft --coverage-redundancy-penalty 0.05 `
  --output-dir knowledge_exports\ms_gse_rpf_soft_redundancy
```

## Summary

```powershell
$env:PYTHONPATH='Scripts'
python -B Scripts\summarize_ms_gse_rpf_results.py `
  --result-dir knowledge_exports\ms_gse_rpf_soft_redundancy `
  --variants full --filename-contains prior-none `
  --output knowledge_exports\ms_gse_rpf_soft_redundancy\ms_gse_rpf_soft_redundancy_summary.md
```
