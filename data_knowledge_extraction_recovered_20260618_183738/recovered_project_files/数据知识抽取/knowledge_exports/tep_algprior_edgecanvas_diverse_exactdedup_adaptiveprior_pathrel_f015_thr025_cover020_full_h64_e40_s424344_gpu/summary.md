# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_canvas-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6234 +/- 0.0039 | 0.6360 +/- 0.0033 | 0.0000 | 0.0000 | 0.1026 | 0.4075 | 0.9669 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9711.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_28 -> xmeas_07 | xmeas_28 -> xmeas_07 | 0.4458 | 0.5582 | 0.5754 | 0.0000 | 0.0001 | 1.0 |
| xmeas_39 -> xmeas_20 | xmeas_39 -> xmeas_20 | 0.3658 | 0.4180 | 0.5506 | 0.0000 | 0.0034 | 1.0 |
| xmeas_37 -> xmeas_19 | xmeas_37 -> xmeas_19 | 0.3272 | 0.3781 | 0.6124 | 0.0000 | 0.6313 | 1.0 |
| xmeas_31 -> xmeas_37 | xmeas_31 -> xmeas_37 | 0.3035 | 0.1883 | 0.6315 | 0.0000 | 0.4898 | 1.0 |
| xmv_08 -> xmeas_01 | xmv_08 -> xmeas_01 | 0.2935 | 0.1170 | 0.6073 | 0.0000 | 0.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_31 -> xmv_10 | xmeas_31 -> xmv_10 | 0.5021 | 0.7768 | 0.1734 | 0.6489 | 0.8125 | 1.0 |
| xmeas_20 -> xmeas_01 | xmeas_20 -> xmeas_01 | 0.3489 | 0.7647 | 0.3004 | 0.6099 | 0.8124 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3258 | 0.8122 | 0.1296 | 0.7140 | 0.8998 | 1.0 |
| xmeas_10 -> xmeas_01 | xmeas_10 -> xmeas_01 | 0.3184 | 0.5980 | 0.8546 | 0.0000 | 0.6707 | 1.0 |
| xmeas_39 -> xmv_09 | xmeas_39 -> xmv_09 | 0.3137 | 0.5602 | 0.6649 | 0.0000 | 0.4436 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmeas_25 | xmeas_14 -> xmeas_25 | 0.3493 | 0.7435 | 0.6186 | 0.0000 | 0.0000 | 1.0 |
| xmeas_06 -> xmeas_11 | xmeas_06 -> xmeas_11 | 0.3143 | 0.6684 | 0.6576 | 0.0000 | 0.1689 | 1.0 |
| xmeas_26 -> xmv_05 | xmeas_26 -> xmv_05 | 0.3117 | 0.8162 | 0.5117 | 0.0000 | 0.9999 | 1.0 |
| xmeas_06 -> xmeas_38 | xmeas_06 -> xmeas_38 | 0.3010 | 0.6379 | 0.7404 | 0.0000 | 0.3571 | 1.0 |
| xmeas_34 -> xmeas_33 | xmeas_34 -> xmeas_33 | 0.2934 | 0.8054 | 0.6242 | 0.0000 | 0.8920 | 1.0 |

