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
| candadmit | 3 | -0.0047 +/- 0.0103 | -0.0045 +/- 0.0078 | -0.0044 +/- 0.0076 | -0.0116 +/- 0.0432 | -0.0064 +/- 0.0103 | 0.1400 |

## Candidate: candadmit

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 10 | -0.0423 +/- 0.0655 |
| 16 | -0.0394 +/- 0.0883 |
| 9 | -0.0244 +/- 0.0269 |
| 0 | -0.0037 +/- 0.0393 |
| 3 | 0.0110 +/- 0.0381 |
| 15 | 0.0295 +/- 0.0968 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_16 -> xmv_05 | 2 | 0.1816 | 0.0711 | 0.6996 |
| xmeas_37 -> xmeas_21 | 1 | 0.2289 | 0.0000 | 0.1048 |
| xmeas_19 -> xmv_09 | 1 | 0.2179 | 0.4305 | 0.3318 |
| xmeas_08 -> xmv_05 | 1 | 0.1745 | 0.0000 | 0.5465 |
| xmeas_38 -> xmeas_19 | 1 | 0.1718 | 0.0000 | 0.0971 |
| xmv_05 -> xmeas_18 | 1 | 0.1586 | 0.0000 | 0.9731 |
| xmeas_13 -> xmeas_11 | 1 | 0.1455 | 0.5847 | 0.5954 |
| xmeas_14 -> xmeas_13 | 1 | 0.1453 | 0.0000 | 0.1463 |

### Edge Prior Audit

- modes: `{'edge_cert_overlay': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `206.0`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
