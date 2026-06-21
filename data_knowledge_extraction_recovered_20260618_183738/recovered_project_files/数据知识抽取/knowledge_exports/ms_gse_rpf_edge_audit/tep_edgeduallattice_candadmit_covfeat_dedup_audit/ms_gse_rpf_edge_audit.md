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
| dual_dedup | 3 | -0.0043 +/- 0.0058 | -0.0020 +/- 0.0047 | -0.0023 +/- 0.0005 | -0.0120 +/- 0.0118 | 0.0004 +/- 0.0077 | 0.0755 |

## Candidate: dual_dedup

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0620 +/- 0.0479 |
| 3 | -0.0507 +/- 0.0456 |
| 16 | -0.0062 +/- 0.0329 |
| 10 | 0.0036 +/- 0.0909 |
| 15 | 0.0144 +/- 0.0848 |
| 0 | 0.0288 +/- 0.0220 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_15 -> xmv_07 | 1 | 0.4610 | 0.0000 | 0.0037 |
| xmeas_08 -> xmeas_20 | 1 | 0.2377 | 0.0000 | 0.5634 |
| xmv_09 -> xmv_06 | 1 | 0.2165 | 0.0000 | 0.1049 |
| xmeas_12 -> xmeas_08 | 1 | 0.2141 | 0.0000 | 0.3049 |
| xmv_05 -> xmeas_11 | 1 | 0.1999 | 0.0000 | 0.9910 |
| xmeas_10 -> xmeas_19 | 1 | 0.1987 | 0.0000 | 0.1425 |
| xmeas_28 -> xmeas_10 | 1 | 0.1888 | 0.3367 | 0.5458 |
| xmeas_19 -> xmv_09 | 1 | 0.1830 | 0.4302 | 0.2850 |
| xmv_09 -> xmeas_13 | 1 | 0.1809 | 0.0000 | 0.4947 |

### Edge Prior Audit

- modes: `{'edge_dual_lattice': 3}`
- density: `0.0763 +/- 0.0003`
- uncapped edges mean: `1882.7`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
