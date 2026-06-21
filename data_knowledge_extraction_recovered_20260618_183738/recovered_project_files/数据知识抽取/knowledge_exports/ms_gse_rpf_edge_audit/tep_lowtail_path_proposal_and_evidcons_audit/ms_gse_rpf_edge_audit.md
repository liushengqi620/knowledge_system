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
| evidcons_rel_s003 | 3 | -0.0059 +/- 0.0054 | -0.0057 +/- 0.0022 | -0.0032 +/- 0.0021 | -0.0120 +/- 0.0223 | -0.0183 +/- 0.0105 | 0.0566 |
| salience_cover010 | 3 | -0.0024 +/- 0.0019 | -0.0052 +/- 0.0045 | -0.0043 +/- 0.0027 | -0.0303 +/- 0.0123 | -0.0207 +/- 0.0111 | 0.0962 |

## Candidate: evidcons_rel_s003

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.0748 +/- 0.0366 |
| 9 | -0.0402 +/- 0.0373 |
| 0 | -0.0226 +/- 0.0513 |
| 15 | -0.0112 +/- 0.0703 |
| 3 | -0.0038 +/- 0.0691 |
| 10 | 0.0806 +/- 0.1087 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_10 -> xmeas_19 | 1 | 0.3213 | 0.0000 | 0.0169 |
| xmeas_14 -> xmv_09 | 1 | 0.3061 | 0.0000 | 0.0018 |
| xmeas_23 -> xmeas_10 | 1 | 0.2509 | 0.0000 | 0.0268 |
| xmeas_36 -> xmeas_10 | 1 | 0.1944 | 0.0000 | 0.0367 |
| xmeas_14 -> xmeas_18 | 1 | 0.1783 | 0.0000 | 0.0291 |
| xmeas_10 -> xmeas_24 | 1 | 0.1627 | 0.0000 | 0.0186 |
| xmeas_37 -> xmeas_19 | 1 | 0.1614 | 0.0000 | 0.0219 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0571 +/- 0.0002`
- uncapped edges mean: `966.7`
- corroborated edges mean: `136.7`
- single-view edges mean: `17.7`
- top-edge family counts: `{'dynamic': 120, 'structural': 112, 'task': 64}`

## Candidate: salience_cover010

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 0 | -0.0697 +/- 0.0427 |
| 16 | -0.0576 +/- 0.0563 |
| 9 | -0.0479 +/- 0.0155 |
| 15 | -0.0291 +/- 0.0368 |
| 10 | 0.0101 +/- 0.0530 |
| 3 | 0.0125 +/- 0.0277 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_36 -> xmeas_38 | 1 | 0.4252 | 0.0000 | 0.0575 |
| xmeas_38 -> xmv_05 | 1 | 0.2598 | 0.0000 | 0.0843 |
| xmeas_29 -> xmeas_30 | 1 | 0.2540 | 0.0000 | 0.0514 |
| xmeas_19 -> xmv_09 | 1 | 0.2491 | 0.2282 | 0.0774 |
| xmeas_25 -> xmv_05 | 1 | 0.2279 | 0.0000 | 0.1399 |
| xmv_05 -> xmeas_18 | 1 | 0.2273 | 0.0000 | 0.0812 |
| xmv_02 -> xmv_05 | 1 | 0.2272 | 0.0000 | 0.0662 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0571 +/- 0.0002`
- uncapped edges mean: `966.7`
- corroborated edges mean: `136.7`
- single-view edges mean: `17.7`
- top-edge family counts: `{'dynamic': 120, 'structural': 112, 'task': 64}`
