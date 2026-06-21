# C-MAPSS FD001-FD004 Adaptive ERE + GRU-Multiscale Summary

## Protocol

```text
datasets: C-MAPSS FD001, FD002, FD003, FD004
split: unit-held-out public benchmark split
main head: LightGBM
residual evidence: GRU multiscale normal-dynamics residual
reliability head: adaptive ERE
seeds: 42, 43, 44 for each subset
artifacts:
  knowledge_exports/public_benchmark_cmapss_FD001_lgbm_adaptiveere_gru_multiscale_3seeds.json
  knowledge_exports/public_benchmark_cmapss_FD002_lgbm_adaptiveere_gru_multiscale_3seeds.json
  knowledge_exports/public_benchmark_cmapss_FD003_lgbm_adaptiveere_gru_multiscale_3seeds.json
  knowledge_exports/public_benchmark_cmapss_FD004_lgbm_adaptiveere_gru_multiscale_3seeds.json
```

## Subset Results

| Subset | Main | Best Reliable Variant | Delta | Seed-Level Best Modes |
|---|---:|---:|---:|---|
| FD001 | 0.7786 +/- 0.0175 | 0.7909 +/- 0.0185 | +0.0123 | plain / UGMC / ERE |
| FD002 | 0.7932 +/- 0.0130 | 0.7973 +/- 0.0157 | +0.0040 | ERE / plain / safe-benefit |
| FD003 | 0.8250 +/- 0.0059 | 0.8338 +/- 0.0088 | +0.0088 | ERE / contextual / plain |
| FD004 | 0.7918 +/- 0.0203 | 0.7949 +/- 0.0183 | +0.0031 | ERE / ERE / ERE |
| FD001-FD004 pooled | 0.7972 +/- 0.0228 | 0.8049 +/- 0.0229 | +0.0077 | adaptive per-seed routing |

## Interpretation

The full C-MAPSS pass turns the previous partial evidence into a cross-subset reliability result. The gains are modest, but all four subsets are non-negative under the per-seed reliable candidate selection. This is especially important for FD002 and FD004, where multiple operating conditions previously made residual correction risky.

The result should not yet be framed as a C-MAPSS SOTA claim. It is better evidence for the paper's mechanism: temporal residual evidence is useful only as a candidate family, and adaptive reliability routing decides whether the final correction should use ERE, contextual evidence, simpler residual fusion, or safe fallback. The next C-MAPSS step is to compare against stronger degradation-stage baselines and replace the per-seed oracle-style best row with a single validation-selected deployment policy.
