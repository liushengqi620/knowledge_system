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
| dual_hardmin050 | 3 | 0.0020 +/- 0.0145 | 0.0014 +/- 0.0059 | 0.0006 +/- 0.0043 | -0.0045 +/- 0.0270 | 0.0027 +/- 0.0078 | 0.0980 |

## Candidate: dual_hardmin050

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 3 | -0.0358 +/- 0.0442 |
| 9 | -0.0214 +/- 0.0092 |
| 16 | -0.0040 +/- 0.0703 |
| 15 | -0.0005 +/- 0.0434 |
| 0 | 0.0099 +/- 0.0451 |
| 10 | 0.0248 +/- 0.1000 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_35 -> xmeas_10 | 1 | 0.3815 | 0.0000 | 0.7712 |
| xmv_10 -> xmeas_02 | 1 | 0.2692 | 0.0000 | 0.1668 |
| xmeas_19 -> xmv_09 | 1 | 0.2417 | 0.4525 | 0.3641 |
| xmv_10 -> xmeas_25 | 1 | 0.2119 | 0.0000 | 0.1771 |
| xmeas_38 -> xmeas_18 | 1 | 0.2061 | 0.0000 | 0.1264 |
| xmeas_38 -> xmv_05 | 1 | 0.2046 | 0.0000 | 0.9317 |
| xmeas_23 -> xmeas_10 | 1 | 0.1925 | 0.0000 | 0.4312 |

### Edge Prior Audit

- modes: `{'edge_dual_lattice': 3}`
- density: `0.0762 +/- 0.0003`
- uncapped edges mean: `1684.7`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
