# RAG Low-Annotation Knowledge Extraction Engineering Brief

## Project Positioning

This project turns the recovered RAG research artifacts into an executable engineering track for low-annotation industrial mechanism-layer knowledge graph extraction. The core task is not open-domain document QA and not production-log traceability modeling. It is a controlled information-extraction system that compares frozen LLM prompting, prompt-atom optimization, and supervised PLM baselines on mechanism entity/relation extraction.

Primary research claim:

```text
PLM-guided prompt-atom adjudication can improve low-resource mechanism-layer KG extraction by using PLM models for candidate generation, uncertainty estimation, evidence-window selection, and prompt-atom routing, while using LLMs for constrained candidate adjudication.
```

Primary engineering goal:

```text
Build a reproducible experiment package that can prepare datasets, run prompt-atom diagnostics, run or register baseline models, evaluate NER/RE results, and produce paper-ready tables.
```

## Scope

In scope:

- Continuous-casting knowledge extraction.
- Mechanism-layer knowledge graph extraction from papers, process manuals, expert rules, and defect mechanism reports.
- Electrochemistry knowledge extraction.
- NER F1, RE F1, and Overall F1 evaluation.
- FSDV and FSDV-EAPA reference reporting.
- Prompt-atom decomposition diagnostics.
- Supervised PLM baseline matrix and adapter slots.
- Result tables for papers and internal review.

Out of scope for the first engineering milestone:

- General RAG chatbot or document QA.
- Using processed Baosteel production records as the primary mechanism-layer extraction dataset.
- Production web UI.
- Online training service.
- Claims based on unexecuted external baselines.

## Current Recovered Assets

```text
experiments/
  prompt_atom_decomposition_experiment.py
  run_atom_decomposition_result_experiment.py
  extended_plm_baselines.py
  build_mechanism_kg_experiment_plan.py
  run_local_plm_baseline.py
  evaluate_local_plm_baseline.py
  plm_external_adapters.template.json

outputs/plm_extended_baselines/
  README.md
  experiment_plan.csv
  results_template.csv

tests/
  test_prompt_atom_decomposition_experiment.py
  test_atom_decomposition_result_runner.py
  test_extended_plm_baselines.py
  test_eapa_atom_strategy.py
```

Some referenced upstream files, such as `experiments/prompt_engineering_ablation.py` and local training modules under `scripts/`, were not recovered in this package. They should be restored or replaced before full end-to-end execution.

## Engineering Modules

### 1. Data Preparation

Purpose:

- Normalize mechanism-layer text, continuous-casting fixtures, and electrochemistry datasets into one extraction schema.
- Produce deterministic train/dev/test splits.
- Sample 10%, 50%, and 100% annotation budgets.

Inputs:

- Mechanism KG: JSONL records from papers, manuals, expert rules, and defect mechanism reports.
- Continuous casting: JSON list with text, entities, and relations.
- Electrochemistry: JSONL records that can be converted into MATERIAL-VALUE relation examples.

Outputs:

- `splits/<dataset>/train.json`
- `splits/<dataset>/dev.json`
- `splits/<dataset>/test.json`
- `manifest.json`
- `results_template.csv`
- `run_commands.ps1`

Implemented by:

- `experiments/extended_plm_baselines.py`

Acceptance criteria:

- Sampling is deterministic for the same seed.
- All configured datasets, ratios, models, and seeds appear in the manifest.
- Missing external adapters are reported as pending, not silently treated as completed.

### 2. Prompt-Atom Diagnostics

Purpose:

- Compare prompt decomposition strategies before expensive LLM evaluation.
- Measure whether a prompt decomposition produces useful local update units.

Strategies:

- `no_atom`
- `fsdv_block`
- `sentence_level`
- `random_atom`
- `over_fine`
- `functional_atom`

Diagnostics:

- Attribution coverage.
- Edit locality.
- Semantic completeness.
- Protected-rule coverage.
- Over-fragmentation risk.
- Over-coarsening risk.

Implemented by:

- `experiments/prompt_atom_decomposition_experiment.py`

Acceptance criteria:

- The script writes machine-readable CSV/JSON diagnostics.
- `functional_atom` should create more local units than `no_atom` and fewer pathological fragments than `over_fine`.
- The diagnostics should not fabricate NER/RE scores.

### 3. Prompt-Atom Result Ablation

Purpose:

- Run the real FSDV-EAPA pipeline once per decomposition strategy.
- Summarize extraction metrics and prompt-update behavior.

Expected metrics:

- NER F1.
- RE F1.
- Overall F1.
- KHR.
- Accepted updates.
- Rollbacks.

Implemented by:

- `experiments/run_atom_decomposition_result_experiment.py`

Blocked by:

- Missing `experiments/prompt_engineering_ablation.py` in the recovered package.

Acceptance criteria:

- Every strategy produces a result row.
- Missing result files are marked as `missing_result_file`, not hidden.
- The final output includes CSV, JSON, and LaTeX table files.

### 4. PLM Baseline Matrix

