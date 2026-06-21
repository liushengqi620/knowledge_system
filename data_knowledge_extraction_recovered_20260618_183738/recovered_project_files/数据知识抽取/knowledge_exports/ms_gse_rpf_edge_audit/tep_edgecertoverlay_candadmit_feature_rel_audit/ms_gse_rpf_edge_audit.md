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
| edge_candidate_feature | 3 | -0.0121 +/- 0.0081 | -0.0077 +/- 0.0015 | -0.0059 +/- 0.0017 | -0.0164 +/- 0.0288 | -0.0130 +/- 0.0084 | 0.1200 |

## Candidate: edge_candidate_feature

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0625 +/- 0.0476 |
| 16 | -0.0479 +/- 0.0747 |
| 10 | -0.0059 +/- 0.0873 |
| 15 | -0.0034 +/- 0.1011 |
| 0 | 0.0055 +/- 0.0397 |
| 3 | 0.0157 +/- 0.0564 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | 1 | 0.3774 | 0.3553 | 0.1779 |
| xmeas_18 -> xmeas_29 | 1 | 0.1728 | 0.0000 | 0.8364 |
| xmeas_36 -> xmeas_13 | 1 | 0.1529 | 0.4443 | 0.5430 |
| xmeas_31 -> xmeas_29 | 1 | 0.1515 | 0.6370 | 0.7640 |
| xmeas_13 -> xmeas_11 | 1 | 0.1301 | 0.5647 | 0.5590 |
| xmv_05 -> xmeas_11 | 1 | 0.1293 | 0.0000 | 0.9590 |

### Edge Prior Audit

- modes: `{'edge_cert_overlay': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `206.0`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
