# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+edge-cal-f0.05-b1.5-reg0.05+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6307 +/- 0.0072 | 0.6411 +/- 0.0098 | 0.0175 | 0.0175 | 0.0852 | 0.3356 | 0.7829 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10580.0 | 166677 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3492 | 0.8622 | 0.2247 | 0.6615 | 0.7761 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3160 | 0.8593 | 0.0124 | 0.5383 | 0.8569 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.2764 | 0.6757 | 0.3809 | 0.2698 | 0.8210 | 1.0 |
| xmeas_22 -> xmv_02 | xmeas_22 -> xmv_02 | 0.2748 | 0.6942 | 0.3525 | 0.0000 | 0.8801 | 1.0 |
| xmeas_40 -> xmv_06 | xmeas_40 -> xmv_06 | 0.2562 | 0.9244 | 0.4184 | 0.0000 | 0.0728 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.5536 | 0.6877 | 0.1875 | 0.5004 | 0.6371 | 1.0 |
| xmeas_22 -> xmv_01 | xmeas_22 -> xmv_01 | 0.5354 | 0.6117 | 0.4065 | 0.0000 | 0.2502 | 1.0 |
| xmeas_13 -> xmeas_01 | xmeas_13 -> xmeas_01 | 0.3725 | 0.6413 | 0.4058 | 0.0000 | 0.8356 | 1.0 |
| xmeas_29 -> xmeas_13 | xmeas_29 -> xmeas_13 | 0.2013 | 0.7653 | 0.3181 | 0.0000 | 0.8122 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.1912 | 0.5046 | 0.2163 | 0.3756 | 0.6305 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_22 -> xmeas_04 | xmeas_22 -> xmeas_04 | 0.2884 | 0.5553 | 0.4036 | 0.0000 | 0.8024 | 1.0 |
| xmeas_30 -> xmeas_01 | xmeas_30 -> xmeas_01 | 0.2648 | 0.7970 | 0.3943 | 0.0000 | 0.0070 | 1.0 |
| xmeas_20 -> xmeas_23 | xmeas_20 -> xmeas_23 | 0.2543 | 0.7736 | 0.0965 | 0.5073 | 0.5905 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2360 | 0.6366 | 0.1533 | 0.4914 | 0.6410 | 1.0 |
| xmeas_30 -> xmeas_39 | xmeas_30 -> xmeas_39 | 0.2221 | 0.7221 | 0.3738 | 0.0000 | 0.0739 | 1.0 |