Purpose:

- Compare FSDV/FSDV-EAPA against supervised PLM extraction baselines under different annotation budgets.

Datasets:

- `continuous_casting`
- `electrochemistry`

Baseline models:

- `BERT-CRF+CasRel`
- `PURE`
- `CasRel`
- `TPLinker`
- `PRGC`
- `OneRel`

Annotation ratios:

- `10%`
- `50%`
- `100%`

Seeds:

- `2026`
- `2027`
- `2028`

Implemented by:

- `experiments/extended_plm_baselines.py`
- `experiments/run_local_plm_baseline.py`
- `experiments/evaluate_local_plm_baseline.py`

Acceptance criteria:

- The experiment matrix includes all dataset/model/ratio/seed combinations.
- External models use adapter commands and must write `summary_metrics.json`.
- Test metrics are separated from development metrics.
- Empty pending rows remain empty until a real run is completed.

## MVP Definition

The first complete engineering milestone is reached when the project can do the following from a clean checkout:

1. Prepare the extended PLM baseline matrix.
2. Run prompt-atom diagnostics.
3. Run unit tests for deterministic sampling and prompt decomposition.
4. Produce a consolidated project status report showing completed, pending, and blocked experiments.

The MVP does not require all external PLM baselines to finish. It does require the pending adapter slots and missing dependencies to be explicit.

## Suggested Command Workflow

From the `RAG` directory:

```powershell
python -m pytest tests
```

Prepare PLM baseline files:

```powershell
python experiments/extended_plm_baselines.py --output-dir outputs/plm_extended_baselines_runs
```

Run prompt-atom diagnostics:

```powershell
python experiments/prompt_atom_decomposition_experiment.py --output-dir outputs/prompt_atom_decomposition
```

Build the mechanism-layer KG paper experiment matrix:

```powershell
python experiments/build_mechanism_kg_experiment_plan.py --output-dir outputs/mechanism_kg_experiment_plan
```

The matrix now includes frontier comparison groups documented in `docs/frontier_knowledge_extraction_baselines.md`, including GLiNER, InstructUIE, GoLLIE, Code4UIE, KnowCoder, DeepKE-LLM, constrained JSON extraction, and retrieval-augmented schema prompting.

Run the large parameterized mechanism-layer KG seed experiment and save extraction results. The current seed set contains 1,000 template, challenge, large-scale, implicit-rule, alias/pronoun, and nested-entity records, reports metrics on the held-out test split, and keeps the rule-based baseline limited to train-split entity lexicons:

```powershell
python experiments/run_mechanism_kg_seed_experiment.py --data-dir data/mechanism_kg --output-dir outputs/mechanism_kg_seed_experiment
```

The optimized proxy keeps long technical entity spans before accepting nested entities, only preserves deliberately coded nested child spans, and uses discourse-trigger positions for implicit relation selection. This is intended to reduce substring boundary false positives and hard-negative hallucinated triples before the final LLM-style adjudication step.

Validate the generated mechanism KG seed records:

```powershell
python experiments/validate_knowledge_extraction_dataset.py --input data/mechanism_kg/annotations/all_records.jsonl --output-dir outputs/mechanism_kg_seed_validation/gold
python experiments/validate_knowledge_extraction_dataset.py --input outputs/mechanism_kg_seed_experiment/final_records_with_predictions.jsonl --output-dir outputs/mechanism_kg_seed_validation/predictions
```

Build the large KG pack for later quality traceability work:

```powershell
python experiments/build_quality_traceability_large_kg_pack.py --output-dir outputs/quality_traceability_large_kg_pack --kg-dir data/quality_traceability_large_kg
```

Build advanced downstream anomaly-traceability experiment groups for comparing feature-only RCA, time-series anomaly models, causal RCA, KG reasoning, GraphRAG/LLM methods, and the proposed PLM-LLM-KG fusion:

```powershell
python experiments/build_advanced_traceability_experiment_groups.py --output-dir outputs/advanced_traceability_experiment_groups --doc-path docs/advanced_anomaly_traceability_experiment_groups.md
```

Run the executable weak-label pilot for KG-enhanced anomaly traceability:

```powershell
python experiments/run_advanced_traceability_pilot_experiment.py --output-dir outputs/advanced_traceability_pilot
```

Build the paper-demo package with leakage-controlled scenarios, path-quality metrics, case studies, and an expert-audit template:

```powershell
python experiments/run_paper_demo_traceability_experiment.py --output-dir outputs/paper_demo_traceability --per-label 200
```

Build paper-ready evidence tables, blinded expert-review files, and the expert-audit scoring report:

```powershell
python experiments/build_traceability_paper_evidence_pack.py --demo-dir outputs/paper_demo_traceability --output-dir outputs/traceability_paper_evidence_pack
```

Use `docs/traceability_expert_audit_protocol.md` as the review protocol before reporting expert-validated traceability claims.

Fill an assistant technical precheck copy of the audit file for internal triage only, then score it in a short output path to avoid Windows path-length issues:

