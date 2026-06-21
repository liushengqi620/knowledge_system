# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_canvas-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6244 +/- 0.0037 | 0.6369 +/- 0.0022 | 0.0175 | 0.0175 | 0.0906 | 0.4254 | 1.0069 | 1.0000 | 0.3129 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10666.7 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmeas_13 | xmv_05 -> xmeas_13 | 0.3360 | 0.7891 | 0.7527 | 0.0000 | 0.9796 | 1.0 |
| xmv_05 -> xmeas_17 | xmv_05 -> xmeas_17 | 0.3245 | 0.8187 | 0.7735 | 0.0000 | 0.9821 | 1.0 |
| xmv_05 -> xmeas_35 | xmv_05 -> xmeas_35 | 0.3001 | 0.6171 | 0.7406 | 0.0000 | 0.8256 | 1.0 |
| xmeas_35 -> xmeas_14 | xmeas_35 -> xmeas_14 | 0.2710 | 0.4083 | 0.7417 | 0.0000 | 0.0006 | 1.0 |
| xmeas_26 -> xmeas_15 | xmeas_26 -> xmeas_15 | 0.2618 | 0.4742 | 0.7613 | 0.0000 | 0.0010 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.6621 | 0.7588 | 0.2481 | 0.5865 | 0.8696 | 1.0 |
| xmeas_06 -> xmv_04 | xmeas_06 -> xmv_04 | 0.5335 | 0.7900 | 0.3274 | 0.4582 | 0.8778 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3125 | 0.7798 | 0.3113 | 0.4874 | 0.8148 | 1.0 |
| xmeas_33 -> xmeas_13 | xmeas_33 -> xmeas_13 | 0.2998 | 0.6089 | 0.2440 | 0.4144 | 0.7394 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.2664 | 0.7416 | 0.2581 | 0.4793 | 0.6166 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_28 -> xmeas_30 | xmeas_28 -> xmeas_30 | 0.4152 | 0.7040 | 0.3041 | 0.4226 | 0.8036 | 1.0 |
| xmeas_08 -> xmeas_19 | xmeas_08 -> xmeas_19 | 0.3773 | 0.4869 | 0.8640 | 0.0000 | 0.5880 | 1.0 |
| xmv_06 -> xmeas_22 | xmv_06 -> xmeas_22 | 0.3561 | 0.6911 | 0.5878 | 0.0000 | 0.6844 | 1.0 |
| xmeas_07 -> xmeas_31 | xmeas_07 -> xmeas_31 | 0.3315 | 0.5171 | 0.1868 | 0.5415 | 0.6111 | 1.0 |
| xmeas_25 -> xmeas_19 | xmeas_25 -> xmeas_19 | 0.3129 | 0.3872 | 0.7191 | 0.0000 | 0.2363 | 1.0 |

