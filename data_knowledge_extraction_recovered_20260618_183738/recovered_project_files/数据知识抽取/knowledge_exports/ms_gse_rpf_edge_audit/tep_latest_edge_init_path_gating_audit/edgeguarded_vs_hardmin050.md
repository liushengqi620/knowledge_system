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
| guarded | 3 | -0.0004 +/- 0.0084 | -0.0096 +/- 0.0039 | -0.0063 +/- 0.0065 | -0.0009 +/- 0.0104 | -0.0138 +/- 0.0140 | 0.1429 |

## Candidate: guarded

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0194 +/- 0.0323 |
| 0 | -0.0095 +/- 0.0588 |
| 15 | -0.0093 +/- 0.0639 |
| 9 | 0.0008 +/- 0.0383 |
| 10 | 0.0089 +/- 0.0604 |
| 3 | 0.0228 +/- 0.0968 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_07 -> xmeas_19 | 1 | 0.3326 | 0.0000 | 0.8025 |
| xmv_05 -> xmeas_28 | 1 | 0.2649 | 0.0000 | 0.9022 |
| xmv_05 -> xmeas_30 | 1 | 0.2222 | 0.0000 | 0.7693 |
| xmv_05 -> xmeas_07 | 1 | 0.2195 | 0.0000 | 0.7961 |
| xmeas_31 -> xmv_09 | 1 | 0.2182 | 0.0000 | 0.9035 |
| xmv_10 -> xmeas_22 | 1 | 0.2108 | 0.0000 | 0.7837 |

### Edge Prior Audit

- modes: `{'edge_guarded_lattice': 3}`
- density: `0.0762 +/- 0.0003`
- uncapped edges mean: `1684.7`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
