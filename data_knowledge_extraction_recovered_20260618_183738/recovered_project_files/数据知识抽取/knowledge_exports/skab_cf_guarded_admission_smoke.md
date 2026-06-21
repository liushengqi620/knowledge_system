# SKAB CF-Guarded Admission Smoke Test

This smoke test verifies that `CF_k` can be used as a pre-admission edge guard in the SKAB dynamic LLM graph route. It is not a final AAAI ablation because it uses one seed, one perturbation mode, and a low-budget setting.

## Protocol

| Item | Value |
|---|---|
| Source edges | `public_benchmark_skab_dynamic_llm_api_seed42_e8_learned_reliability_probe2_t045_k4.json` |
| Output JSON | `public_benchmark_skab_dynamic_llm_api_seed42_e3_cf_guard_reverse_probe1.json` |
| Seed | 42 |
| Sequence epochs | 3 |
| Edge probe epochs | 1 |
| Guard mode | `reverse_direction` |
| Minimum CF drop | `0.01` Macro-F1 |
| API use | none; dynamic edges loaded from prior result |

## Result

| Variant | Macro-F1 | Delta vs Baseline | Binary F1 | FAR | MAR | Input Edges | Kept Edges | FAR Rejects | CF Rejects |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CF-guarded smoke | 0.8676 | +0.0015 | 0.8325 | 12.14 | 12.61 | 4 | 1 | 2 | 1 |

The baseline Macro-F1 in this low-budget run is `0.8662`. The CF-guarded route keeps only `Current -> Pressure` and rejects one edge by the pre-admission counterfactual guard.

## Interpretation

This smoke test proves that the implementation can use counterfactual sensitivity before deployment-time edge admission. It turns `CF_k` from a post-hoc perturbation diagnostic into an executable admission condition. The result is intentionally labeled as smoke evidence: the paper still needs an e8/e10, three-seed, multi-mode CF-guarded ablation against the current no-CF admission diagnostic.
