# TEP MTAD-GAT-Style Baseline Evidence

Date: 2026-06-16

## Purpose

This report adds a preliminary MTAD-GAT-style supervised temporal-graph attention baseline to the strict TEP sequence protocol family. It complements the GDN-style baseline by testing a model family that combines temporal encoding with feature-level attention.

## Implementation

The new `mtad_gat` sequence head is implemented in `Scripts/tep_sequence_heads.py`.

It uses:

```text
window x in R^{T x F}
bidirectional GRU -> temporal context
feature tokens from [last, mean, slope] + feature embeddings
multi-head feature attention -> graph-attentive variable representation
temporal gate -> fusion of temporal context and feature-attention context
classification head -> class logits
```

This is not an official MTAD-GAT reproduction. It is a strict-protocol, supervised MTAD-GAT-style comparator designed to test whether generic temporal graph attention can compete with the reliability-calibrated mechanism model under the same TEP split and metrics.

## Smoke Check

Command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model mtad_gat --seeds 42 --max-rows 2000 --window-size 32 --hidden-dim 32 --epochs 1 --batch-size 128 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --output knowledge_exports\tep_sequence_graph_ablation_mtad_gat_style_smoke_seed42_e1_2k.json
```

Result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|
| no_graph | 0.0413 | 0.0405 | 0.0000 | n/a | n/a |
| all_lagged | 0.0428 | 0.0420 | 0.0000 | 79 | 0 |
| reliable_lagged | 0.0443 | 0.0438 | 0.0000 | 40 | 39 |
| residual_gated_lagged | 0.0452 | 0.0444 | 0.0476 | 40 | 39 |

## Interpretation

The smoke result is not competitive and should not be used for performance claims. Its value is pipeline evidence:

- The TEP runner now supports a second graph-temporal strong-baseline family beyond GDN-style.
- The same external lagged mechanism graph can be injected as all-edge, reliability-pruned, and residual-gated evidence.
- Even at smoke scale, residual-gated evidence is the best MTAD-GAT-style variant, which is directionally consistent with TCN/GRU/FT/GDN findings.

## Next MTAD-GAT-Specific Steps

Run a matched stronger setting:

```text
max_rows=5000 or 10000 for intermediate trend
epochs=3 to 5
seeds=42,43,44
hidden_dim=48 or 64
```

Then decide whether a full 20k/10epoch run is worthwhile. If MTAD-GAT-style remains far below the strict mechanism model, it still serves as a useful strong negative baseline showing that generic temporal graph attention is insufficient without reliability-calibrated mechanism admission.

## Recovery Validation on 2026-06-20

The recovered workspace had lost the MTAD-GAT-style implementation referenced above. The following code paths have been restored and smoke-tested:

```text
Scripts/tep_sequence_heads.py
  _build_sequence_module("mtad_gat")
  _MTADGATStyleSequenceModule
  _ResidualGatedSequenceModule

Scripts/run_tep_sequence_graph_ablation.py
  --model mtad_gat
  --include-residual-gated
  --device auto
  Windows long-path-safe result writing
```

CUDA smoke command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model mtad_gat --seeds 42 --max-rows 600 --window-size 16 --hidden-dim 24 --epochs 1 --batch-size 64 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --device auto --output knowledge_exports\tep_mtad_smoke.json
```

Smoke result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Candidate Edges | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|---:|
| no_graph | 0.0279 | 0.0266 | 0.0476 | n/a | n/a | n/a |
| all_lagged | 0.0304 | 0.0290 | 0.0952 | 79 | 79 | 0 |
| reliable_lagged | 0.0291 | 0.0278 | 0.0952 | 79 | 40 | 39 |
| residual_gated_lagged | 0.0280 | 0.0267 | 0.0476 | 79 | 40 | 39 |

This is only a code-path and diagnostics validation. It confirms CUDA execution, MTAD-GAT-style temporal-feature attention, fallback TEP expert+LLM edge construction, reliability pruning, and project-local result writing. It does not replace the required stronger 5k/10k trend or full 20k/10epoch/3-seed MTAD-GAT-style baseline.

