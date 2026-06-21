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
| edge_lattice_affinity | 3 | -0.0078 +/- 0.0052 | -0.0083 +/- 0.0094 | -0.0066 +/- 0.0053 | -0.0256 +/- 0.0040 | -0.0183 +/- 0.0148 | 0.1429 |

## Candidate: edge_lattice_affinity

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0745 +/- 0.0692 |
| 16 | -0.0676 +/- 0.0727 |
| 15 | -0.0641 +/- 0.0266 |
| 3 | -0.0012 +/- 0.1141 |
| 10 | 0.0240 +/- 0.0551 |
| 0 | 0.0295 +/- 0.0439 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_18 -> xmeas_19 | 2 | 0.2519 | 0.3642 | 0.2682 |
| xmv_05 -> xmeas_21 | 1 | 0.2544 | 0.0000 | 0.0756 |
| xmv_02 -> xmv_05 | 1 | 0.2217 | 0.0000 | 0.0643 |
| xmeas_31 -> xmeas_30 | 1 | 0.2052 | 0.0000 | 0.0682 |
| xmeas_30 -> xmeas_19 | 1 | 0.2034 | 0.0000 | 0.0148 |
| xmeas_01 -> xmeas_18 | 1 | 0.2034 | 0.0000 | 0.0896 |
| xmv_02 -> xmeas_13 | 1 | 0.1843 | 0.0000 | 0.0467 |

### Edge Prior Audit

- modes: `{'edge_lattice': 3}`
- density: `0.0939 +/- 0.0006`
- uncapped edges mean: `987.3`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
