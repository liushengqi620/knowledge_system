# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6307 +/- 0.0045 | 0.6438 +/- 0.0037 | 0.0000 | 0.0000 | 0.0848 | 0.3370 | 0.7935 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 12554.7 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2522 | 0.7751 | 0.2157 | 0.6766 | 0.8002 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2464 | 0.5227 | 0.3929 | 0.3328 | 0.2117 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2452 | 0.7085 | 0.5773 | 0.0000 | 0.2613 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2181 | 0.5382 | 0.3217 | 0.2743 | 0.8363 | 1.0 |
| xmeas_20 -> xmeas_27 | xmeas_20 -> xmeas_27 | 0.2145 | 0.8050 | 0.0581 | 0.3629 | 0.3907 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4734 | 0.7671 | 0.2697 | 0.5018 | 0.6341 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.3157 | 0.8834 | 0.4744 | 0.0000 | 0.9953 | 1.0 |
| xmeas_37 -> xmeas_09 | xmeas_37 -> xmeas_09 | 0.2826 | 0.4785 | 0.4356 | 0.0000 | 0.3364 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.2284 | 0.7203 | 0.4943 | 0.0000 | 0.9910 | 1.0 |
| xmeas_30 -> xmeas_19 | xmeas_30 -> xmeas_19 | 0.2192 | 0.6398 | 0.3694 | 0.0000 | 0.3068 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_08 -> xmeas_34 | xmeas_08 -> xmeas_34 | 0.3697 | 0.6760 | 0.5165 | 0.0000 | 0.4942 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2974 | 0.7444 | 0.0814 | 0.5810 | 0.8428 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2394 | 0.8656 | 0.4409 | 0.0000 | 0.7853 | 1.0 |
| xmeas_21 -> xmv_05 | xmeas_21 -> xmv_05 | 0.2335 | 0.4387 | 0.4894 | 0.0000 | 0.7347 | 1.0 |
| xmeas_30 -> xmeas_17 | xmeas_30 -> xmeas_17 | 0.2127 | 0.6597 | 0.4373 | 0.0000 | 0.0030 | 1.0 |

