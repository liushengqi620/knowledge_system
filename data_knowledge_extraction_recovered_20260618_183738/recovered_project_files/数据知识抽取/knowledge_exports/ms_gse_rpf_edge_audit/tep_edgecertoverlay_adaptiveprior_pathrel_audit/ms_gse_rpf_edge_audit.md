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
| edge_cert_overlay | 3 | -0.0059 +/- 0.0141 | -0.0032 +/- 0.0027 | -0.0041 +/- 0.0057 | -0.0148 +/- 0.0110 | -0.0076 +/- 0.0074 | 0.1400 |

## Candidate: edge_cert_overlay

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0994 +/- 0.0458 |
| 10 | -0.0213 +/- 0.0221 |
| 3 | -0.0117 +/- 0.0198 |
| 16 | -0.0076 +/- 0.0724 |
| 15 | 0.0149 +/- 0.0264 |
| 0 | 0.0367 +/- 0.0136 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_14 -> xmv_09 | 1 | 0.4600 | 0.0000 | 0.0022 |
| xmv_05 -> xmeas_41 | 1 | 0.4228 | 0.0000 | 0.9929 |
| xmeas_24 -> xmv_02 | 1 | 0.3005 | 0.0000 | 0.0195 |
| xmeas_12 -> xmeas_08 | 1 | 0.2037 | 0.0000 | 0.1652 |
| xmeas_23 -> xmeas_25 | 1 | 0.1955 | 0.0000 | 0.4911 |
| xmv_09 -> xmeas_13 | 1 | 0.1905 | 0.0000 | 0.2758 |
| xmeas_25 -> xmv_05 | 1 | 0.1727 | 0.0000 | 0.6317 |

### Edge Prior Audit

- modes: `{'edge_cert_overlay': 3}`
- density: `0.0858 +/- 0.0003`
- uncapped edges mean: `232.0`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{'dynamic': 294, 'structural': 119, 'task': 69}`
