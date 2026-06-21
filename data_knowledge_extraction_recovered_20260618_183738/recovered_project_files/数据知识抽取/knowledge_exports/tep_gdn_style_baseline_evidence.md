# TEP GDN-Style Baseline Evidence

Date: 2026-06-16

## Purpose

This report adds a preliminary GDN-style supervised sequence graph baseline to the strict TEP protocol family. The goal is to start closing the missing strong-baseline gap identified in the AAAI readiness audit, not to claim that the low-budget run is competitive with the strict mechanism model.

## Implementation

The new `gdn` sequence head is implemented in `Scripts/tep_sequence_heads.py`.

It treats each process variable as a graph node:

```text
window x in R^{T x F}
per-variable temporal encoder -> node states h_j
learnable node embeddings -> top-k feature graph A
graph aggregation A h -> neighbor states
classification from mean pooled [h_j, A h_j, h_j - A h_j]
```

This creates a supervised GDN-style comparator under the same TEP sequence protocol. It can also receive the existing external lagged mechanism graph through the same ablation runner:

```text
no_graph
all_lagged
reliable_lagged
residual_gated_lagged
```

## Smoke Check

Command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model gdn --seeds 42 --max-rows 2000 --window-size 32 --hidden-dim 32 --epochs 1 --batch-size 128 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --output knowledge_exports\tep_sequence_graph_ablation_gdn_style_smoke_seed42_e1_2k.json
```

Result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall |
|---|---:|---:|---:|
| no_graph | 0.0483 | 0.0461 | 0.1429 |
| all_lagged | 0.0581 | 0.0554 | 0.1429 |
| reliable_lagged | 0.0597 | 0.0570 | 0.1429 |
| residual_gated_lagged | 0.0578 | 0.0552 | 0.1429 |

Interpretation: the smoke run only verifies that the full training, graph admission, metric, and report pipeline works.

## 5k / 3 Epoch / 3 Seed Preliminary Result

Command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model gdn --seeds 42,43,44 --max-rows 5000 --window-size 32 --hidden-dim 48 --epochs 3 --batch-size 192 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --resume --output knowledge_exports\tep_sequence_graph_ablation_gdn_style_seed42_e3_5k.json
```

Result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|
| no_graph | 0.1461 +/- 0.0221 | 0.1409 +/- 0.0220 | 0.1905 +/- 0.0000 | n/a | n/a |
| all_lagged | 0.1345 +/- 0.0162 | 0.1298 +/- 0.0158 | 0.1905 +/- 0.0000 | 79 | 0 |
| reliable_lagged | 0.1401 +/- 0.0178 | 0.1348 +/- 0.0174 | 0.1587 +/- 0.0224 | 40 | 39 |
| residual_gated_lagged | 0.1448 +/- 0.0190 | 0.1390 +/- 0.0182 | 0.1905 +/- 0.0389 | 40 | 39 |

Per-seed target-F1:

| Seed | no_graph | all_lagged | reliable_lagged | residual_gated_lagged |
|---:|---:|---:|---:|---:|
| 42 | 0.1641 | 0.1535 | 0.1586 | 0.1681 |
| 43 | 0.1150 | 0.1138 | 0.1161 | 0.1216 |
| 44 | 0.1592 | 0.1363 | 0.1455 | 0.1447 |

## Conclusion

The preliminary GDN-style result is a useful negative/diagnostic baseline:

- GDN-style supervised sequence graph learning is not competitive with the strict mechanism/KIEP-GL result under the current low-budget setting.
- Directly injecting all lagged mechanism edges hurts the GDN-style head.
- Reliability pruning reduces the damage relative to all-edge injection.
- Residual-gated lagged graph evidence is safer than direct graph injection, but at this budget it does not yet beat the no-graph GDN mean.

This reinforces the current paper claim: mechanism evidence should not be injected just because it is graph-shaped. It needs a reliable intervention route and enough validation evidence before it is allowed to correct the main model.

## Next GDN-Specific Steps

Before using GDN-style results as a serious TEP baseline, run a stronger setting:

```text
max_rows=20000
epochs=10
seeds=42,43,44
hidden_dim=64
normal_residual_features enabled
weak-class rerank enabled
```

If the stronger GDN setting remains far below the strict mechanism model, it can be reported as a matched strong baseline showing that generic graph neural sequence heads do not solve TEP weak-class diagnosis without reliability-calibrated mechanism evidence.

## Recovery Validation on 2026-06-20

The recovered workspace had lost the implementation referenced above. The following code paths have been restored and smoke-tested:

```text
Scripts/tep_sequence_heads.py
  _build_sequence_module("gdn")
  _GDNStyleSequenceModule
  _ResidualGatedSequenceModule
  train_sequence_model(..., lagged_graph_fusion_mode="residual_channel")

Scripts/run_tep_sequence_graph_ablation.py
  --model gdn
  --include-residual-gated
  --device auto
  Windows long-path-safe result writing
```

