# MS-GSE + RPF Edge/Path Audit

- dataset: tep
- target: event_quality_class_id
- variant: full
- low-tail quantile: 0.25

## Baseline

| Runs | Val Macro-F1 | Test Macro-F1 | Test Bal. Acc. |
|---:|---:|---:|---:|
| 3 | 0.7393 +/- 0.0114 | 0.6361 +/- 0.0051 | 0.6477 +/- 0.0044 |

## Baseline Low-Tail Classes

| Class | Val F1 | Runs |
|---|---:|---:|
| 9 | 0.2377 +/- 0.0550 | 3 |
| 15 | 0.2418 +/- 0.0757 | 3 |
| 3 | 0.2431 +/- 0.0174 | 3 |
| 10 | 0.2571 +/- 0.0740 | 3 |
| 16 | 0.3546 +/- 0.0377 | 3 |
| 0 | 0.4157 +/- 0.0091 | 3 |

## Candidate Summary

| Candidate | Runs | Val Gain | Test Gain | Test Bal. Gain | Low-Tail Val Gain | Low-Tail Test Gain | Path Jaccard |
|---|---:|---:|---:|---:|---:|---:|---:|
| class_staticlag_l3w025 | 3 | -0.0086 +/- 0.0121 | -0.0055 +/- 0.0010 | -0.0024 +/- 0.0028 | -0.0305 +/- 0.0341 | -0.0093 +/- 0.0040 | 0.0755 |

## Candidate: class_staticlag_l3w025

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0819 +/- 0.1146 |
| 3 | -0.0779 +/- 0.0220 |
| 9 | -0.0600 +/- 0.0156 |
| 15 | -0.0128 +/- 0.0356 |
| 10 | 0.0155 +/- 0.1223 |
| 0 | 0.0338 +/- 0.0115 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | 1 | 0.3929 | 0.5248 | 0.2164 |
| xmv_10 -> xmeas_25 | 1 | 0.3559 | 0.0000 | 0.3306 |
| xmeas_26 -> xmeas_18 | 1 | 0.2844 | 0.0000 | 0.4744 |
| xmv_05 -> xmeas_10 | 1 | 0.2836 | 0.0000 | 0.2412 |
| xmeas_13 -> xmeas_28 | 1 | 0.2312 | 0.0000 | 0.2942 |
| xmeas_21 -> xmeas_01 | 1 | 0.2225 | 0.0000 | 0.3320 |
| xmeas_10 -> xmeas_21 | 1 | 0.2044 | 0.0000 | 0.0849 |
| xmeas_23 -> xmeas_30 | 1 | 0.1938 | 0.0000 | 0.4029 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
