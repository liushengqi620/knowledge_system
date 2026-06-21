# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-edge_bank-k16-lag3-vote2-sv0.45-vb0.15-gb4.0@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6209 +/- 0.0052 | 0.6450 +/- 0.0035 | 0.0000 | 0.0000 | 0.2231 | 0.3425 | 0.7422 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 18442.0 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_07 -> xmv_11 | xmv_07 -> xmv_11 | 0.3856 | 0.9412 | 0.4265 | 0.0000 | 0.7754 | 1.0 |
| xmeas_17 -> xmv_11 | xmeas_17 -> xmv_11 | 0.3416 | 0.9482 | 0.0981 | 0.8592 | 0.7397 | 1.0 |
| xmeas_06 -> xmeas_25 | xmeas_06 -> xmeas_25 | 0.2936 | 0.4497 | 0.4237 | 0.0000 | 0.1803 | 1.0 |
| xmv_11 -> xmeas_25 | xmv_11 -> xmeas_25 | 0.2893 | 0.8994 | 0.2756 | 0.7232 | 0.5999 | 1.0 |
| xmv_10 -> xmv_11 | xmv_10 -> xmv_11 | 0.2722 | 0.8291 | 0.1412 | 0.7675 | 0.7106 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmv_04 | xmeas_18 -> xmv_04 | 0.3895 | 0.8162 | 0.5078 | 0.0000 | 0.9743 | 1.0 |
| xmeas_36 -> xmv_03 | xmeas_36 -> xmv_03 | 0.3829 | 0.7633 | 0.4321 | 0.0000 | 0.6512 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.3810 | 0.7593 | 0.5155 | 0.0000 | 0.9586 | 1.0 |
| xmeas_10 -> xmeas_01 | xmeas_10 -> xmeas_01 | 0.3440 | 0.7286 | 0.5498 | 0.0000 | 0.7610 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.3367 | 0.8198 | 0.0563 | 0.7073 | 0.6081 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_12 -> xmv_05 | xmeas_12 -> xmv_05 | 0.5284 | 0.5116 | 0.4444 | 0.0000 | 0.3944 | 1.0 |
| xmeas_13 -> xmv_05 | xmeas_13 -> xmv_05 | 0.2720 | 0.5612 | 0.1330 | 0.6376 | 0.8780 | 1.0 |
| xmeas_18 -> xmeas_09 | xmeas_18 -> xmeas_09 | 0.2308 | 0.6707 | 0.3481 | 0.0000 | 0.4210 | 1.0 |
| xmv_10 -> xmeas_23 | xmv_10 -> xmeas_23 | 0.2291 | 0.6844 | 0.2312 | 0.6852 | 0.4995 | 1.0 |
| xmeas_06 -> xmeas_10 | xmeas_06 -> xmeas_10 | 0.2283 | 0.3297 | 0.4131 | 0.0000 | 0.0075 | 1.0 |

