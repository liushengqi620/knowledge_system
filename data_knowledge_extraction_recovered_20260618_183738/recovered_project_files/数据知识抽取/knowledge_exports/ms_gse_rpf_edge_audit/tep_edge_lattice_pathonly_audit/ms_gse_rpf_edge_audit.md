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
| edge_lattice_pathonly | 3 | -0.0081 +/- 0.0064 | -0.0127 +/- 0.0094 | -0.0095 +/- 0.0084 | -0.0263 +/- 0.0188 | -0.0202 +/- 0.0159 | 0.0556 |

## Candidate: edge_lattice_pathonly

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.1380 +/- 0.0411 |
| 3 | -0.0406 +/- 0.0882 |
| 15 | -0.0278 +/- 0.0439 |
| 0 | -0.0056 +/- 0.0435 |
| 9 | 0.0002 +/- 0.0532 |
| 10 | 0.0541 +/- 0.0606 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_09 -> xmeas_13 | 1 | 0.2921 | 0.0000 | 0.0519 |
| xmeas_35 -> xmeas_05 | 1 | 0.2884 | 0.0000 | 0.0061 |
| xmv_05 -> xmeas_21 | 1 | 0.2678 | 0.0000 | 0.0657 |
| xmv_10 -> xmeas_09 | 1 | 0.2417 | 0.1934 | 0.0480 |
| xmeas_37 -> xmeas_19 | 1 | 0.2009 | 0.0000 | 0.0101 |
| xmeas_01 -> xmeas_07 | 1 | 0.1624 | 0.0000 | 0.0445 |
| xmeas_01 -> xmeas_28 | 1 | 0.1622 | 0.0000 | 0.0448 |
| xmeas_21 -> xmeas_01 | 1 | 0.1604 | 0.0000 | 0.0211 |
| xmv_08 -> xmeas_40 | 1 | 0.1601 | 0.1450 | 0.1783 |

### Edge Prior Audit

- modes: `{'edge_lattice': 3}`
- density: `0.0939 +/- 0.0006`
- uncapped edges mean: `987.3`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
