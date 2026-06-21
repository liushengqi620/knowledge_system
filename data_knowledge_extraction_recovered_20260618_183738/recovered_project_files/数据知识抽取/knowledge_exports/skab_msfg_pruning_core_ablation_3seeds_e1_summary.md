# SKAB MSFG Pruning Core Ablation

Date: 2026-06-16

This low-budget run tests the complexity/source-pruning term in the reliability certificate. It compares the original fused MSFG edge set with the reliability-pruned KG under the same run-level splits and a lightweight `masked_tcn` sequence budget.

## Protocol

```text
Dataset: SKAB
Seeds: 42, 43, 44
Modes: original_full_msfg, full_pruned_kg
Sequence head: masked_tcn
Epochs: 1
Hidden dim: 16
Batch size: 1024
Output JSON: knowledge_exports/skab_msfg_pruning_core_ablation_3seeds_e1.json
```

## Results

| Seed | Original Macro-F1 | Pruned Macro-F1 | Delta | Original FAR | Pruned FAR | Original Fused Edges | Pruned Fused Edges |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 0.5415 | 0.7908 | +0.2493 | 33.60 | 4.68 | 13 | 9 |
| 43 | 0.6215 | 0.6624 | +0.0409 | 24.35 | 18.33 | 12 | 8 |
| 44 | 0.6348 | 0.7117 | +0.0770 | 6.04 | 27.87 | 14 | 9 |
| Mean | 0.5993 +/- 0.0412 | 0.7217 +/- 0.0529 | +0.1224 +/- 0.0910 | n/a | n/a | n/a | n/a |

## Interpretation

The pruning result is positive on all three seeds, supporting the claim that unsupported expert/source edges can harm SKAB anomaly diagnosis and should be filtered before graph evidence is admitted. Because this is an e1 low-budget run, it should be used as reliability-term evidence rather than final SOTA evidence. The next version should run the same core comparison at e3/e5 and add the remaining source-role modes: no-LLM, expert-only, LLM-only, and data-only.
