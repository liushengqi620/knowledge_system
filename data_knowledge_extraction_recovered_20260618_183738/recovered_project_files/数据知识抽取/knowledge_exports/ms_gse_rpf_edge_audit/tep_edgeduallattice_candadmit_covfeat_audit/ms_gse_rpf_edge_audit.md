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
| dual | 3 | -0.0169 +/- 0.0040 | -0.0124 +/- 0.0020 | -0.0156 +/- 0.0044 | -0.0257 +/- 0.0220 | -0.0191 +/- 0.0083 | 0.0784 |

## Candidate: dual

### Most Harmed Low-Tail Validation Classes

| Class | Val F1 Gain |
|---|---:|
| 10 | -0.1067 +/- 0.0761 |
| 16 | -0.0510 +/- 0.0746 |
| 9 | -0.0219 +/- 0.0269 |
| 15 | -0.0026 +/- 0.0408 |
| 0 | 0.0084 +/- 0.0161 |
| 3 | 0.0196 +/- 0.0625 |

### New Candidate Top Paths

| Path | Count | Weight | Prior | Salience |
|---|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | 1 | 0.3488 | 0.4626 | 0.2461 |
| xmeas_34 -> xmeas_19 | 1 | 0.2940 | 0.4221 | 0.8447 |
| xmv_02 -> xmv_05 | 1 | 0.2397 | 0.1541 | 0.9822 |
| xmeas_13 -> xmeas_11 | 1 | 0.2172 | 0.7015 | 0.7161 |
| xmeas_33 -> xmv_09 | 1 | 0.2045 | 0.0000 | 0.0281 |
| xmv_05 -> xmeas_20 | 1 | 0.1887 | 0.6647 | 0.8305 |
| xmeas_08 -> xmeas_26 | 1 | 0.1775 | 0.3246 | 0.3599 |

### Edge Prior Audit

- modes: `{'edge_dual_lattice': 3}`
- density: `0.0763 +/- 0.0003`
- uncapped edges mean: `1882.7`
- corroborated edges mean: `0.0`
- single-view edges mean: `0.0`
- top-edge family counts: `{}`
