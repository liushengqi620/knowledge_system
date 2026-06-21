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
| classcert_f005 | 3 | -0.0074 +/- 0.0052 | -0.0098 +/- 0.0029 | -0.0060 +/- 0.0024 | -0.0160 +/- 0.0073 | -0.0053 +/- 0.0098 | 0.0962 |
| classcert_f050 | 3 | -0.0074 +/- 0.0054 | -0.0095 +/- 0.0074 | -0.0078 +/- 0.0022 | -0.0156 +/- 0.0183 | -0.0111 +/- 0.0134 | 0.0943 |

## Candidate: classcert_f005

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0621 +/- 0.0662 |
| 0 | -0.0528 +/- 0.0641 |
| 16 | -0.0432 +/- 0.0436 |
| 3 | -0.0136 +/- 0.0744 |
| 15 | 0.0327 +/- 0.0226 |
| 10 | 0.0428 +/- 0.0544 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_37 -> xmeas_19 | 1 | 0.2606 | 0.0000 | 0.0223 |
| xmeas_19 -> xmv_09 | 1 | 0.2169 | 0.2692 | 0.1212 |
| xmv_10 -> xmeas_09 | 1 | 0.2139 | 0.0000 | 0.0199 |
| xmeas_30 -> xmeas_19 | 1 | 0.1990 | 0.0000 | 0.0434 |
| xmeas_10 -> xmeas_31 | 1 | 0.1956 | 0.0000 | 0.0219 |
| xmv_05 -> xmeas_07 | 1 | 0.1871 | 0.0000 | 0.0846 |
| xmeas_01 -> xmeas_07 | 1 | 0.1748 | 0.0000 | 0.0455 |
| xmeas_14 -> xmv_09 | 1 | 0.1496 | 0.0000 | 0.0011 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0571 +/- 0.0002`
- uncapped edges mean: `966.7`
- corroborated edges mean: `136.7`
- single-view edges mean: `17.7`
- top-edge family counts: `{'dynamic': 120, 'structural': 112, 'task': 64}`

## Candidate: classcert_f050

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0800 +/- 0.0492 |
| 3 | -0.0697 +/- 0.0616 |
| 0 | -0.0585 +/- 0.0257 |
| 9 | -0.0370 +/- 0.0338 |
| 10 | 0.0650 +/- 0.0761 |
| 15 | 0.0868 +/- 0.0042 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_37 -> xmeas_19 | 1 | 0.4909 | 0.0000 | 0.0177 |
| xmv_10 -> xmeas_09 | 1 | 0.2433 | 0.0000 | 0.0238 |
| xmeas_10 -> xmeas_19 | 1 | 0.2164 | 0.0000 | 0.0092 |
| xmv_11 -> xmeas_27 | 1 | 0.1907 | 0.0000 | 0.0116 |
| xmeas_14 -> xmeas_18 | 1 | 0.1884 | 0.0000 | 0.0139 |
| xmv_09 -> xmeas_13 | 1 | 0.1831 | 0.0000 | 0.0707 |
| xmeas_25 -> xmv_05 | 1 | 0.1773 | 0.0000 | 0.0842 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0571 +/- 0.0002`
- uncapped edges mean: `966.7`
- corroborated edges mean: `136.7`
- single-view edges mean: `17.7`
- top-edge family counts: `{'dynamic': 120, 'structural': 112, 'task': 64}`
