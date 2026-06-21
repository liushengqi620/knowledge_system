# TEP GPU Evidence Admission Summary

This note records the unified CUDA follow-up for the current TEP MS-GSE + RPF screening setting. All runs use the same 8000-window train/test budget, 25 epochs, `group_pair_inclusive` path coverage, hard coverage de-duplication, class-conditioned path evidence with top-8 features, path auxiliary loss 0.05, evidence-router auxiliary loss 0.05, and `device=cuda`.

| Setting | Seeds | Macro-F1 | Balanced accuracy | Prior mass | Context importance | Inference/s | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Algorithm-only class-conditioned RPF | 42/43/44 | 0.6095 +/- 0.0105 | 0.6185 +/- 0.0108 | 0.0000 | 0.7480 | 7280.4 | safest current TEP default |
| Algorithm + calibrated expert prior | 42/43/44 | 0.6088 +/- 0.0120 | 0.6168 +/- 0.0127 | 0.0284 | 0.7668 | 8021.8 | prior enters paths but does not improve mean accuracy |
| Algorithm + calibrated expert+LLM prior | 42/43/44 | 0.6040 +/- 0.0119 | 0.6140 +/- 0.0134 | 0.0295 | 0.7698 | 7218.5 | LLM edges are not yet stable enough for default admission |
| Burden-aware validation admission | 42/43/44 | 0.6097 +/- 0.0105 | 0.6195 +/- 0.0108 | mixed | mixed | 7267.6 | selects baseline / expert+LLM / baseline by validation score after source burden |

Interpretation:

- The single-seed expert+LLM gain was not reproduced under unified GPU three-seed evaluation.
- External evidence is visible in path fusion (`mean_path_prior_weight` rises from 0.0000 to about 0.029), but visibility is not the same as useful evidence.
- The burden-aware admission rule prevents most negative transfer and admits expert+LLM only for seed43, but the mean gain over algorithm-only is only `+0.0002` Macro-F1. This is a safety result, not yet a strong performance result.
- The paper claim should therefore be validation-gated evidence admission: expert and LLM edges are candidate evidence sources that can be accepted, rejected, or burden-penalized.
- The next TEP algorithm step should add a formal source-burden admission rule for expert/LLM evidence and improve temporal path quality, especially fault-family and lag-aware path prototypes.

Artifacts:

- `knowledge_exports/tep_cls_k8_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_expcal_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_expllmc_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_external_evidence_gpu_burden/ms_gse_rpf_validation_admission.md`