Additional 2k/1epoch CUDA smoke:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model mtad_gat --seeds 42 --max-rows 2000 --window-size 32 --hidden-dim 32 --epochs 1 --batch-size 128 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --device auto --output knowledge_exports\tep_mtad_2k_e1_smoke.json
```

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall |
|---|---:|---:|---:|
| no_graph | 0.0399 | 0.0380 | 0.0952 |
| all_lagged | 0.0463 | 0.0442 | 0.0476 |
| reliable_lagged | 0.0429 | 0.0409 | 0.0952 |
| residual_gated_lagged | 0.0373 | 0.0356 | 0.0952 |

At 2k/1epoch, all-lagged and reliability-pruned graph input are above no-graph for the restored MTAD-GAT-style head, while residual-gated routing is not yet positive. This should be treated as early optimization evidence only; longer training is required before drawing method conclusions.

## 5k / 3 Epoch / 3 Seed Recovered Intermediate Result

Command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model mtad_gat --seeds 42,43,44 --max-rows 5000 --window-size 32 --hidden-dim 48 --epochs 3 --batch-size 192 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --device auto --output knowledge_exports\tep_mtad_5k_e3_recovered.json
```

Result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|
| no_graph | 0.2693 +/- 0.0071 | 0.2593 +/- 0.0076 | 0.3651 +/- 0.0594 | n/a | n/a |
| all_lagged | 0.2713 +/- 0.0093 | 0.2611 +/- 0.0075 | 0.3651 +/- 0.0449 | 79 | 0 |
| reliable_lagged | 0.2679 +/- 0.0079 | 0.2583 +/- 0.0061 | 0.3175 +/- 0.0449 | 40 | 39 |
| residual_gated_lagged | 0.2780 +/- 0.0088 | 0.2677 +/- 0.0113 | 0.3651 +/- 0.0594 | 40 | 39 |

Per-seed target-F1:

| Seed | no_graph | all_lagged | reliable_lagged | residual_gated_lagged |
|---:|---:|---:|---:|---:|
| 42 | 0.2776 | 0.2845 | 0.2791 | 0.2782 |
| 43 | 0.2699 | 0.2636 | 0.2617 | 0.2887 |
| 44 | 0.2604 | 0.2659 | 0.2629 | 0.2672 |

Interpretation: residual-gated lagged evidence is the best mean variant for the restored MTAD-GAT-style head, even though the margin is modest. This supports the paper claim that graph evidence is safer as a residual verifier than as unconditional feature smoothing. The absolute score remains far below the strict mechanism model, so MTAD-GAT-style should be used as a matched strong baseline rather than the proposed main backbone.

## 20k / 10 Epoch / 3 Seed Recovered Full-Budget Result

Command:

```text
python Scripts\run_tep_sequence_graph_ablation.py --model mtad_gat --seeds 42,43,44 --max-rows 20000 --window-size 32 --hidden-dim 64 --epochs 10 --batch-size 256 --normal-pretrain-epochs 0 --graph-strength 0.15 --reliability-threshold 0.70 --max-edges 40 --include-residual-gated --device auto --output knowledge_exports\tep_mtad_20k_e10_recovered.json
```

Result:

| Variant | Target-F1 | Macro-F1 | Event Macro-Recall | Matched Edges | Pruned Edges |
|---|---:|---:|---:|---:|---:|
| no_graph | 0.6369 +/- 0.0050 | 0.6119 +/- 0.0035 | 0.8413 +/- 0.0224 | n/a | n/a |
| all_lagged | 0.6337 +/- 0.0031 | 0.6080 +/- 0.0024 | 0.8254 +/- 0.0224 | 79 | 0 |
| reliable_lagged | 0.6321 +/- 0.0021 | 0.6066 +/- 0.0006 | 0.8413 +/- 0.0224 | 40 | 39 |
| residual_gated_lagged | 0.6447 +/- 0.0038 | 0.6201 +/- 0.0025 | 0.8254 +/- 0.0224 | 40 | 39 |

Per-seed target-F1:

| Seed | no_graph | all_lagged | reliable_lagged | residual_gated_lagged |
|---:|---:|---:|---:|---:|
| 42 | 0.6300 | 0.6327 | 0.6302 | 0.6421 |
| 43 | 0.6419 | 0.6380 | 0.6350 | 0.6502 |
| 44 | 0.6388 | 0.6306 | 0.6311 | 0.6419 |

Interpretation: full-budget MTAD-GAT-style is the strongest tree-free temporal graph baseline so far, but still trails the strict mechanism model by `0.3102` Target-F1. Direct all-edge and reliable smoothing are slightly harmful, while residual-gated lagged evidence gives a small but stable `+0.0078` Target-F1 over no graph. This is useful strong-baseline evidence and supports residual graph evidence as a controlled correction rather than unconditional graph smoothing.
