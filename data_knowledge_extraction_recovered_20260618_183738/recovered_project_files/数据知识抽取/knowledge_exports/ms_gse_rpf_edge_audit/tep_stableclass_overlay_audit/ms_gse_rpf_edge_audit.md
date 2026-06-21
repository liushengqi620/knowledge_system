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
| stableclass_overlay | 3 | -0.0038 +/- 0.0142 | -0.0018 +/- 0.0037 | -0.0041 +/- 0.0032 | -0.0014 +/- 0.0275 | -0.0014 +/- 0.0058 | 0.1875 |
| proposal_s050 | 3 | -0.0003 +/- 0.0042 | -0.0002 +/- 0.0045 | -0.0011 +/- 0.0006 | -0.0056 +/- 0.0179 | -0.0079 +/- 0.0029 | 0.0179 |

## Candidate: stableclass_overlay

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0403 +/- 0.0279 |
| 16 | -0.0395 +/- 0.0668 |
| 0 | -0.0196 +/- 0.0235 |
| 10 | -0.0033 +/- 0.0982 |
| 3 | 0.0258 +/- 0.0590 |
| 15 | 0.0687 +/- 0.0913 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_20 -> xmeas_19 | 1 | 0.3173 | 0.0000 | 0.0218 |
| xmeas_19 -> xmv_09 | 1 | 0.2959 | 0.3571 | 0.2585 |
| xmv_10 -> xmeas_07 | 1 | 0.2331 | 0.0000 | 0.1581 |
| xmv_10 -> xmeas_25 | 1 | 0.2328 | 0.0000 | 0.1513 |
| xmeas_18 -> xmv_09 | 1 | 0.2254 | 0.5306 | 0.5434 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`

## Candidate: proposal_s050

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0593 +/- 0.1696 |
| 0 | -0.0233 +/- 0.0198 |
| 9 | -0.0154 +/- 0.0592 |
| 3 | -0.0122 +/- 0.0456 |
| 10 | 0.0171 +/- 0.0299 |
| 15 | 0.0594 +/- 0.0503 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_08 -> xmv_05 | 2 | 0.2830 | 0.0000 | 0.7937 |
| xmv_10 -> xmeas_25 | 1 | 0.3018 | 0.0000 | 0.5043 |
| xmeas_01 -> xmeas_07 | 1 | 0.2365 | 0.0000 | 0.7487 |
| xmeas_23 -> xmv_11 | 1 | 0.2204 | 0.4583 | 0.5527 |
| xmeas_31 -> xmv_11 | 1 | 0.1993 | 0.0000 | 0.8811 |
| xmeas_34 -> xmv_11 | 1 | 0.1636 | 0.0000 | 0.5867 |
| xmv_02 -> xmv_05 | 1 | 0.1608 | 0.0000 | 0.8261 |
| xmv_10 -> xmeas_12 | 1 | 0.1508 | 0.0000 | 0.5984 |
| xmeas_21 -> xmv_10 | 1 | 0.1501 | 0.0000 | 0.2732 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
