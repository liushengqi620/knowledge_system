# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.50-thr0.35-t0.05-f0.20-retain0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6344 +/- 0.0055 | 0.6468 +/- 0.0008 | 0.0000 | 0.0000 | 0.0861 | 0.4008 | 0.7688 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11672.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.6044 | 0.7718 | 0.1450 | 0.6369 | 0.7376 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3601 | 0.2181 | 0.0845 | 0.5051 | 0.3477 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2686 | 0.7421 | 0.2890 | 0.0000 | 0.2127 | 1.0 |
| xmv_10 -> xmeas_12 | xmv_10 -> xmeas_12 | 0.2254 | 0.7278 | 0.2889 | 0.0000 | 0.4720 | 1.0 |
| xmeas_18 -> xmeas_04 | xmeas_18 -> xmeas_04 | 0.2024 | 0.3937 | 0.4493 | 0.0000 | 0.3790 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3748 | 0.6486 | 0.0921 | 0.5115 | 0.6475 | 1.0 |
| xmeas_30 -> xmeas_25 | xmeas_30 -> xmeas_25 | 0.3185 | 0.6745 | 0.3227 | 0.0000 | 0.6019 | 1.0 |
| xmeas_20 -> xmv_03 | xmeas_20 -> xmv_03 | 0.3086 | 0.7641 | 0.5684 | 0.0000 | 0.6231 | 1.0 |
| xmeas_11 -> xmeas_01 | xmeas_11 -> xmeas_01 | 0.2892 | 0.6753 | 0.2820 | 0.0000 | 0.7198 | 1.0 |
| xmv_03 -> xmv_05 | xmv_03 -> xmv_05 | 0.2889 | 0.5741 | 0.4333 | 0.0000 | 0.7149 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_15 -> xmeas_13 | xmeas_15 -> xmeas_13 | 0.4938 | 0.6724 | 0.2852 | 0.0000 | 0.6336 | 1.0 |
| xmv_08 -> xmv_05 | xmv_08 -> xmv_05 | 0.3638 | 0.6285 | 0.4818 | 0.0000 | 0.9834 | 1.0 |
| xmeas_20 -> xmeas_39 | xmeas_20 -> xmeas_39 | 0.3574 | 0.5152 | 0.2989 | 0.0000 | 0.6505 | 1.0 |
| xmeas_01 -> xmeas_25 | xmeas_01 -> xmeas_25 | 0.2927 | 0.7942 | 0.7697 | 0.0000 | 0.9577 | 1.0 |
| xmeas_20 -> xmeas_40 | xmeas_20 -> xmeas_40 | 0.2721 | 0.3942 | 0.2224 | 0.0000 | 0.5956 | 1.0 |

