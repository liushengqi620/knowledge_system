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
| edge_cert_overlay_anchor | 3 | -0.0029 +/- 0.0046 | -0.0057 +/- 0.0041 | -0.0038 +/- 0.0044 | -0.0038 +/- 0.0153 | 0.0003 +/- 0.0011 | 0.2128 |

## Candidate: edge_cert_overlay_anchor

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0792 +/- 0.0458 |
| 3 | -0.0116 +/- 0.0143 |
| 10 | -0.0048 +/- 0.0234 |
| 0 | -0.0035 +/- 0.0226 |
| 16 | 0.0055 +/- 0.0500 |
| 15 | 0.0710 +/- 0.0759 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_20 -> xmeas_19 | 1 | 0.2322 | 0.0000 | 0.0151 |
| xmeas_18 -> xmv_09 | 1 | 0.2140 | 0.5081 | 0.5114 |
| xmeas_15 -> xmv_07 | 1 | 0.2062 | 0.0000 | 0.0146 |
| xmv_10 -> xmeas_07 | 1 | 0.1862 | 0.0000 | 0.1405 |
| xmv_05 -> xmv_03 | 1 | 0.1861 | 0.5410 | 0.9763 |
| xmv_10 -> xmeas_28 | 1 | 0.1621 | 0.0000 | 0.1096 |

### Edge Prior Audit

- modes: `{'edge_cert_overlay': 3}`
- density: `0.0858 +/- 0.0005`
- uncapped edges mean: `232.0`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
