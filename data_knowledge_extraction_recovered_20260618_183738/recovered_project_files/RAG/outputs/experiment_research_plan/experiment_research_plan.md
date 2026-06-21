# RAG Experiment Research Plan

| ID | Track | Title | Status | Decision Gate |
|---|---|---|---|---|
| A1 | prompt_atom | Prompt-atom decomposition diagnostics | ready | functional_atom should beat no_atom on edit locality and diagnostic score without over_fine fragmentation risk |
| A2 | prompt_atom | Prompt-atom runner dry run | ready | Every strategy should produce a row with missing_result_file or not_executed rather than failing silently |
| A3 | prompt_atom | Full prompt-atom result ablation | ready_scaffold_only | functional_atom must improve Overall F1 and reduce KHR against no_atom and random_atom under the same data and evaluator |
| B1 | plm_baseline | Prepare supervised PLM matrix | blocked_missing_dataset | All configured combinations appear in the manifest, and fixed FSDV/FSDV-EAPA rows remain separated from trainable PLM rows |
| B2 | plm_baseline | BERT-CRF+CasRel supervised baseline | blocked_missing_data_or_training_modules | Use dev Overall F1 for checkpoint selection, then evaluate held-out test splits separately |
| B3 | plm_baseline | External PLM adapters | pending_adapter_implementation | Each adapter must use the same split, seed, encoder policy, and test metric schema |
| C1 | evaluation | Held-out test evaluation | blocked_until_trained_runs_exist | Paper tables must use test metrics or clearly mark development metrics |
| D1 | reporting | Evidence audit for paper claims | ready | No placeholder row can be described as an experimental result |

## Commands

### A1. Prompt-atom decomposition diagnostics

Question: Which prompt decomposition strategy creates the most useful local update units before LLM evaluation?

```powershell
python experiments/prompt_atom_decomposition_experiment.py --output-dir outputs/prompt_atom_decomposition
```

Expected outputs: diagnostic_results.json; diagnostic_summary.csv; diagnostic_table.tex; experiment_protocol.md

Notes: This is a safe first experiment because it does not fabricate extraction metrics.

### A2. Prompt-atom runner dry run

Question: Can all decomposition strategies be scheduled and summarized with explicit missing-result states?

```powershell
python experiments/run_atom_decomposition_result_experiment.py --dry-run --output-root outputs/atom_decomposition_result_dryrun
```

Expected outputs: atom_decomposition_result_summary.csv; atom_decomposition_result_summary.json; atom_decomposition_result_table.tex

Notes: Use this to inspect commands before running any expensive LLM pipeline.

### A3. Full prompt-atom result ablation

Question: Does functional_atom improve NER F1, RE F1, Overall F1, and KHR over coarse or random prompt decompositions?

```powershell
python experiments/run_atom_decomposition_result_experiment.py --output-root outputs/atom_decomposition_result
```

Expected outputs: per-strategy ablation_results.json plus consolidated CSV/JSON/LaTeX table

Notes: The recovered prompt_engineering_ablation.py is a scaffold unless a real evaluator is restored.

### B1. Prepare supervised PLM matrix

Question: What exact dataset/model/ratio/seed combinations are required for a fair low-annotation comparison?

```powershell
python experiments/extended_plm_baselines.py --output-dir outputs/plm_extended_baselines_runs
```

Expected outputs: manifest.json; results_template.csv; run_commands.ps1; split files

Notes: Provide dataset paths or restore data before running on real inputs.

### B2. BERT-CRF+CasRel supervised baseline

Question: How much annotation does the local supervised pipeline need to approach FSDV-EAPA?

```powershell
python experiments/extended_plm_baselines.py --execute --models BERT-CRF+CasRel --output-dir outputs/plm_extended_baselines_runs
```

Expected outputs: summary_metrics.json for each dataset/ratio/seed row

Notes: Do not compare dev-selected metrics directly against test-only FSDV/FSDV-EAPA rows.

### B3. External PLM adapters

Question: Do PURE, CasRel, TPLinker, and PRGC change the conclusion under the same annotation budgets?

```powershell
edit experiments/plm_external_adapters.template.json, then run extended_plm_baselines.py --execute
```

Expected outputs: summary_metrics.json from each external adapter plus per-sample predictions

Notes: OneRel can remain optional unless the final paper table needs it.

### C1. Held-out test evaluation

Question: Do completed supervised baselines hold up on test data after dev selection?

```powershell
python experiments/evaluate_local_plm_baseline.py --run-root outputs/plm_extended_baselines_runs --device cuda
```

Expected outputs: test_results.csv; test_summary.csv; per-run test_metrics.json

Notes: Run after BERT-CRF+CasRel training outputs exist.

### D1. Evidence audit for paper claims

Question: Which claims are supported by completed evidence and which are still planned?

```powershell
python experiments/experiment_status.py --output-dir outputs/experiment_status
```

Expected outputs: status_report.json; status_items.csv; status_report.md

Notes: Use this before writing or updating any manuscript table.
