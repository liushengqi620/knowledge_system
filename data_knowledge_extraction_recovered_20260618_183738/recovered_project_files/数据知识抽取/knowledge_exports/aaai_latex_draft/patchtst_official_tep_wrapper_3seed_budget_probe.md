# PatchTST Official-Source TEP Wrapper

- Status: official_source_adapted_wrapper_executed
- Claim boundary: Official PatchTST supervised source backbone adapted with a lightweight TEP classification head; not an official PatchTST paper benchmark score.

| Seed | Target-F1 | Macro-F1 | Event Macro-Recall | Train sec. |
|---|---:|---:|---:|---:|
| 42 | 0.3845 | 0.3789 | 0.4762 | 7.21 |
| 43 | 0.4126 | 0.4048 | 0.5714 | 6.38 |
| 44 | 0.4619 | 0.4488 | 0.4762 | 7.03 |

## Summary

```json
{
  "target_defect_macro_f1": {
    "mean": 0.41966028181741827,
    "std": 0.032008458145587795
  },
  "macro_f1": {
    "mean": 0.4108444927704698,
    "std": 0.028845334637731604
  },
  "event_macro_recall": {
    "mean": 0.5079365079365079,
    "std": 0.04489566864676491
  },
  "train_seconds": {
    "mean": 6.873637099983171,
    "std": 0.3594158679194774
  }
}
```
