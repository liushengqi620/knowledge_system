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
| dual_proposal | 3 | -0.0023 +/- 0.0126 | 0.0004 +/- 0.0051 | 0.0002 +/- 0.0036 | -0.0066 +/- 0.0256 | 0.0042 +/- 0.0223 | 0.0980 |

## Candidate: dual_proposal

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0582 +/- 0.0156 |
| 16 | -0.0453 +/- 0.0400 |
| 3 | -0.0365 +/- 0.0611 |
| 15 | 0.0147 +/- 0.0594 |
| 0 | 0.0335 +/- 0.0258 |
| 10 | 0.0522 +/- 0.1148 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_11 -> xmv_05 | 1 | 0.2906 | 0.0000 | 0.8729 |
| xmeas_19 -> xmv_09 | 1 | 0.2316 | 0.3797 | 0.2730 |
| xmv_10 -> xmeas_02 | 1 | 0.2289 | 0.0000 | 0.1912 |
| xmeas_38 -> xmeas_20 | 1 | 0.2151 | 0.0193 | 0.5568 |
| xmeas_19 -> xmeas_09 | 1 | 0.1960 | 0.0000 | 0.4689 |
| xmeas_18 -> xmeas_09 | 1 | 0.1912 | 0.0000 | 0.4245 |

### Edge Prior Audit

- modes: `{'edge_dual_lattice': 3}`
- density: `0.0762 +/- 0.0003`
- uncapped edges mean: `1684.7`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
