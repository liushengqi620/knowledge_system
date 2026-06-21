# TEP GPU Algorithmic Path Candidate Summary

This note records the first TEP follow-up after the external-evidence admission check. All rows use the same 8000-window TEP screening budget, 25 epochs, `group_pair_inclusive` path coverage, hard coverage de-duplication, class-conditioned path evidence top-8, path auxiliary loss 0.05, evidence-router auxiliary loss 0.05, and `device=cuda`.

| Setting | Seeds | Macro-F1 | Balanced accuracy | Salience mass | Context importance | Result |
|---|---:|---:|---:|---:|---:|---|
| Static class-conditioned evidence | 42/43/44 | 0.6095 +/- 0.0105 | 0.6185 +/- 0.0108 | 0.2975 | 0.7480 | current algorithm-only reference |
| Static + lag evidence, max lag 3, weight 0.50 | 42/43/44 | 0.6071 +/- 0.0085 | 0.6162 +/- 0.0121 | 0.1456 | 0.7404 | lag evidence lowers salience mass and does not improve mean |
| Static + lag evidence, max lag 1, weight 0.25 | 42/43/44 | 0.6051 +/- 0.0111 | 0.6118 +/- 0.0140 | 0.2175 | 0.7753 | conservative lag mix still hurts |
| Two-hop path compression, 25% path budget | 42/43/44 | 0.6005 +/- 0.0205 | 0.6049 +/- 0.0255 | 0.3468 | 0.8349 | improves seed42 but collapses seed44 |
| Two-hop path compression, 10% path budget | 42/43/44 | 0.6003 +/- 0.0153 | 0.6083 +/- 0.0183 | 0.3152 | 0.7961 | lower two-hop budget remains unstable |
| Burden-aware algorithmic admission | 42/43/44 | 0.6098 +/- 0.0105 | 0.6199 +/- 0.0108 | 0.2426 | mixed | selects baseline / static-lag / baseline by validation |
| Fault-family class path prototypes, k=3, weight 0.25 | 42/43/44 | 0.6058 +/- 0.0151 | 0.6121 +/- 0.0155 | 0.2790 | 0.7554 | improves seeds 42/43 over some lag variants but hurts seed44 |
| Fault-family prototypes + sample gate, threshold 0.20 | 42/43/44 | 0.6074 +/- 0.0101 | 0.6142 +/- 0.0111 | 0.2651 | 0.7434 | improves seed43 to 0.6160 but is not validation-selected |
| Burden-aware algorithmic admission v2 | 42/43/44 | 0.6098 +/- 0.0105 | 0.6199 +/- 0.0108 | 0.2426 | mixed | still selects baseline / static-lag / baseline; family/gate reveals validation-test mismatch |

Interpretation:

- The new lag-aware evidence implementation is functional and direction-aware, but direct lag mixing is not a stable TEP gain.
- Two-hop paths expose plausible mechanism chains and improve seed42, but they are too unstable without a stronger admission rule.
- Validation admission can safely adopt the lag candidate for seed43 while falling back to the baseline for seeds 42 and 44; the mean gain over static class evidence is only `+0.0003` Macro-F1.
- Fault-family smoothing and sample-level evidence gating are implemented and auditable. The gate reduces class evidence only mildly (`Class adm.` about 0.9565 on the tested setting), and the gated family candidate reaches the best seed43 test Macro-F1 among this batch (`0.6160`).
- Strict validation admission does not select the family/gate candidate because its validation score is lower than static-lag on seed43. This is a useful diagnosis: the next gain depends on better validation-aligned local routing, not on selecting by test behavior.
- The next algorithmic step should not be more static lag correlation. It should learn validation-aligned fault-family path prototypes, ideally with per-class or per-sample admission that can reject harmful family/long-path evidence.

Artifacts:

- `knowledge_exports/tep_cls_k8_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_staticlag_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_staticlag_l1w025_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_multihop_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_multihop010_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_family3w025_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_family3w025_gate020_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_algorithmic_path_candidates_gpu_burden/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_algorithmic_path_candidates_v2_gpu_burden/ms_gse_rpf_validation_admission.md`
