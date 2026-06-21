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
| edge_sieve_edgecal | 3 | -0.0069 +/- 0.0020 | -0.0040 +/- 0.0091 | -0.0019 +/- 0.0048 | -0.0140 +/- 0.0081 | -0.0056 +/- 0.0201 | 0.1489 |
| edge_overlay | 3 | -0.0053 +/- 0.0091 | -0.0058 +/- 0.0042 | -0.0051 +/- 0.0013 | -0.0028 +/- 0.0323 | -0.0131 +/- 0.0032 | 0.1400 |
| edge_pool_edgecal | 3 | -0.0040 +/- 0.0095 | -0.0054 +/- 0.0050 | -0.0066 +/- 0.0062 | -0.0161 +/- 0.0250 | -0.0076 +/- 0.0092 | 0.2667 |

## Candidate: edge_sieve_edgecal

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0619 +/- 0.0384 |
| 15 | -0.0466 +/- 0.0355 |
| 3 | -0.0336 +/- 0.0460 |
| 9 | -0.0127 +/- 0.0419 |
| 0 | 0.0183 +/- 0.0111 |
| 10 | 0.0526 +/- 0.0977 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_20 -> xmv_05 | 2 | 0.2421 | 0.6323 | 0.8827 |
| xmv_05 -> xmeas_07 | 1 | 0.3316 | 0.0000 | 0.9840 |
| xmeas_08 -> xmeas_13 | 1 | 0.2473 | 0.0000 | 0.3330 |
| xmeas_37 -> xmeas_35 | 1 | 0.2360 | 0.0000 | 0.0265 |
| xmeas_36 -> xmeas_13 | 1 | 0.2251 | 0.4946 | 0.6193 |

### Edge Prior Audit

- modes: `{'edge_sieve': 3}`
- density: `0.0735 +/- 0.0005`
- uncapped edges mean: `674.3`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{'dynamic': 279, 'structural': 100, 'task': 67}`

## Candidate: edge_overlay

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0652 +/- 0.0786 |
| 9 | -0.0613 +/- 0.0547 |
| 3 | -0.0268 +/- 0.0138 |
| 0 | -0.0211 +/- 0.0404 |
| 15 | 0.0576 +/- 0.0566 |
| 10 | 0.1003 +/- 0.1537 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_18 -> xmeas_23 | 1 | 0.2327 | 0.0000 | 0.1253 |
| xmeas_38 -> xmeas_19 | 1 | 0.2214 | 0.0000 | 0.1421 |
| xmeas_38 -> xmv_05 | 1 | 0.2084 | 0.0000 | 0.6605 |
| xmeas_28 -> xmeas_10 | 1 | 0.1740 | 0.0000 | 0.4818 |
| xmeas_08 -> xmeas_20 | 1 | 0.1693 | 0.0000 | 0.3911 |
| xmv_07 -> xmeas_19 | 1 | 0.1667 | 0.0000 | 0.1240 |
| xmv_10 -> xmeas_20 | 1 | 0.1665 | 0.0000 | 0.7142 |

### Edge Prior Audit

- modes: `{'edge_overlay': 3}`
- density: `0.0913 +/- 0.0005`
- uncapped edges mean: `247.0`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`

## Candidate: edge_pool_edgecal

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0560 +/- 0.0646 |
| 9 | -0.0531 +/- 0.0745 |
| 10 | -0.0476 +/- 0.0404 |
| 0 | 0.0025 +/- 0.0447 |
| 15 | 0.0200 +/- 0.0987 |
| 3 | 0.0378 +/- 0.0332 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_40 -> xmv_06 | 1 | 0.2562 | 0.0000 | 0.0728 |
| xmv_10 -> xmeas_07 | 1 | 0.2328 | 0.0000 | 0.1993 |
| xmeas_18 -> xmv_09 | 1 | 0.2150 | 0.5219 | 0.5338 |
| xmeas_33 -> xmv_09 | 1 | 0.1988 | 0.0000 | 0.0049 |
| xmeas_19 -> xmv_09 | 1 | 0.1960 | 0.4451 | 0.3704 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
