# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.05-thr0.50-t0.05-relative_evidence-s0.50+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_cert_overlay-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6316 +/- 0.0094 | 0.6433 +/- 0.0116 | 0.0175 | 0.0175 | 0.0847 | 0.3598 | 0.8009 | 1.0000 | 0.3609 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7297.4 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmeas_21 | xmeas_37 -> xmeas_21 | 0.2289 | 0.2946 | 0.3953 | 0.0000 | 0.1048 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2203 | 0.8851 | 0.4330 | 0.6538 | 0.7636 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.2179 | 0.5903 | 0.2683 | 0.4305 | 0.3318 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.1828 | 0.8093 | 0.7672 | 0.0000 | 0.1515 | 1.0 |
| xmeas_08 -> xmv_05 | xmeas_08 -> xmv_05 | 0.1745 | 0.8472 | 0.6435 | 0.0000 | 0.5465 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4367 | 0.8269 | 0.2019 | 0.5193 | 0.6652 | 1.0 |
| xmeas_31 -> xmeas_02 | xmeas_31 -> xmeas_02 | 0.2610 | 0.3939 | 0.4959 | 0.0000 | 0.0009 | 1.0 |
| xmeas_23 -> xmeas_38 | xmeas_23 -> xmeas_38 | 0.2277 | 0.5988 | 0.6837 | 0.0000 | 0.7601 | 1.0 |
| xmeas_38 -> xmeas_04 | xmeas_38 -> xmeas_04 | 0.2163 | 0.7912 | 0.7060 | 0.0000 | 0.5993 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2056 | 0.8060 | 0.7827 | 0.0000 | 0.6883 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3181 | 0.8043 | 0.4138 | 0.5749 | 0.8322 | 1.0 |
| xmeas_20 -> xmeas_04 | xmeas_20 -> xmeas_04 | 0.2284 | 0.3727 | 0.5907 | 0.0000 | 0.4915 | 1.0 |
| xmeas_39 -> xmv_05 | xmeas_39 -> xmv_05 | 0.2258 | 0.6572 | 0.4693 | 0.0000 | 0.8853 | 1.0 |
| xmeas_20 -> xmeas_29 | xmeas_20 -> xmeas_29 | 0.2254 | 0.6446 | 0.0940 | 0.5094 | 0.6099 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2225 | 0.8199 | 0.7267 | 0.0000 | 0.9026 | 1.0 |

