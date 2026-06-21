# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.05-thr0.50-t0.05-relative_evidence-s0.50-feature+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_cert_overlay-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6284 +/- 0.0064 | 0.6418 +/- 0.0054 | 0.0351 | 0.0351 | 0.0857 | 0.3604 | 0.8112 | 1.0000 | 0.3580 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7176.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.4251 | 0.7274 | 0.0818 | 0.5397 | 0.8560 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3774 | 0.6245 | 0.4112 | 0.3553 | 0.1779 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2883 | 0.8823 | 0.3838 | 0.6286 | 0.7219 | 1.0 |
| xmeas_18 -> xmeas_29 | xmeas_18 -> xmeas_29 | 0.1728 | 0.7477 | 0.4801 | 0.0000 | 0.8364 | 1.0 |
| xmeas_36 -> xmeas_13 | xmeas_36 -> xmeas_13 | 0.1529 | 0.4377 | 0.1108 | 0.4443 | 0.5430 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3955 | 0.7926 | 0.2351 | 0.5089 | 0.6451 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2303 | 0.6938 | 0.7380 | 0.0000 | 0.6822 | 1.0 |
| xmeas_20 -> xmv_05 | xmeas_20 -> xmv_05 | 0.1636 | 0.6156 | 0.1291 | 0.5407 | 0.5632 | 1.0 |
| xmeas_35 -> xmeas_09 | xmeas_35 -> xmeas_09 | 0.1574 | 0.6221 | 0.6193 | 0.0000 | 0.6431 | 1.0 |
| xmeas_04 -> xmv_11 | xmeas_04 -> xmv_11 | 0.1555 | 0.4965 | 0.4451 | 0.0000 | 0.1032 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_20 -> xmeas_29 | xmeas_20 -> xmeas_29 | 0.3106 | 0.6675 | 0.0987 | 0.5074 | 0.6030 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2555 | 0.7805 | 0.6574 | 0.0000 | 0.9003 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2355 | 0.6773 | 0.3205 | 0.3988 | 0.2969 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2312 | 0.7637 | 0.3979 | 0.5748 | 0.8307 | 1.0 |
| xmeas_11 -> xmeas_13 | xmeas_11 -> xmeas_13 | 0.2172 | 0.6730 | 0.0738 | 0.7108 | 0.8266 | 1.0 |

