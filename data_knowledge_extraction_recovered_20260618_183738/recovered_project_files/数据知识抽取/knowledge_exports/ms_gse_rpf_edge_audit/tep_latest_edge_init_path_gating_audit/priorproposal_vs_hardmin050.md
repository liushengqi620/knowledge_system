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
| priorproposal | 3 | 0.0067 +/- 0.0050 | -0.0032 +/- 0.0078 | -0.0019 +/- 0.0097 | 0.0125 +/- 0.0093 | -0.0017 +/- 0.0140 | 0.1224 |

## Candidate: priorproposal

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0588 +/- 0.0569 |
| 9 | -0.0312 +/- 0.0537 |
| 0 | 0.0217 +/- 0.0463 |
| 10 | 0.0406 +/- 0.0824 |
| 3 | 0.0455 +/- 0.0825 |
| 15 | 0.0572 +/- 0.0194 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | 2 | 0.2177 | 0.1448 | 0.7943 |
| xmeas_01 -> xmv_10 | 1 | 0.2409 | 0.0000 | 0.8733 |
| xmeas_01 -> xmeas_07 | 1 | 0.2131 | 0.0000 | 0.8733 |
| xmeas_09 -> xmeas_21 | 1 | 0.2026 | 0.0805 | 0.7279 |
| xmv_11 -> xmeas_28 | 1 | 0.1728 | 0.0000 | 0.9022 |
| xmeas_36 -> xmeas_13 | 1 | 0.1629 | 0.0000 | 0.7943 |

### Edge Prior Audit

- modes: `{'edge_dual_lattice': 3}`
- density: `0.0762 +/- 0.0003`
- uncapped edges mean: `1684.7`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
