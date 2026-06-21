# RAG Experiment Status

Project root: `C:\Users\CPILAB\Documents\xwechat_files\wxid_fn3terjpgaio22_c340\msg\file\2026-06\codex_recovery\data_knowledge_extraction_recovered_20260618_183738\recovered_project_files\RAG`

## Summary

- `total_items`: 17
- `blocker_count`: 4
- `pending_count`: 5
- `ready_count`: 8

## Items

| Area | Name | Status | Note |
|---|---|---|---|
| core_file | `prompt_diagnostic` | ready | found |
| core_file | `prompt_result_runner` | ready | found |
| core_file | `prompt_ablation_pipeline` | ready | found |
| core_file | `plm_matrix` | ready | found |
| core_file | `local_plm_train_adapter` | ready | found |
| core_file | `local_plm_test_evaluator` | ready | found |
| core_file | `external_adapter_template` | ready | found |
| dataset | `continuous_casting` | missing | provide dataset or pass source override before PLM runs |
| dataset | `electrochemistry` | missing | provide dataset or pass source override before PLM runs |
| dataset | `baosteel_quality_traceability` | ready | found candidate dataset |
| training_module | `advanced_ner_training_module` | missing | required only for BERT-CRF+CasRel execution |
| training_module | `relation_extraction_training_module` | missing | required only for BERT-CRF+CasRel execution |
| external_adapter | `OneRel` | pending | Optional OneRel adapter. The command must write summary_metrics.json to {output_dir}. |
| external_adapter | `PRGC` | pending | Fill in the command for an external PRGC implementation. The command must write summary_metrics.json to {output_dir}. |
| external_adapter | `PURE` | pending | Fill in the command for an external PURE implementation. The command must write summary_metrics.json to {output_dir}. |
| external_adapter | `TPLinker` | pending | Fill in the command for an external TPLinker implementation. The command must write summary_metrics.json to {output_dir}. |
| result | `plm_results_template` | partial | 10 rows with metrics, 54 rows pending |

## Recommended Next Steps

- Restore or point to the continuous-casting extraction dataset.
- Restore or point to the electrochemistry extraction dataset.
- Restore local NER/RE training modules before running BERT-CRF+CasRel.
- Replace placeholder commands for external adapters: OneRel, PRGC, PURE, TPLinker.
