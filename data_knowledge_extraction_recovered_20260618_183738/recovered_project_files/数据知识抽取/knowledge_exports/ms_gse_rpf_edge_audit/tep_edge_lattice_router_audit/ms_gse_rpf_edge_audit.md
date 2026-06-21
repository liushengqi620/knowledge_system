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
| edge_lattice_router | 3 | 0.0023 +/- 0.0092 | -0.0061 +/- 0.0060 | -0.0035 +/- 0.0055 | 0.0033 +/- 0.0362 | -0.0108 +/- 0.0105 | 0.0962 |

## Candidate: edge_lattice_router

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0834 +/- 0.1052 |
| 15 | -0.0374 +/- 0.0567 |
| 0 | -0.0185 +/- 0.0609 |
| 9 | 0.0273 +/- 0.0400 |
| 10 | 0.0432 +/- 0.1064 |
| 3 | 0.0885 +/- 0.1136 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_21 -> xmeas_01 | 1 | 0.3196 | 0.0000 | 0.0267 |
| xmeas_21 -> xmv_10 | 1 | 0.3140 | 0.0000 | 0.0287 |
| xmeas_23 -> xmeas_04 | 1 | 0.2874 | 0.0000 | 0.0539 |
| xmv_05 -> xmeas_10 | 1 | 0.2530 | 0.0000 | 0.0719 |
| xmv_10 -> xmeas_09 | 1 | 0.2353 | 0.1708 | 0.0406 |
| xmeas_13 -> xmeas_11 | 1 | 0.2257 | 0.1980 | 0.0623 |
| xmeas_02 -> xmeas_19 | 1 | 0.2187 | 0.0000 | 0.0473 |
| xmv_05 -> xmeas_31 | 1 | 0.2109 | 0.0000 | 0.0253 |

### Edge Prior Audit

- modes: `{'edge_lattice': 3}`
- density: `0.1022 +/- 0.0025`
- uncapped edges mean: `276.3`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