```powershell
python experiments/fill_assistant_traceability_audit.py --blind outputs/traceability_paper_evidence_pack/expert_audit_blind.csv --key outputs/traceability_paper_evidence_pack/expert_audit_key.csv --output outputs/traceability_assistant_precheck/assistant_technical_audit.csv
python experiments/build_traceability_paper_evidence_pack.py --demo-dir outputs/paper_demo_traceability --audit-file outputs/traceability_assistant_precheck/assistant_technical_audit.csv --output-dir outputs/tace_ai_pack
```

The method chapter draft is `docs/paper_method_chapter_plm_llm_kg_traceability.md`.

Validate the rich knowledge-extraction seed dataset:

```powershell
python experiments/validate_knowledge_extraction_dataset.py --input data/examples/continuous_casting_seed.json --output-dir outputs/dataset_validation
```

Optional downstream validation only: build the Baosteel-derived instance-layer dataset from processed traceability tables and three-level system outputs:

```powershell
python experiments/build_baosteel_knowledge_extraction_dataset.py --output-dir data/baosteel_knowledge_extraction --top-features 8
```

Optional downstream validation only: validate the Baosteel JSONL dataset:

```powershell
python experiments/validate_knowledge_extraction_dataset.py --input data/baosteel_knowledge_extraction/records.jsonl --output-dir outputs/baosteel_dataset_validation
```

Optional downstream validation only: prepare PLM baseline files for the Baosteel dataset:

```powershell
python experiments/extended_plm_baselines.py --datasets baosteel_quality_traceability --output-dir outputs/plm_baosteel_runs
```

Run result-level prompt-atom ablation after restoring the missing upstream pipeline:

```powershell
python experiments/run_atom_decomposition_result_experiment.py --output-root atom_result
```

On Windows, keep atom-result output roots short when this recovered workspace is nested deeply. Long roots such as `outputs/experiment_suite/atom_decomposition_result_dryrun` can exceed the legacy path-length limit.

Build a concrete experiment research plan:

```powershell
python experiments/build_experiment_research_plan.py --output-dir outputs/experiment_research_plan
```

Audit experiment readiness:

```powershell
python experiments/experiment_status.py --output-dir outputs/experiment_status
```

Run the safe smoke workflow:

```powershell
python experiments/run_experiment_suite.py --output-dir outputs/experiment_suite
```

Preview the suite without executing commands:

```powershell
python experiments/run_experiment_suite.py --dry-run --output-dir outputs/experiment_suite_dryrun
```

## Engineering Backlog

### P0: Make the Package Reproducible

- Build a mechanism-layer gold dataset from papers, process manuals, expert rules, and defect mechanism reports.
- Replace the scaffold in `experiments/prompt_engineering_ablation.py` with the full evaluator before reporting real FSDV-EAPA result ablations.
- Restore or replace local NER/RE training modules used by `run_local_plm_baseline.py`.
- Add a pinned dependency file such as `requirements.txt` or `environment.yml`.
- Add a small synthetic fixture dataset for CI tests.
- Keep `data/examples/continuous_casting_seed.json` as a schema fixture only.
- Keep `data/baosteel_knowledge_extraction/records.jsonl` out of the current mechanism-layer main experiment; use it only for later instance-layer attachment or traceability validation.
- Keep `experiments/experiment_status.py` as the gate for missing files, missing datasets, and pending adapters.

### P1: Complete Baseline Execution

- Implement adapter wrappers for PURE, CasRel, TPLinker, and PRGC.
- Decide whether OneRel is required or optional for the final paper table.
- Store per-sample predictions for bootstrap significance testing.
- Ensure all reported rows identify dev-selected checkpoints and test-only metrics.

### P2: Paper-Ready Reporting

- Generate final CSV, JSON, Markdown, and LaTeX tables from one command.
- Add plotting scripts for annotation-ratio curves.
- Add an audit report separating completed evidence from planned evidence.

### P3: Engineering Hardening

- Add CLI config files for datasets, models, seeds, and output roots.
- Add structured logs for each experiment run.
- Add checksum tracking for datasets and split files.
- Add cache reuse for expensive LLM or PLM runs.

## Proposed Team Task Split

Algorithm owner:

- Owns FSDV-EAPA, prompt atom strategies, KHR definition, and ablation design.

Data owner:

- Owns dataset conversion, split reproducibility, schema validation, and data checksums.

Baseline owner:

- Owns BERT-CRF+CasRel and external PLM adapter integrations.

Evaluation owner:

- Owns metric scripts, test/dev separation, bootstrap testing, and final tables.

Paper owner:

- Owns experiment claims, evidence audit, figure/table wording, and pending-result gates.

## Definition of Done

A result or table is publishable only when:

- The command that generated it is recorded.
- The dataset split and seed are recorded.
- The metric source is test data, unless clearly marked as development.
- The output file path is listed.
- External baseline status is either completed with metrics or explicitly pending.
- No placeholder row is described as an experimental result.
