# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.25-thr0.35-t0.05-f0.20-agreement+stable-path-static_lag-s4-v0.50-w0.50-lag3@0.50-path-off-edge4+stable-class-edge-overlay-max-s0.25-k8-g2-fw1.25-nw0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@1.00@8+path-aux@0.05+router@0.05 | 3 | 0.6300 +/- 0.0053 | 0.6398 +/- 0.0076 | 0.0175 | 0.0175 | 0.0870 | 0.3506 | 0.7830 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12018.9 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4909 | 0.8613 | 0.2671 | 0.6264 | 0.7254 | 1.0 |
| xmeas_12 -> xmeas_19 | xmeas_12 -> xmeas_19 | 0.4837 | 0.8218 | 0.3463 | 0.0000 | 0.0935 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3705 | 0.8626 | 0.0800 | 0.5570 | 0.8892 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2831 | 0.6398 | 0.3055 | 0.2672 | 0.8074 | 1.0 |
| xmeas_20 -> xmeas_19 | xmeas_20 -> xmeas_19 | 0.2450 | 0.7205 | 0.2894 | 0.0000 | 0.0387 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4115 | 0.7336 | 0.2494 | 0.4887 | 0.6126 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.3523 | 0.6602 | 0.0574 | 0.1618 | 0.6440 | 1.0 |
| xmeas_33 -> xmeas_01 | xmeas_33 -> xmeas_01 | 0.3233 | 0.6126 | 0.3624 | 0.0000 | 0.7087 | 1.0 |
| xmeas_24 -> xmv_03 | xmeas_24 -> xmv_03 | 0.2701 | 0.7377 | 0.3775 | 0.0000 | 0.6316 | 1.0 |
| xmeas_20 -> xmv_05 | xmeas_20 -> xmv_05 | 0.2440 | 0.4732 | 0.0746 | 0.5461 | 0.5749 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmv_10 | xmv_01 -> xmv_10 | 0.4225 | 0.6093 | 0.3591 | 0.0000 | 0.3294 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3987 | 0.7141 | 0.1542 | 0.5800 | 0.8406 | 1.0 |
| xmeas_20 -> xmeas_16 | xmeas_20 -> xmeas_16 | 0.2961 | 0.5494 | 0.2778 | 0.0000 | 0.0115 | 1.0 |
| xmeas_32 -> xmv_05 | xmeas_32 -> xmv_05 | 0.2538 | 0.6363 | 0.2583 | 0.0000 | 0.9980 | 1.0 |
| xmeas_21 -> xmv_05 | xmeas_21 -> xmv_05 | 0.2442 | 0.5414 | 0.4728 | 0.0000 | 0.7389 | 1.0 |

