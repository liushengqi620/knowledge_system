# TEP Protocol Audit

## Finding

The valid TEP mechanism-evidence protocol uses the 52 raw process variables as the KIEP-GL graph interface. The archived strong run uses:

```text
max_rows=20000
feature_set=raw
split=metadata
tree_estimators=160
tree_max_depth=16
tree_min_samples_leaf=1
prior=expert_llm
weak_specialist=True
pairwise_recall_guard=True
support_gated_persistence=True
temporal_smoothing=True
seeds=42,43,44
```

The matched no-pairwise rerun keeps the same protocol and changes only `pairwise_recall_guard=False`.

## Matched Result

| Variant | Target-F1 | Sample Macro-F1 | Event Macro-Recall | Path Hit Rate |
|---|---:|---:|---:|---:|
| pairwise/support-gated mechanism evidence | 0.9520 +/- 0.0070 | 0.9434 +/- 0.0068 | 0.8413 +/- 0.0224 | 0.7143 +/- 0.0000 |
| no pairwise recall guard | 0.9122 +/- 0.0134 | 0.9025 +/- 0.0167 | 0.8571 +/- 0.0778 | 0.7143 +/- 0.0000 |

## Protocol Guard

The failed 5k smoke run used `feature_set=window`, expanding the input from 52 raw variables to 832 derived lag/statistical features. That breaks the variable-level semantics of the TEP expert/LLM graph prior. The code now rejects TEP mechanism experiments that combine window features with expert/LLM mechanism evidence. Window dynamics should be introduced through sequence heads or residual auxiliary branches, not by replacing the graph interface.

## Paper Use

Use TEP as the primary positive mechanism benchmark. Report the matched no-pairwise ablation as the main evidence that pairwise/support-gated mechanism evidence is not decorative post-processing.
