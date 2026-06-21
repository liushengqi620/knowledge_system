# MS-GSE + RPF Edge/Path Audit

- dataset: tep
- target: event_quality_class_id
- variant: full
- low-tail quantile: 0.25

## Baseline

| Runs | Val Macro-F1 | Test Macro-F1 | Test Bal. Acc. |
|---:|---:|---:|---:|
| 3 | 0.7413 +/- 0.0039 | 0.6375 +/- 0.0044 | 0.6483 +/- 0.0065 |

## Baseline Low-Tail Classes

| Class | Val F1 | Runs |
|---|---:|---:|
| 3 | 0.2073 +/- 0.0416 | 3 |
| 9 | 0.2163 +/- 0.0467 | 3 |
| 15 | 0.2413 +/- 0.0438 | 3 |
| 10 | 0.2819 +/- 0.0532 | 3 |
| 16 | 0.3506 +/- 0.0523 | 3 |
| 0 | 0.4257 +/- 0.0365 | 3 |

## Candidate Summary

| Candidate | Runs | Val Gain | Test Gain | Test Bal. Gain | Low-Tail Val Gain | Low-Tail Test Gain | Path Jaccard |
|---|---:|---:|---:|---:|---:|---:|---:|
| protectedproposal | 3 | -0.0007 +/- 0.0082 | -0.0038 +/- 0.0024 | -0.0063 +/- 0.0044 | 0.0042 +/- 0.0158 | -0.0108 +/- 0.0035 | 0.1176 |

## Candidate: protectedproposal

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0659 +/- 0.0613 |
| 10 | -0.0125 +/- 0.0770 |
| 0 | 0.0052 +/- 0.0325 |
| 3 | 0.0267 +/- 0.0419 |
| 9 | 0.0308 +/- 0.0323 |
| 15 | 0.0408 +/- 0.0288 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_10 -> xmeas_22 | 1 | 0.2672 | 0.0000 | 0.7837 |
| xmeas_38 -> xmv_09 | 1 | 0.2539 | 0.0000 | 0.7826 |
| xmeas_37 -> xmeas_18 | 1 | 0.2270 | 0.0000 | 0.6650 |
| xmeas_01 -> xmeas_07 | 1 | 0.1891 | 0.0000 | 0.8733 |
| xmv_11 -> xmeas_09 | 1 | 0.1878 | 0.0000 | 0.7815 |
| xmv_10 -> xmeas_13 | 1 | 0.1796 | 0.0000 | 0.7837 |
| xmv_10 -> xmeas_34 | 1 | 0.1789 | 0.0000 | 0.9093 |

### Edge Prior Audit

- modes: `{'edge_dual_lattice': 3}`
- density: `0.0762 +/- 0.0003`
- uncapped edges mean: `1684.7`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
