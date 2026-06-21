# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.10+alg-prior-edge_canvas-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6225 +/- 0.0091 | 0.6346 +/- 0.0082 | 0.0175 | 0.0175 | 0.0813 | 0.4148 | 1.0428 | 1.0000 | 0.3438 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10985.5 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_02 -> xmv_05 | xmv_02 -> xmv_05 | 0.4164 | 0.9024 | 0.4126 | 0.6412 | 0.9088 | 1.0 |
| xmeas_30 -> xmeas_28 | xmeas_30 -> xmeas_28 | 0.4111 | 0.8344 | 0.6060 | 0.3487 | 0.4572 | 1.0 |
| xmv_05 -> xmeas_13 | xmv_05 -> xmeas_13 | 0.3967 | 0.8048 | 0.3370 | 0.7185 | 0.9167 | 1.0 |
| xmeas_17 -> xmeas_12 | xmeas_17 -> xmeas_12 | 0.3153 | 0.7980 | 0.3060 | 0.2921 | 0.7844 | 1.0 |
| xmeas_17 -> xmv_01 | xmeas_17 -> xmv_01 | 0.2891 | 0.1165 | 0.6781 | 0.0000 | 0.0692 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_20 -> xmeas_01 | xmeas_20 -> xmeas_01 | 0.5218 | 0.8082 | 0.1888 | 0.6607 | 0.8957 | 1.0 |
| xmv_10 -> xmv_03 | xmv_10 -> xmv_03 | 0.5077 | 0.8900 | 0.1480 | 0.6158 | 0.6646 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.4124 | 0.7641 | 0.1813 | 0.6920 | 0.8652 | 1.0 |
| xmeas_10 -> xmeas_01 | xmeas_10 -> xmeas_01 | 0.3052 | 0.7674 | 0.7384 | 0.0000 | 0.9843 | 1.0 |
| xmeas_24 -> xmeas_27 | xmeas_24 -> xmeas_27 | 0.3051 | 0.5342 | 0.7636 | 0.0000 | 0.6469 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_24 -> xmeas_11 | xmeas_24 -> xmeas_11 | 0.3692 | 0.4687 | 0.6475 | 0.0000 | 0.7616 | 1.0 |
| xmeas_24 -> xmeas_28 | xmeas_24 -> xmeas_28 | 0.3487 | 0.5419 | 0.7822 | 0.0000 | 0.2236 | 1.0 |
| xmeas_06 -> xmeas_11 | xmeas_06 -> xmeas_11 | 0.2883 | 0.3785 | 0.7966 | 0.0000 | 0.1454 | 1.0 |
| xmeas_15 -> xmeas_37 | xmeas_15 -> xmeas_37 | 0.2680 | 0.1326 | 0.6419 | 0.0000 | 0.0012 | 1.0 |
| xmeas_28 -> xmv_03 | xmeas_28 -> xmv_03 | 0.2664 | 0.9054 | 0.2606 | 0.6362 | 0.9194 | 1.0 |

