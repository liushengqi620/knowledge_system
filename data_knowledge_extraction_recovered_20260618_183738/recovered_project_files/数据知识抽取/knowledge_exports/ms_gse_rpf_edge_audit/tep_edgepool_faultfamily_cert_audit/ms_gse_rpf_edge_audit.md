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
| edge_fault_family_cert | 3 | -0.0075 +/- 0.0194 | -0.0077 +/- 0.0082 | -0.0072 +/- 0.0078 | -0.0253 +/- 0.0441 | -0.0099 +/- 0.0203 | 0.1837 |

## Candidate: edge_fault_family_cert

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0803 +/- 0.1282 |
| 9 | -0.0460 +/- 0.0058 |
| 10 | -0.0200 +/- 0.0554 |
| 0 | -0.0093 +/- 0.0385 |
| 15 | -0.0053 +/- 0.1349 |
| 3 | 0.0091 +/- 0.0241 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_34 -> xmeas_10 | 1 | 0.2266 | 0.4238 | 0.7518 |
| xmeas_38 -> xmeas_19 | 1 | 0.2184 | 0.0000 | 0.0738 |
| xmeas_13 -> xmeas_11 | 1 | 0.2014 | 0.6239 | 0.6657 |
| xmeas_31 -> xmeas_29 | 1 | 0.1857 | 0.5929 | 0.6941 |
| xmv_09 -> xmeas_18 | 1 | 0.1817 | 0.5326 | 0.5413 |
| xmv_05 -> xmeas_18 | 1 | 0.1621 | 0.0000 | 0.9906 |
| xmeas_35 -> xmeas_13 | 1 | 0.1454 | 0.4819 | 0.6097 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `100.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
