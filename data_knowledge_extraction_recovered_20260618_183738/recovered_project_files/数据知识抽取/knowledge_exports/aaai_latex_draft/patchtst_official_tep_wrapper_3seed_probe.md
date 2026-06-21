# PatchTST Official-Source TEP Wrapper

- Status: official_source_adapted_wrapper_executed
- Claim boundary: Official PatchTST supervised source backbone adapted with a lightweight TEP classification head; not an official PatchTST paper benchmark score.

| Seed | Target-F1 | Macro-F1 | Event Macro-Recall | Train sec. |
|---|---:|---:|---:|---:|
| 42 | 0.0191 | 0.0237 | 0.0476 | 0.31 |
| 43 | 0.0472 | 0.0494 | 0.0952 | 0.03 |
| 44 | 0.0233 | 0.0240 | 0.0952 | 0.03 |

## Summary

```json
{
  "target_defect_macro_f1": {
    "mean": 0.02987301419875964,
    "std": 0.01233699203512936
  },
  "macro_f1": {
    "mean": 0.03235227550383469,
    "std": 0.012053519586602038
  },
  "event_macro_recall": {
    "mean": 0.07936507936507936,
    "std": 0.022447834323382456
  },
  "train_seconds": {
    "mean": 0.1213788668004175,
    "std": 0.13369397565666166
  }
}
```
