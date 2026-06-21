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
| stableclass_overlay | 3 | -0.0038 +/- 0.0142 | -0.0018 +/- 0.0037 | -0.0041 +/- 0.0032 | -0.0014 +/- 0.0275 | -0.0014 +/- 0.0058 | 0.1875 |
| stableclass_overlay_evidadmit | 3 | -0.0067 +/- 0.0087 | -0.0073 +/- 0.0072 | -0.0060 +/- 0.0067 | -0.0141 +/- 0.0218 | -0.0100 +/- 0.0134 | 0.0962 |

## Candidate: stableclass_overlay

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0403 +/- 0.0279 |
| 16 | -0.0395 +/- 0.0668 |
| 0 | -0.0196 +/- 0.0235 |
| 10 | -0.0033 +/- 0.0982 |
| 3 | 0.0258 +/- 0.0590 |
| 15 | 0.0687 +/- 0.0913 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_20 -> xmeas_19 | 1 | 0.3173 | 0.0000 | 0.0218 |
| xmeas_19 -> xmv_09 | 1 | 0.2959 | 0.3571 | 0.2585 |
| xmv_10 -> xmeas_07 | 1 | 0.2331 | 0.0000 | 0.1581 |
| xmv_10 -> xmeas_25 | 1 | 0.2328 | 0.0000 | 0.1513 |
| xmeas_18 -> xmv_09 | 1 | 0.2254 | 0.5306 | 0.5434 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`

## Candidate: stableclass_overlay_evidadmit

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0794 +/- 0.1032 |
| 9 | -0.0603 +/- 0.0996 |
| 0 | -0.0379 +/- 0.0348 |
| 3 | 0.0240 +/- 0.0129 |
| 15 | 0.0263 +/- 0.0350 |
| 10 | 0.0427 +/- 0.0327 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_05 -> xmeas_13 | 1 | 0.4737 | 0.2445 | 0.9759 |
| xmeas_19 -> xmv_09 | 1 | 0.3453 | 0.3256 | 0.2163 |
| xmeas_18 -> xmv_09 | 1 | 0.2450 | 0.4618 | 0.4496 |
| xmv_05 -> xmv_09 | 1 | 0.2233 | 0.4572 | 0.7609 |
| xmv_05 -> xmeas_38 | 1 | 0.2144 | 0.0000 | 0.5245 |
| xmv_08 -> xmv_11 | 1 | 0.2054 | 0.0000 | 0.4189 |
| xmeas_10 -> xmeas_07 | 1 | 0.2009 | 0.0000 | 0.5546 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`
