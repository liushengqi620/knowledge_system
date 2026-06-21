# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6284 +/- 0.0130 | 0.6363 +/- 0.0119 | 0.0175 | 0.0175 | 0.0827 | 0.3480 | 0.7756 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12519.0 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4911 | 0.8310 | 0.2438 | 0.5956 | 0.6884 | 1.0 |
| xmeas_14 -> xmv_09 | xmeas_14 -> xmv_09 | 0.4104 | 0.3229 | 0.2996 | 0.0000 | 0.0016 | 1.0 |
| xmv_11 -> xmeas_09 | xmv_11 -> xmeas_09 | 0.3272 | 0.6628 | 0.3752 | 0.0000 | 0.4798 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3018 | 0.6572 | 0.5279 | 0.2730 | 0.8334 | 1.0 |
| xmeas_13 -> xmeas_09 | xmeas_13 -> xmeas_09 | 0.2811 | 0.4415 | 0.3389 | 0.0000 | 0.3346 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_08 -> xmv_04 | xmeas_08 -> xmv_04 | 0.5199 | 0.8062 | 0.1509 | 0.4235 | 0.7824 | 1.0 |
| xmeas_26 -> xmv_04 | xmeas_26 -> xmv_04 | 0.4483 | 0.8011 | 0.5191 | 0.0000 | 0.8915 | 1.0 |
| xmv_09 -> xmv_04 | xmv_09 -> xmv_04 | 0.4174 | 0.6914 | 0.4501 | 0.0000 | 0.5201 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4063 | 0.7733 | 0.2079 | 0.4880 | 0.6220 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.3933 | 0.6260 | 0.4116 | 0.0000 | 0.7634 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_11 -> xmeas_13 | xmeas_11 -> xmeas_13 | 0.4345 | 0.5829 | 0.0874 | 0.6373 | 0.7229 | 1.0 |
| xmeas_17 -> xmv_05 | xmeas_17 -> xmv_05 | 0.3769 | 0.4374 | 0.4191 | 0.0000 | 0.9933 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2468 | 0.6939 | 0.2852 | 0.5812 | 0.8445 | 1.0 |
| xmeas_26 -> xmeas_18 | xmeas_26 -> xmeas_18 | 0.2206 | 0.4172 | 0.3818 | 0.0000 | 0.6024 | 1.0 |
| xmeas_30 -> xmeas_18 | xmeas_30 -> xmeas_18 | 0.2058 | 0.7776 | 0.4288 | 0.0000 | 0.6995 | 1.0 |

