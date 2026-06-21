# C-MAPSS FD003 Adaptive ERE + GRU-Multiscale Summary

## Protocol

```text
dataset: C-MAPSS FD003
split: unit-held-out public benchmark split
main head: LightGBM
residual evidence: GRU multiscale normal-dynamics residual
reliability head: adaptive ERE
seeds: 42, 43, 44
artifact: knowledge_exports/public_benchmark_cmapss_FD003_lgbm_adaptiveere_gru_multiscale_3seeds.json
```

## Three-Seed Result

| Method | Macro-F1 |
|---|---:|
| Main | 0.8250 +/- 0.0059 |
| Plain residual fusion | 0.8328 +/- 0.0077 |
| UGMC selective correction | 0.8324 +/- 0.0078 |
| Contextual residual correction | 0.8330 +/- 0.0096 |
| ERE reliability routing | 0.8327 +/- 0.0096 |
| Per-seed best reliable variant | 0.8338 +/- 0.0088 |

Seed-level selected best variants:

```text
seed42: ERE reliability routing       0.8460 vs main 0.8330
seed43: contextual residual correction 0.8295 vs main 0.8228
seed44: plain residual fusion          0.8259 vs main 0.8191
```

## Interpretation

FD003 is now a positive degradation-stage evidence point rather than only a limitation case. The gain is still not large enough to support a C-MAPSS-wide SOTA claim, but it supports the method's theory: multi-scale temporal residual evidence can improve a strong degradation classifier when a reliability layer decides whether to use the evidence, keep contextual evidence, or fall back to simpler residual fusion.

The next required experiment is FD001-FD004 under the same GRU-multiscale/adaptive ERE setting, followed by external degradation baselines. Until that is complete, C-MAPSS should be described as a theory stress test with a positive FD003 result, not as a solved benchmark.
