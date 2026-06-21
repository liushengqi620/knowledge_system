# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.35-thr0.35-t0.05-f0.20-evidence_admit-retain0.50+stable-path-static_lag-s4-v0.50-w0.50-lag3@0.50-path-off-edge4+stable-class-edge-overlay-max-s0.25-k8-g2-fw1.25-nw0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@1.00@8+path-aux@0.05+router@0.05 | 3 | 0.6288 +/- 0.0029 | 0.6418 +/- 0.0032 | 0.0175 | 0.0175 | 0.0868 | 0.3787 | 0.7612 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10117.9 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmeas_13 | xmv_05 -> xmeas_13 | 0.4737 | 0.8172 | 0.0585 | 0.2445 | 0.9759 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3453 | 0.5878 | 0.2665 | 0.3256 | 0.2163 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3135 | 0.8374 | 0.4403 | 0.6245 | 0.7195 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2792 | 0.7315 | 0.0349 | 0.5593 | 0.8937 | 1.0 |
| xmeas_18 -> xmv_09 | xmeas_18 -> xmv_09 | 0.2450 | 0.6863 | 0.1037 | 0.4618 | 0.4496 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_15 -> xmeas_01 | xmeas_15 -> xmeas_01 | 0.5908 | 0.7364 | 0.2931 | 0.0000 | 0.9960 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4124 | 0.7377 | 0.2513 | 0.4924 | 0.6129 | 1.0 |
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.3965 | 0.7621 | 0.4149 | 0.0000 | 0.9894 | 1.0 |
| xmeas_20 -> xmeas_01 | xmeas_20 -> xmeas_01 | 0.2790 | 0.7002 | 0.3842 | 0.0000 | 0.9588 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.2410 | 0.6085 | 0.1645 | 0.4049 | 0.6775 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_36 -> xmv_05 | xmeas_36 -> xmv_05 | 0.2801 | 0.5408 | 0.2858 | 0.0000 | 0.9744 | 1.0 |
| xmeas_11 -> xmeas_13 | xmeas_11 -> xmeas_13 | 0.2706 | 0.5317 | 0.0658 | 0.6291 | 0.7056 | 1.0 |
| xmeas_15 -> xmv_05 | xmeas_15 -> xmv_05 | 0.2683 | 0.6613 | 0.2742 | 0.0000 | 0.9940 | 1.0 |
| xmeas_29 -> xmv_05 | xmeas_29 -> xmv_05 | 0.2548 | 0.5453 | 0.2716 | 0.0000 | 0.8410 | 1.0 |
| xmeas_30 -> xmeas_13 | xmeas_30 -> xmeas_13 | 0.2513 | 0.7693 | 0.3435 | 0.0000 | 0.1321 | 1.0 |

