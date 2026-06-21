# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6264 +/- 0.0082 | 0.6384 +/- 0.0104 | 0.0175 | 0.0175 | 0.1582 | 0.3060 | 0.7729 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11742.8 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4195 | 0.8693 | 0.1756 | 0.6149 | 0.7558 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3049 | 0.7887 | 0.5055 | 0.3180 | 0.7907 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2837 | 0.6902 | 0.2018 | 0.8852 | 0.2201 | 1.0 |
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.2834 | 0.7474 | 0.6001 | 0.0000 | 0.1056 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2649 | 0.7645 | 0.1245 | 0.8102 | 0.7420 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.5013 | 0.7501 | 0.3125 | 0.7191 | 0.6157 | 1.0 |
| xmeas_36 -> xmv_10 | xmeas_36 -> xmv_10 | 0.3796 | 0.7618 | 0.3574 | 0.0000 | 0.8587 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.3161 | 0.6505 | 0.4210 | 0.0000 | 0.9951 | 1.0 |
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.2855 | 0.7664 | 0.4551 | 0.0000 | 0.9958 | 1.0 |
| xmeas_14 -> xmv_09 | xmeas_14 -> xmv_09 | 0.2424 | 0.1297 | 0.4226 | 0.0000 | 0.0577 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_07 -> xmv_05 | xmv_07 -> xmv_05 | 0.3452 | 0.6260 | 0.2836 | 0.0000 | 0.9285 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3165 | 0.8342 | 0.3187 | 0.0000 | 0.5682 | 1.0 |
| xmeas_12 -> xmv_05 | xmeas_12 -> xmv_05 | 0.2927 | 0.7414 | 0.3072 | 0.0000 | 0.8173 | 1.0 |
| xmv_07 -> xmv_10 | xmv_07 -> xmv_10 | 0.2773 | 0.7614 | 0.3323 | 0.0000 | 0.2191 | 1.0 |
| xmeas_20 -> xmeas_16 | xmeas_20 -> xmeas_16 | 0.2507 | 0.6748 | 0.3045 | 0.0000 | 0.1005 | 1.0 |

