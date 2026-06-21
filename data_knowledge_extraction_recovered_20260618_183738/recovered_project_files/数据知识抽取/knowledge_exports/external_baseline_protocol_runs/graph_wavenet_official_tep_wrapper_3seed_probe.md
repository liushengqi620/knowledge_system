# Graph WaveNet Official-Source TEP Wrapper

- Status: official_source_adapted_wrapper_executed
- Claim boundary: Official Graph WaveNet source backbone adapted with a lightweight TEP classification head; not an official Graph WaveNet paper benchmark score.

| Seed | Target-F1 | Macro-F1 | Event Macro-Recall | Train sec. |
|---|---:|---:|---:|---:|
| 42 | 0.0043 | 0.0041 | 0.0476 | 0.43 |
| 43 | 0.0044 | 0.0042 | 0.0476 | 0.06 |
| 44 | 0.0038 | 0.0036 | 0.0476 | 0.06 |

## Summary

```json
{
  "target_defect_macro_f1": {
    "mean": 0.004138490345167997,
    "std": 0.0002783806759209298
  },
  "macro_f1": {
    "mean": 0.003950377147660362,
    "std": 0.0002657270088336148
  },
  "event_macro_recall": {
    "mean": 0.047619047619047616,
    "std": 0.0
  },
  "train_seconds": {
    "mean": 0.18570316668289402,
    "std": 0.1731557854015623
  }
}
```
