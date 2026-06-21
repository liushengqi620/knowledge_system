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
| certcore_coreonly | 3 | -0.0078 +/- 0.0069 | -0.0058 +/- 0.0129 | -0.0039 +/- 0.0108 | -0.0452 +/- 0.0198 | -0.0138 +/- 0.0306 | 0.0357 |
| certcore_sepcandidate | 3 | -0.0129 +/- 0.0094 | -0.0123 +/- 0.0071 | -0.0106 +/- 0.0051 | -0.0432 +/- 0.0260 | -0.0191 +/- 0.0090 | 0.0755 |

## Candidate: certcore_coreonly

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0881 +/- 0.0393 |
| 15 | -0.0797 +/- 0.0309 |
| 16 | -0.0703 +/- 0.0604 |
| 3 | -0.0463 +/- 0.0125 |
| 10 | 0.0017 +/- 0.0984 |
| 0 | 0.0113 +/- 0.0203 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_37 -> xmeas_19 | 1 | 0.4932 | 0.0000 | 0.0036 |
| xmeas_20 -> xmeas_11 | 1 | 0.3189 | 0.0000 | 0.0587 |
| xmeas_25 -> xmv_05 | 1 | 0.2477 | 0.0000 | 0.0628 |
| xmv_10 -> xmeas_13 | 1 | 0.2455 | 0.0000 | 0.0324 |
| xmv_10 -> xmeas_09 | 1 | 0.2328 | 0.1549 | 0.0673 |
| xmv_02 -> xmv_05 | 1 | 0.1926 | 0.0000 | 0.0944 |
| xmeas_26 -> xmv_05 | 1 | 0.1827 | 0.0000 | 0.0499 |
| xmeas_18 -> xmeas_28 | 1 | 0.1777 | 0.0000 | 0.0145 |
| xmeas_29 -> xmeas_30 | 1 | 0.1773 | 0.0000 | 0.0675 |
| xmv_03 -> xmeas_11 | 1 | 0.1675 | 0.0000 | 0.0416 |

### Edge Prior Audit

- modes: `{'edge_lattice': 3}`
- density: `0.0939 +/- 0.0006`
- uncapped edges mean: `987.3`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`

## Candidate: certcore_sepcandidate

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 9 | -0.0834 +/- 0.0647 |
| 10 | -0.0687 +/- 0.0954 |
| 16 | -0.0668 +/- 0.0636 |
| 0 | -0.0166 +/- 0.0371 |
| 15 | -0.0121 +/- 0.0091 |
| 3 | -0.0116 +/- 0.0704 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmv_09 -> xmeas_21 | 1 | 0.4017 | 0.0000 | 0.0282 |
| xmv_10 -> xmeas_09 | 1 | 0.3224 | 0.1840 | 0.0381 |
| xmv_05 -> xmeas_21 | 1 | 0.3060 | 0.0000 | 0.0727 |
| xmeas_32 -> xmv_02 | 1 | 0.2876 | 0.0000 | 0.0027 |
| xmv_05 -> xmeas_09 | 1 | 0.2817 | 0.0000 | 0.0743 |
| xmeas_26 -> xmeas_07 | 1 | 0.2635 | 0.0000 | 0.0807 |
| xmeas_07 -> xmeas_28 | 1 | 0.2432 | 0.0000 | 0.0217 |
| xmeas_15 -> xmv_05 | 1 | 0.1996 | 0.0000 | 0.0281 |

### Edge Prior Audit

- modes: `{'edge_lattice': 3}`
- density: `0.0939 +/- 0.0006`
- uncapped edges mean: `987.3`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
