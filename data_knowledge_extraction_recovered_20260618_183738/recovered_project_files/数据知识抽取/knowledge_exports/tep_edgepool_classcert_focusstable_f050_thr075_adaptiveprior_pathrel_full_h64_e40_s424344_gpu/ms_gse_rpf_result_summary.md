# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+class-evid-cert-focus_stability-f0.50-thr0.75-t0.05+prior-cover@0.20+alg-prior-edge_pool-k8-g3-lag3-vote2-sv0.55-vb0.15-pool2.0-rank0.35@0.05+class-evidence-static_lag-lag3@0.50-family2@0.35-focus-low_train_separation6@0.15@8+path-aux@0.05+router@0.05 | 3 | 0.6266 +/- 0.0032 | 0.6399 +/- 0.0023 | 0.0000 | 0.0000 | 0.0363 | 0.0456 | 0.7970 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10765.7 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmeas_19 | xmeas_37 -> xmeas_19 | 0.4909 | 0.6161 | 0.3311 | 0.0000 | 0.0177 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3081 | 0.7514 | 0.5299 | 0.0000 | 0.1005 | 1.0 |
| xmeas_23 -> xmeas_13 | xmeas_23 -> xmeas_13 | 0.2436 | 0.5295 | 0.3836 | 0.0000 | 0.0620 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2433 | 0.7591 | 0.6751 | 0.0000 | 0.0238 | 1.0 |
| xmeas_10 -> xmeas_19 | xmeas_10 -> xmeas_19 | 0.2164 | 0.4200 | 0.3437 | 0.0000 | 0.0092 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.4111 | 0.7141 | 0.3673 | 0.1553 | 0.0808 | 1.0 |
| xmeas_34 -> xmv_03 | xmeas_34 -> xmv_03 | 0.3185 | 0.5355 | 0.3714 | 0.0000 | 0.0402 | 1.0 |
| xmeas_35 -> xmv_10 | xmeas_35 -> xmv_10 | 0.2643 | 0.6907 | 0.5080 | 0.0000 | 0.0259 | 1.0 |
| xmeas_41 -> xmeas_01 | xmeas_41 -> xmeas_01 | 0.2486 | 0.7401 | 0.4908 | 0.0000 | 0.0619 | 1.0 |
| xmeas_21 -> xmv_10 | xmeas_21 -> xmv_10 | 0.2474 | 0.7391 | 0.4445 | 0.0000 | 0.0502 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_01 -> xmv_10 | xmeas_01 -> xmv_10 | 0.3435 | 0.5944 | 0.7748 | 0.0000 | 0.0218 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3415 | 0.6059 | 0.2981 | 0.1485 | 0.0708 | 1.0 |
| xmeas_26 -> xmeas_18 | xmeas_26 -> xmeas_18 | 0.3094 | 0.5494 | 0.4862 | 0.0000 | 0.3228 | 1.0 |
| xmeas_09 -> xmeas_23 | xmeas_09 -> xmeas_23 | 0.2369 | 0.7710 | 0.5946 | 0.0000 | 0.0514 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2364 | 0.6010 | 0.2267 | 0.2404 | 0.1318 | 1.0 |

