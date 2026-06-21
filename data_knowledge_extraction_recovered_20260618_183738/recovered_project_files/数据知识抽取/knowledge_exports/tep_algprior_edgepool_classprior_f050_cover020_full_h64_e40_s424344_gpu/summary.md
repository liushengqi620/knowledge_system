# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6296 +/- 0.0042 | 0.6415 +/- 0.0043 | 0.0175 | 0.0175 | 0.1056 | 0.3214 | 0.8017 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12088.0 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4014 | 0.8645 | 0.2276 | 0.7130 | 0.7600 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3841 | 0.8975 | 0.1354 | 0.5761 | 0.8739 | 1.0 |
| xmeas_12 -> xmeas_19 | xmeas_12 -> xmeas_19 | 0.3613 | 0.6621 | 0.4166 | 0.0000 | 0.0929 | 1.0 |
| xmv_10 -> xmeas_31 | xmv_10 -> xmeas_31 | 0.3008 | 0.8443 | 0.5561 | 0.0000 | 0.1370 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2692 | 0.7031 | 0.3980 | 0.2966 | 0.8658 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4883 | 0.7526 | 0.3889 | 0.5842 | 0.6247 | 1.0 |
| xmeas_23 -> xmeas_01 | xmeas_23 -> xmeas_01 | 0.4382 | 0.7260 | 0.4826 | 0.0000 | 0.9607 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.2676 | 0.7894 | 0.5123 | 0.0000 | 0.9980 | 1.0 |
| xmeas_24 -> xmv_03 | xmeas_24 -> xmv_03 | 0.2514 | 0.7031 | 0.5323 | 0.0000 | 0.6125 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.2455 | 0.6733 | 0.4312 | 0.0000 | 0.9925 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2620 | 0.7557 | 0.1144 | 0.6159 | 0.8394 | 1.0 |
| xmeas_20 -> xmeas_17 | xmeas_20 -> xmeas_17 | 0.2306 | 0.5785 | 0.4063 | 0.0000 | 0.2217 | 1.0 |
| xmeas_20 -> xmeas_40 | xmeas_20 -> xmeas_40 | 0.2203 | 0.5916 | 0.3738 | 0.0000 | 0.5383 | 1.0 |
| xmeas_37 -> xmeas_23 | xmeas_37 -> xmeas_23 | 0.2074 | 0.4065 | 0.4390 | 0.0000 | 0.0122 | 1.0 |
| xmeas_32 -> xmeas_19 | xmeas_32 -> xmeas_19 | 0.1973 | 0.4430 | 0.3996 | 0.0000 | 0.0877 | 1.0 |

