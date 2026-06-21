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
| evidcons_rel_s010 | 3 | -0.0078 +/- 0.0068 | -0.0085 +/- 0.0056 | -0.0060 +/- 0.0050 | -0.0146 +/- 0.0233 | -0.0107 +/- 0.0102 | 0.1176 |
| evidcons_rel_s003 | 3 | -0.0059 +/- 0.0054 | -0.0057 +/- 0.0022 | -0.0032 +/- 0.0021 | -0.0120 +/- 0.0223 | -0.0183 +/- 0.0105 | 0.0566 |

## Candidate: evidcons_rel_s010

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 3 | -0.0918 +/- 0.0614 |
| 16 | -0.0703 +/- 0.0776 |
| 0 | -0.0425 +/- 0.0798 |
| 9 | -0.0168 +/- 0.0162 |
| 15 | 0.0512 +/- 0.0670 |
| 10 | 0.0825 +/- 0.0819 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_33 -> xmeas_07 | 1 | 0.2851 | 0.0000 | 0.0337 |
| xmeas_19 -> xmv_09 | 1 | 0.2245 | 0.2405 | 0.0817 |
| xmv_05 -> xmeas_18 | 1 | 0.2131 | 0.0000 | 0.0634 |
| xmeas_15 -> xmv_07 | 1 | 0.2086 | 0.0000 | 0.0056 |
| xmeas_08 -> xmeas_14 | 1 | 0.2021 | 0.0000 | 0.0059 |
| xmeas_20 -> xmeas_11 | 1 | 0.1979 | 0.0000 | 0.0473 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0571 +/- 0.0002`
- uncapped edges mean: `966.7`
- corroborated edges mean: `136.7`
- single-view edges mean: `17.7`
- top-edge family counts: `{'dynamic': 120, 'structural': 112, 'task': 64}`

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
