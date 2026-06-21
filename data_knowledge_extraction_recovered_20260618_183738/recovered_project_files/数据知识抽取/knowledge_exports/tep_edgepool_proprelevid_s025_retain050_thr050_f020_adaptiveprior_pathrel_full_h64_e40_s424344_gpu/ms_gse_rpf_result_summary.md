# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+path-proposal-cons-s0.25-thr0.50-t0.05-f0.20-relative_evidence-retain0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6280 +/- 0.0066 | 0.6390 +/- 0.0098 | 0.0351 | 0.0351 | 0.0893 | 0.3642 | 0.7761 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11484.4 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_32 -> xmeas_38 | xmeas_32 -> xmeas_38 | 0.5206 | 0.8497 | 0.3025 | 0.0000 | 0.8100 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3582 | 0.8748 | 0.8811 | 0.5338 | 0.8444 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3359 | 0.8040 | 0.2054 | 0.6120 | 0.6922 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3273 | 0.6921 | 0.2918 | 0.3436 | 0.2301 | 1.0 |
| xmeas_02 -> xmeas_19 | xmeas_02 -> xmeas_19 | 0.2331 | 0.4552 | 0.4094 | 0.0000 | 0.0688 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4107 | 0.7424 | 0.3143 | 0.4833 | 0.6044 | 1.0 |
| xmeas_29 -> xmv_03 | xmeas_29 -> xmv_03 | 0.3417 | 0.6338 | 0.2138 | 0.4428 | 0.6279 | 1.0 |
| xmeas_15 -> xmeas_01 | xmeas_15 -> xmeas_01 | 0.3284 | 0.7302 | 0.4863 | 0.0000 | 0.9968 | 1.0 |
| xmeas_20 -> xmeas_23 | xmeas_20 -> xmeas_23 | 0.3236 | 0.6441 | 0.0472 | 0.5082 | 0.4372 | 1.0 |
| xmeas_20 -> xmeas_01 | xmeas_20 -> xmeas_01 | 0.3090 | 0.7715 | 0.4007 | 0.0000 | 0.9938 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_06 -> xmv_05 | xmeas_06 -> xmv_05 | 0.3086 | 0.6837 | 0.2674 | 0.0000 | 0.7915 | 1.0 |
| xmeas_22 -> xmv_02 | xmeas_22 -> xmv_02 | 0.2747 | 0.6363 | 0.3046 | 0.0000 | 0.3850 | 1.0 |
| xmeas_29 -> xmeas_07 | xmeas_29 -> xmeas_07 | 0.2728 | 0.6958 | 0.4070 | 0.0000 | 0.8174 | 1.0 |
| xmeas_27 -> xmv_05 | xmeas_27 -> xmv_05 | 0.2689 | 0.5451 | 0.2619 | 0.0000 | 0.7763 | 1.0 |
| xmeas_32 -> xmv_05 | xmeas_32 -> xmv_05 | 0.2459 | 0.6443 | 0.2473 | 0.0000 | 0.8638 | 1.0 |

