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
| protected | 3 | 0.0047 +/- 0.0057 | -0.0011 +/- 0.0017 | -0.0005 +/- 0.0033 | -0.0162 +/- 0.0075 | 0.0000 +/- 0.0125 | 0.0962 |

## Candidate: protected

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0552 +/- 0.0260 |
| 16 | -0.0528 +/- 0.0792 |
| 15 | -0.0165 +/- 0.0336 |
| 10 | -0.0085 +/- 0.0878 |
| 3 | 0.0004 +/- 0.1113 |
| 0 | 0.0354 +/- 0.0162 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_10 -> xmeas_22 | 2 | 0.2130 | 0.0000 | 0.8004 |
| xmeas_37 -> xmeas_19 | 1 | 0.2353 | 0.0000 | 0.8025 |
| xmeas_08 -> xmeas_10 | 1 | 0.2258 | 0.0000 | 1.0000 |
| xmv_10 -> xmeas_31 | 1 | 0.2151 | 0.0031 | 0.9035 |
| xmv_10 -> xmeas_21 | 1 | 0.2050 | 0.0000 | 0.7837 |
| xmeas_39 -> xmeas_20 | 1 | 0.1974 | 0.0000 | 0.7118 |
| xmeas_01 -> xmeas_07 | 1 | 0.1889 | 0.0000 | 0.8733 |
| xmeas_01 -> xmeas_08 | 1 | 0.1865 | 0.0000 | 0.8733 |
| xmv_10 -> xmeas_06 | 1 | 0.1816 | 0.0000 | 0.7837 |

### Edge Prior Audit

- modes: `{'edge_dual_lattice': 3}`
- density: `0.0762 +/- 0.0003`
- uncapped edges mean: `1684.7`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
