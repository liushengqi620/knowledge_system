# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+edge-family-router-t0.50-f0.05-b0.25+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6211 +/- 0.0022 | 0.6315 +/- 0.0016 | 0.0175 | 0.0175 | 0.0827 | 0.4126 | 1.0652 | 1.0000 | 0.3048 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10479.2 | 162644 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_29 -> xmeas_28 | xmeas_29 -> xmeas_28 | 0.5242 | 0.5306 | 0.7525 | 0.0000 | 0.4825 | 1.0 |
| xmv_05 -> xmv_01 | xmv_05 -> xmv_01 | 0.4140 | 0.7827 | 0.1993 | 0.4950 | 0.9842 | 1.0 |
| xmeas_08 -> xmeas_40 | xmeas_08 -> xmeas_40 | 0.3920 | 0.4902 | 0.9169 | 0.0000 | 0.0000 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3610 | 0.8285 | 0.4742 | 0.5292 | 0.9082 | 1.0 |
| xmeas_08 -> xmeas_27 | xmeas_08 -> xmeas_27 | 0.3459 | 0.2592 | 0.6863 | 0.0000 | 0.3335 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_10 -> xmeas_03 | xmeas_10 -> xmeas_03 | 0.4078 | 0.4433 | 0.2552 | 0.0664 | 0.0000 | 1.0 |
| xmv_05 -> xmeas_23 | xmv_05 -> xmeas_23 | 0.3504 | 0.7916 | 0.2243 | 0.4753 | 0.8892 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.3392 | 0.9058 | 0.1524 | 0.4606 | 0.8612 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.3361 | 0.8923 | 0.2182 | 0.4997 | 0.6268 | 1.0 |
| xmeas_32 -> xmeas_19 | xmeas_32 -> xmeas_19 | 0.3298 | 0.8166 | 0.4870 | 0.2426 | 0.6914 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmeas_27 | xmeas_30 -> xmeas_27 | 0.4744 | 0.3880 | 0.6351 | 0.0000 | 0.0180 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4238 | 0.8732 | 0.6106 | 0.5478 | 0.8754 | 1.0 |
| xmeas_18 -> xmeas_03 | xmeas_18 -> xmeas_03 | 0.3172 | 0.4989 | 0.7125 | 0.0000 | 0.0361 | 1.0 |
| xmeas_30 -> xmv_05 | xmeas_30 -> xmv_05 | 0.3044 | 0.6774 | 0.5600 | 0.0000 | 0.2664 | 1.0 |
| xmeas_28 -> xmeas_03 | xmeas_28 -> xmeas_03 | 0.2972 | 0.5155 | 0.7029 | 0.0000 | 0.1353 | 1.0 |

