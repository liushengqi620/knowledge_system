# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.50-thr0.35-t0.05-f0.20-prior+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6310 +/- 0.0052 | 0.6415 +/- 0.0066 | 0.0175 | 0.0175 | 0.0887 | 0.3437 | 0.7915 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11459.0 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_17 -> xmv_09 | xmeas_17 -> xmv_09 | 0.3184 | 0.4293 | 0.2154 | 0.0000 | 0.0009 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.3182 | 0.6765 | 0.2655 | 0.0000 | 0.1331 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3115 | 0.4543 | 0.1018 | 0.3453 | 0.2651 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2994 | 0.7528 | 0.1658 | 0.5827 | 0.6622 | 1.0 |
| xmv_05 -> xmv_09 | xmv_05 -> xmv_09 | 0.2557 | 0.7599 | 0.2418 | 0.4638 | 0.7701 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_27 -> xmv_10 | xmeas_27 -> xmv_10 | 0.5304 | 0.5798 | 0.2472 | 0.0000 | 0.6832 | 1.0 |
| xmeas_20 -> xmv_03 | xmeas_20 -> xmv_03 | 0.4351 | 0.6542 | 0.4698 | 0.0000 | 0.6297 | 1.0 |
| xmeas_20 -> xmv_05 | xmeas_20 -> xmv_05 | 0.2883 | 0.5779 | 0.0913 | 0.5177 | 0.5310 | 1.0 |
| xmeas_30 -> xmv_03 | xmeas_30 -> xmv_03 | 0.2491 | 0.5687 | 0.3004 | 0.0000 | 0.5526 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2358 | 0.8650 | 0.9283 | 0.6377 | 0.8045 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2628 | 0.6671 | 0.5135 | 0.4866 | 0.6602 | 1.0 |
| xmeas_28 -> xmeas_03 | xmeas_28 -> xmeas_03 | 0.2506 | 0.4881 | 0.2413 | 0.0000 | 0.0015 | 1.0 |
| xmeas_09 -> xmv_02 | xmeas_09 -> xmv_02 | 0.2374 | 0.3364 | 0.2294 | 0.0000 | 0.4774 | 1.0 |
| xmv_01 -> xmv_10 | xmv_01 -> xmv_10 | 0.1921 | 0.5511 | 0.2866 | 0.0000 | 0.4103 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.1674 | 0.5615 | 0.1137 | 0.4834 | 0.4376 | 1.0 |

