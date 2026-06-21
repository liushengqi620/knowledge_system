# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_overlay-k20-g4-lag3-vote2-sv0.25-vb0.12-gb5.0-pool3.0-rank0.25@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6303 +/- 0.0019 | 0.6426 +/- 0.0057 | 0.0175 | 0.0175 | 0.0939 | 0.3349 | 0.7847 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11850.2 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3552 | 0.8071 | 0.3060 | 0.6780 | 0.8588 | 1.0 |
| xmeas_18 -> xmeas_23 | xmeas_18 -> xmeas_23 | 0.2327 | 0.3093 | 0.3629 | 0.0000 | 0.1253 | 1.0 |
| xmeas_38 -> xmeas_19 | xmeas_38 -> xmeas_19 | 0.2214 | 0.7197 | 0.3918 | 0.0000 | 0.1421 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2153 | 0.7414 | 0.4768 | 0.7284 | 0.7925 | 1.0 |
| xmeas_38 -> xmv_05 | xmeas_38 -> xmv_05 | 0.2084 | 0.7934 | 0.3537 | 0.0000 | 0.6605 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3869 | 0.7132 | 0.3201 | 0.4990 | 0.6385 | 1.0 |
| xmv_09 -> xmv_03 | xmv_09 -> xmv_03 | 0.3752 | 0.5874 | 0.3610 | 0.0000 | 0.6398 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.3212 | 0.6730 | 0.3756 | 0.0000 | 0.9947 | 1.0 |
| xmeas_20 -> xmv_05 | xmeas_20 -> xmv_05 | 0.2939 | 0.6201 | 0.0611 | 0.6547 | 0.7967 | 1.0 |
| xmeas_09 -> xmeas_01 | xmeas_09 -> xmeas_01 | 0.2668 | 0.5905 | 0.5755 | 0.0000 | 0.8149 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3589 | 0.7999 | 0.5220 | 0.6407 | 0.8136 | 1.0 |
| xmv_06 -> xmeas_10 | xmv_06 -> xmeas_10 | 0.2837 | 0.7104 | 0.3207 | 0.8741 | 0.8736 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2666 | 0.7892 | 0.0630 | 0.6428 | 0.8219 | 1.0 |
| xmv_07 -> xmv_10 | xmv_07 -> xmv_10 | 0.2171 | 0.7237 | 0.3325 | 0.0000 | 0.2358 | 1.0 |
| xmeas_41 -> xmeas_25 | xmeas_41 -> xmeas_25 | 0.2122 | 0.6515 | 0.3566 | 0.0000 | 0.0370 | 1.0 |

