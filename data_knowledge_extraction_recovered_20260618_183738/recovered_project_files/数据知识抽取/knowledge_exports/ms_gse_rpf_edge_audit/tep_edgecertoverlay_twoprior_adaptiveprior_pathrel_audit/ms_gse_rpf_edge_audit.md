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
| edge_cert_overlay_twoprior | 3 | -0.0081 +/- 0.0064 | -0.0050 +/- 0.0050 | -0.0057 +/- 0.0042 | -0.0180 +/- 0.0299 | -0.0040 +/- 0.0049 | 0.2174 |

## Candidate: edge_cert_overlay_twoprior

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 3 | -0.0771 +/- 0.0426 |
| 9 | -0.0308 +/- 0.0490 |
| 16 | -0.0257 +/- 0.0053 |
| 10 | -0.0228 +/- 0.0600 |
| 0 | -0.0031 +/- 0.0186 |
| 15 | 0.0517 +/- 0.1181 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_10 -> xmeas_31 | 1 | 0.1997 | 0.0000 | 0.1571 |
| xmeas_36 -> xmeas_34 | 1 | 0.1821 | 0.0000 | 0.5549 |
| xmv_10 -> xmeas_25 | 1 | 0.1762 | 0.0000 | 0.1433 |
| xmeas_40 -> xmv_06 | 1 | 0.1707 | 0.0000 | 0.0604 |

### Edge Prior Audit

- modes: `{'edge_cert_overlay': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `206.0`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
