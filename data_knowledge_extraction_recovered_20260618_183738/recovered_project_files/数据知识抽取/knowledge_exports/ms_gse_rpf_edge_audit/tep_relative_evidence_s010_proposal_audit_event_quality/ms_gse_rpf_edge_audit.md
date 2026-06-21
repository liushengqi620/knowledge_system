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
| rel_evidence_s010 | 3 | -0.0105 +/- 0.0104 | -0.0067 +/- 0.0065 | -0.0061 +/- 0.0042 | -0.0082 +/- 0.0412 | -0.0138 +/- 0.0120 | 0.1667 |

## Candidate: rel_evidence_s010

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0744 +/- 0.0703 |
| 0 | -0.0277 +/- 0.0093 |
| 9 | -0.0267 +/- 0.0585 |
| 3 | -0.0135 +/- 0.0103 |
| 15 | 0.0129 +/- 0.1233 |
| 10 | 0.0800 +/- 0.0797 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | 1 | 0.3462 | 0.3218 | 0.1849 |
| xmv_10 -> xmeas_07 | 1 | 0.2168 | 0.0000 | 0.2067 |
| xmeas_03 -> xmeas_37 | 1 | 0.2136 | 0.0000 | 0.0856 |
| xmeas_19 -> xmeas_38 | 1 | 0.2052 | 0.0000 | 0.0639 |
| xmeas_36 -> xmeas_11 | 1 | 0.1918 | 0.0000 | 0.4809 |
| xmeas_01 -> xmeas_07 | 1 | 0.1876 | 0.0000 | 0.7185 |
| xmv_10 -> xmeas_39 | 1 | 0.1849 | 0.0000 | 0.2107 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
