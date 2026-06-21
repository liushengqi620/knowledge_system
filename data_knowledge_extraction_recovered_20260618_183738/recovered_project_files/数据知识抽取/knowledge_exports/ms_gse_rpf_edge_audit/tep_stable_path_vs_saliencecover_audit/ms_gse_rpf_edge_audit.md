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
| stable_path_w025_classoff | 3 | -0.0044 +/- 0.0068 | -0.0021 +/- 0.0036 | -0.0025 +/- 0.0035 | -0.0273 +/- 0.0100 | -0.0006 +/- 0.0033 | 0.1667 |
| salience_cover010 | 3 | -0.0024 +/- 0.0019 | -0.0052 +/- 0.0045 | -0.0043 +/- 0.0027 | -0.0303 +/- 0.0123 | -0.0207 +/- 0.0111 | 0.0962 |

## Candidate: stable_path_w025_classoff

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0652 +/- 0.1001 |
| 0 | -0.0464 +/- 0.0470 |
| 15 | -0.0368 +/- 0.0556 |
| 9 | -0.0163 +/- 0.0380 |
| 3 | -0.0030 +/- 0.0452 |
| 10 | 0.0036 +/- 0.0921 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_28 -> xmeas_10 | 1 | 0.3333 | 0.3238 | 0.5158 |
| xmeas_32 -> xmv_02 | 1 | 0.2031 | 0.0000 | 0.2237 |
| xmeas_35 -> xmeas_13 | 1 | 0.1952 | 0.5116 | 0.6589 |
| xmv_10 -> xmeas_25 | 1 | 0.1760 | 0.0000 | 0.1351 |
| xmv_11 -> xmeas_20 | 1 | 0.1655 | 0.0000 | 0.7346 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`

## Candidate: salience_cover010

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 0 | -0.0697 +/- 0.0427 |
| 16 | -0.0576 +/- 0.0563 |
| 9 | -0.0479 +/- 0.0155 |
| 15 | -0.0291 +/- 0.0368 |
| 10 | 0.0101 +/- 0.0530 |
| 3 | 0.0125 +/- 0.0277 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_36 -> xmeas_38 | 1 | 0.4252 | 0.0000 | 0.0575 |
| xmeas_38 -> xmv_05 | 1 | 0.2598 | 0.0000 | 0.0843 |
| xmeas_29 -> xmeas_30 | 1 | 0.2540 | 0.0000 | 0.0514 |
| xmeas_19 -> xmv_09 | 1 | 0.2491 | 0.2282 | 0.0774 |
| xmeas_25 -> xmv_05 | 1 | 0.2279 | 0.0000 | 0.1399 |
| xmv_05 -> xmeas_18 | 1 | 0.2273 | 0.0000 | 0.0812 |
| xmv_02 -> xmv_05 | 1 | 0.2272 | 0.0000 | 0.0662 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0571 +/- 0.0002`
- uncapped edges mean: `966.7`
- corroborated edges mean: `136.7`
- single-view edges mean: `17.7`
- top-edge family counts: `{'dynamic': 120, 'structural': 112, 'task': 64}`