CUDA smoke command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model gdn --seeds 42 --max-rows 600 --window-size 16 --hidden-dim 24 --epochs 1 --batch-size 64 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --device auto --output knowledge_exports\tep_gdn_smoke.json
```

Smoke result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|
| no_graph | 0.0042 | 0.0040 | 0.0476 | n/a | n/a | n/a |
| all_lagged | 0.0041 | 0.0039 | 0.0476 | 79 | 79 | 0 |
| reliable_lagged | 0.0041 | 0.0039 | 0.0476 | 79 | 40 | 39 |
| residual_gated_lagged | 0.0072 | 0.0068 | 0.0476 | 79 | 40 | 39 |

This is only a code-path and diagnostics validation. It confirms CUDA execution, fallback TEP expert+LLM edge construction, reliability pruning, residual-gated graph routing, and project-local result writing. It does not replace the required 20k/10epoch/3-seed GDN baseline.

Additional 2k/1epoch CUDA smoke:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model gdn --seeds 42 --max-rows 2000 --window-size 32 --hidden-dim 32 --epochs 1 --batch-size 128 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --device auto --output knowledge_exports\tep_gdn_2k_e1_smoke.json
```

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall |
|---|---:|---:|---:|
| no_graph | 0.0184 | 0.0175 | 0.0476 |
| all_lagged | 0.0259 | 0.0247 | 0.0952 |
| reliable_lagged | 0.0261 | 0.0249 | 0.0952 |
| residual_gated_lagged | 0.0233 | 0.0222 | 0.0476 |

At 2k/1epoch, direct and reliability-pruned graph input is directionally positive for the restored GDN-style head, while residual-gated routing is not yet better than direct graph use. This reinforces that residual gating should be judged under the longer matched budget, not under one-epoch smoke.

## 5k / 3 Epoch / 3 Seed Recovered Intermediate Result

Command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model gdn --seeds 42,43,44 --max-rows 5000 --window-size 32 --hidden-dim 48 --epochs 3 --batch-size 192 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --device auto --output knowledge_exports\tep_gdn_5k_e3_recovered.json
```

Result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|
| no_graph | 0.0941 +/- 0.0215 | 0.0898 +/- 0.0205 | 0.1905 +/- 0.0389 | n/a | n/a |
| all_lagged | 0.0926 +/- 0.0192 | 0.0884 +/- 0.0184 | 0.2222 +/- 0.0449 | 79 | 0 |
| reliable_lagged | 0.0965 +/- 0.0182 | 0.0922 +/- 0.0174 | 0.2063 +/- 0.0594 | 40 | 39 |
| residual_gated_lagged | 0.1002 +/- 0.0202 | 0.0957 +/- 0.0193 | 0.2063 +/- 0.0594 | 40 | 39 |

Per-seed target-F1:

| Seed | no_graph | all_lagged | reliable_lagged | residual_gated_lagged |
|---:|---:|---:|---:|---:|
| 42 | 0.0650 | 0.0674 | 0.0729 | 0.0723 |
| 43 | 0.1007 | 0.0963 | 0.0995 | 0.1089 |
| 44 | 0.1165 | 0.1141 | 0.1173 | 0.1194 |

Interpretation: under the recovered implementation, all-edge graph smoothing is slightly harmful on average, reliability pruning turns the graph channel positive, and residual-gated lagged evidence is the best mean variant. The absolute score is still far below the strict mechanism model, so this remains a strong negative baseline and a path-fusion ablation, not a replacement backbone.

## 20k / 10 Epoch / 3 Seed Recovered Full-Budget Result

Command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model gdn --seeds 42,43,44 --max-rows 20000 --window-size 32 --hidden-dim 64 --epochs 10 --batch-size 256 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --device auto --output knowledge_exports\tep_gdn_20k_e10_recovered.json
```

Result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|
| no_graph | 0.3922 +/- 0.0510 | 0.3820 +/- 0.0432 | 0.4603 +/- 0.0224 | n/a | n/a |
| all_lagged | 0.4051 +/- 0.0518 | 0.3954 +/- 0.0456 | 0.4603 +/- 0.0809 | 79 | 0 |
| reliable_lagged | 0.4149 +/- 0.0502 | 0.4037 +/- 0.0434 | 0.4921 +/- 0.0224 | 40 | 39 |
| residual_gated_lagged | 0.5179 +/- 0.0372 | 0.4993 +/- 0.0328 | 0.5238 +/- 0.0389 | 40 | 39 |

Per-seed target-F1:

| Seed | no_graph | all_lagged | reliable_lagged | residual_gated_lagged |
|---:|---:|---:|---:|---:|
| 42 | 0.4340 | 0.4636 | 0.4728 | 0.5539 |
| 43 | 0.4223 | 0.4141 | 0.4214 | 0.5332 |
| 44 | 0.3204 | 0.3377 | 0.3504 | 0.4667 |

Interpretation: full-budget GDN makes the residual-gated lagged graph channel materially positive: `+0.1257` Target-F1 over the GDN no-graph variant and `+0.1030` over direct reliable graph smoothing. This is strong evidence for the paper's path-fusion claim, even though the GDN family remains far below the strict mechanism model.
