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
| edge_universe | 3 | -0.0008 +/- 0.0203 | -0.0122 +/- 0.0125 | -0.0125 +/- 0.0089 | -0.0017 +/- 0.0287 | -0.0044 +/- 0.0023 | 0.0364 |
| path_prior_consistency | 3 | -0.0052 +/- 0.0097 | 0.0007 +/- 0.0070 | -0.0009 +/- 0.0045 | -0.0272 +/- 0.0420 | -0.0045 +/- 0.0073 | 0.1154 |
| class_blend | 3 | -0.0112 +/- 0.0043 | -0.0100 +/- 0.0096 | -0.0080 +/- 0.0067 | -0.0364 +/- 0.0276 | -0.0092 +/- 0.0109 | 0.0769 |
| edgepool_minscore010 | 3 | -0.0148 +/- 0.0062 | -0.0070 +/- 0.0051 | -0.0069 +/- 0.0080 | -0.0354 +/- 0.0238 | -0.0085 +/- 0.0110 | 0.0943 |

## Candidate: edge_universe

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 0 | -0.0451 +/- 0.0180 |
| 15 | -0.0274 +/- 0.1420 |
| 16 | -0.0220 +/- 0.1201 |
| 9 | -0.0211 +/- 0.0630 |
| 3 | -0.0182 +/- 0.0503 |
| 10 | 0.1237 +/- 0.0690 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | 2 | 0.2887 | 0.8686 | 0.0000 |
| xmv_08 -> xmv_11 | 1 | 0.7025 | 0.0000 | 0.0000 |
| xmeas_04 -> xmv_11 | 1 | 0.4567 | 0.0000 | 0.0000 |
| xmeas_17 -> xmv_11 | 1 | 0.4004 | 0.8240 | 0.0000 |
| xmv_09 -> xmv_11 | 1 | 0.3384 | 0.0000 | 0.0000 |
| xmeas_40 -> xmv_11 | 1 | 0.2969 | 0.0000 | 0.0000 |
| xmv_10 -> xmeas_13 | 1 | 0.2678 | 0.0000 | 0.0000 |
| xmv_10 -> xmeas_07 | 1 | 0.2658 | 0.0000 | 0.0000 |
| xmeas_18 -> xmv_11 | 1 | 0.2277 | 0.0000 | 0.0000 |

### Edge Prior Audit

- modes: `{'edge_universe': 3}`
- density: `0.1048 +/- 0.0018`
- uncapped edges mean: `322.7`
- corroborated edges mean: `278.7`
- single-view edges mean: `4.0`
- top-edge family counts: `{'dynamic': 283, 'structural': 92, 'task': 54}`

## Candidate: path_prior_consistency

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.1058 +/- 0.1034 |
| 9 | -0.0481 +/- 0.0627 |
| 0 | -0.0183 +/- 0.0402 |
| 15 | -0.0095 +/- 0.0110 |
| 10 | 0.0028 +/- 0.1780 |
| 3 | 0.0158 +/- 0.1096 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_05 -> xmeas_30 | 1 | 0.3527 | 0.0000 | 0.4035 |
| xmv_10 -> xmeas_02 | 1 | 0.1961 | 0.0000 | 0.3723 |
| xmv_05 -> xmeas_08 | 1 | 0.1879 | 0.0000 | 0.4154 |
| xmeas_13 -> xmeas_28 | 1 | 0.1812 | 0.0000 | 0.1904 |
| xmv_10 -> xmeas_09 | 1 | 0.1757 | 0.5187 | 0.3803 |
| xmeas_08 -> xmeas_16 | 1 | 0.1678 | 0.0000 | 0.1700 |
| xmeas_38 -> xmeas_04 | 1 | 0.1673 | 0.0000 | 0.2510 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`

## Candidate: class_blend

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.1020 +/- 0.0933 |
| 16 | -0.0749 +/- 0.1413 |
| 3 | -0.0499 +/- 0.0505 |
| 0 | -0.0204 +/- 0.0154 |
| 15 | -0.0157 +/- 0.0416 |
| 10 | 0.0448 +/- 0.0873 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_10 -> xmeas_09 | 3 | 0.2236 | 0.1300 | 0.2208 |
| xmeas_19 -> xmv_09 | 1 | 0.3261 | 0.5560 | 0.2340 |
| xmeas_26 -> xmeas_18 | 1 | 0.2519 | 0.0000 | 0.2730 |
| xmeas_29 -> xmeas_09 | 1 | 0.2121 | 0.0000 | 0.4498 |
| xmeas_18 -> xmeas_19 | 1 | 0.2116 | 0.6369 | 0.3649 |
| xmeas_21 -> xmv_05 | 1 | 0.1854 | 0.0000 | 0.2863 |
| xmv_04 -> xmeas_21 | 1 | 0.1807 | 0.0000 | 0.3357 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0762 +/- 0.0005`
- uncapped edges mean: `1446.7`
- corroborated edges mean: `200.0`
- single-view edges mean: `6.0`
- top-edge family counts: `{'dynamic': 120, 'structural': 114, 'task': 80}`

## Candidate: edgepool_minscore010

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 16 | -0.1034 +/- 0.1091 |
| 9 | -0.0836 +/- 0.0853 |
| 3 | -0.0800 +/- 0.0664 |
| 0 | -0.0212 +/- 0.0299 |
| 15 | -0.0072 +/- 0.0500 |
| 10 | 0.0832 +/- 0.0318 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_10 -> xmeas_25 | 1 | 0.3878 | 0.0000 | 0.2860 |
| xmeas_19 -> xmv_09 | 1 | 0.3345 | 0.4808 | 0.2006 |
| xmeas_30 -> xmeas_19 | 1 | 0.3207 | 0.0000 | 0.2729 |
| xmeas_26 -> xmeas_27 | 1 | 0.2790 | 0.0000 | 0.0143 |
| xmeas_01 -> xmeas_07 | 1 | 0.2298 | 0.0000 | 0.1064 |
| xmeas_01 -> xmv_10 | 1 | 0.1951 | 0.0000 | 0.3081 |
| xmv_11 -> xmeas_01 | 1 | 0.1944 | 0.0000 | 0.2043 |

### Edge Prior Audit

- modes: `{'edge_pool': 3}`
- density: `0.0759 +/- 0.0005`
- uncapped edges mean: `1320.3`
- corroborated edges mean: `193.7`
- single-view edges mean: `11.7`
- top-edge family counts: `{'dynamic': 120, 'structural': 105, 'task': 80}`
