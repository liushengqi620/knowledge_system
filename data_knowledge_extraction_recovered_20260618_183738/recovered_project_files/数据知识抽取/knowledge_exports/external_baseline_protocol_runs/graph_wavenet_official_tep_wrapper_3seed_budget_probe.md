# Graph WaveNet Official-Source TEP Wrapper

- Status: official_source_adapted_wrapper_executed
- Claim boundary: Official Graph WaveNet source backbone adapted with a lightweight TEP classification head; not an official Graph WaveNet paper benchmark score.

| Seed | Target-F1 | Macro-F1 | Event Macro-Recall | Train sec. |
|---|---:|---:|---:|---:|
| 42 | 0.2201 | 0.2170 | 0.2381 | 13.52 |
| 43 | 0.2862 | 0.2801 | 0.2381 | 11.26 |
| 44 | 0.3497 | 0.3482 | 0.3333 | 7.94 |

## Summary

```json
{
  "target_defect_macro_f1": {
    "mean": 0.28535363559876725,
    "std": 0.05290978106305519
  },
  "macro_f1": {
    "mean": 0.28179984279516,
    "std": 0.05357616564061767
  },
  "event_macro_recall": {
    "mean": 0.2698412698412698,
    "std": 0.04489566864676492
  },
  "train_seconds": {
    "mean": 10.906443599999571,
    "std": 2.2911740602369752
  }
}
```
