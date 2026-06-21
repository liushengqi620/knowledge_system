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
| edge_cert_pool | 3 | -0.0051 +/- 0.0024 | -0.0114 +/- 0.0025 | -0.0101 +/- 0.0014 | -0.0265 +/- 0.0049 | -0.0153 +/- 0.0085 | 0.0741 |

## Candidate: edge_cert_pool

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0724 +/- 0.0548 |
| 3 | -0.0629 +/- 0.0794 |
| 9 | -0.0502 +/- 0.0658 |
| 10 | -0.0363 +/- 0.1027 |
| 0 | 0.0189 +/- 0.0302 |
| 15 | 0.0437 +/- 0.0267 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | 1 | 0.4978 | 0.0000 | 0.2105 |
| xmeas_37 -> xmeas_19 | 1 | 0.3049 | 0.0000 | 0.0243 |
| xmeas_01 -> xmeas_18 | 1 | 0.1812 | 0.0000 | 0.8961 |
| xmv_07 -> xmeas_19 | 1 | 0.1782 | 0.0000 | 0.1968 |
| xmeas_40 -> xmeas_10 | 1 | 0.1778 | 0.0000 | 0.7129 |
| xmeas_18 -> xmeas_28 | 1 | 0.1651 | 0.0000 | 0.2942 |
| xmv_05 -> xmeas_32 | 1 | 0.1642 | 0.0000 | 0.9382 |
| xmeas_01 -> xmeas_32 | 1 | 0.1578 | 0.0000 | 0.7589 |

### Edge Prior Audit

- modes: `{'edge_cert_pool': 3}`
- density: `0.0730 +/- 0.0009`
- uncapped edges mean: `554.7`
- corroborated edges mean: `178.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
