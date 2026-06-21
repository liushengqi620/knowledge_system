# LLM Expert-Condition Verifier Experiment Plan

## Purpose

This branch converts LLM evidence from an independent graph-edge source into a metadata-only conditional verifier for existing expert mechanism edges. The LLM does not add final graph edges. An expert edge can only receive verifier support after train-only data support admits it.

## Implemented Protocol

1. Generate metadata-only verifier evidence:

```powershell
$env:PYTHONPATH='Scripts'
python -B Scripts/llm_public_benchmark_evidence.py `
  --dataset skab `
  --target anomaly `
  --mode expert_condition_verifier `
  --max-edges 12 `
  --max-prompt-features 120 `
  --output-dir knowledge_exports/llm_evidence
```

2. Merge verified metadata into the ready knowledge graph only after reviewing the response:

```powershell
$env:PYTHONPATH='Scripts'
python -B Scripts/llm_public_benchmark_evidence.py `
  --dataset skab `
  --target anomaly `
  --mode expert_condition_verifier `
  --response-file knowledge_exports/llm_evidence/skab_anomaly_llm_expert_condition_verifier.json `
  --merge-into-ready-graph
```

3. Train with verifier admission enabled:

```powershell
$env:PYTHONPATH='Scripts'
python -B Scripts/run_public_ms_gse_rpf_experiment.py `
  --dataset skab `
  --variant full `
  --seeds 42,43,44 `
  --epochs 40 `
  --device cuda `
  --evidence-prior-mode expert `
  --algorithmic-edge-prior-mode edge_pool `
  --algorithmic-edge-prior-top-k 16 `
  --algorithmic-edge-prior-candidate-only `
  --use-llm-expert-condition-verifier `
  --llm-condition-verifier-min-data-support 0.05 `
  --llm-condition-verifier-weight 0.50 `
  --use-candidate-prior-admission `
  --candidate-coverage-fraction 0.05 `
  --output-dir knowledge_exports/skab_llm_condition_verifier_main
```

## Required Ablations

- A0: algorithmic-only edge/path prior.
- A1: expert prior as path candidate only.
- A2: legacy independent LLM candidate edges.
- A3: current LLM expert graph dynamic correction.
- A4: new LLM expert-condition verifier.
- A5: verifier plus weak-class class_scope records for low-tail classes.

## Decision Criteria

- Main metrics: macro-F1, balanced accuracy, low-tail class F1 for classification; RMSE, MAE, NASA score for C-MAPSS RUL.
- Stability: mean and std over seeds 42, 43, 44.
- Reliability diagnostics: admitted verifier edges, rejected verifier edges, data-supported ratio, class-evidence edges before/after.
- Efficiency: train seconds, inference samples per second, parameter count.

## Paper Claim Boundary

The verifier branch should be described as conditional mechanism-path evidence, not as LLM graph construction. The paper story is: expert graph supplies mechanism hypotheses, algorithmic evidence supplies train-only temporal/data support, and LLM supplies conditional semantic gates that are admitted only when the data support is sufficient.
