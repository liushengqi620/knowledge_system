# C-MAPSS FD001/FD003 Adaptive ERE + GRU-Multiscale Summary

## Protocol

```text
datasets: C-MAPSS FD001 and FD003
split: unit-held-out public benchmark split
main head: LightGBM
residual evidence: GRU multiscale normal-dynamics residual
reliability head: adaptive ERE
seeds: 42, 43, 44
artifacts:
  knowledge_exports/public_benchmark_cmapss_FD001_lgbm_adaptiveere_gru_multiscale_3seeds.json
  knowledge_exports/public_benchmark_cmapss_FD003_lgbm_adaptiveere_gru_multiscale_3seeds.json
```

## Three-Seed Results

| Subset | Main | Best Reliable Variant | Delta | Seed-Level Best Modes |
|---|---:|---:|---:|---|
| FD001 | 0.7786 +/- 0.0175 | 0.7909 +/- 0.0184 | +0.0123 | plain, UGMC, ERE |
| FD003 | 0.8250 +/- 0.0059 | 0.8338 +/- 0.0088 | +0.0088 | ERE, contextual, plain |
| FD001+FD003 pooled | 0.8018 +/- 0.0266 | 0.8124 +/- 0.0258 | +0.0106 | adaptive per-seed routing |

## Interpretation

The positive C-MAPSS evidence now covers two subsets instead of one. FD001 shows that the GRU-multiscale temporal residual family improves the lower baseline setting, while FD003 shows the same family improves the more stable single-condition degradation setting. The important modeling conclusion is that no single correction mode dominates all seeds: the useful candidate changes among plain residual fusion, UGMC, contextual residual correction, and ERE. This supports the paper's reliability thesis more strongly than a fixed post-hoc rule would.

The remaining C-MAPSS risk is FD002/FD004, where multi-condition operating regimes have historically caused negative transfer. The next experiment should run the same configuration on FD002 and FD004 and report whether adaptive ERE produces true gains or only safe abstention.
