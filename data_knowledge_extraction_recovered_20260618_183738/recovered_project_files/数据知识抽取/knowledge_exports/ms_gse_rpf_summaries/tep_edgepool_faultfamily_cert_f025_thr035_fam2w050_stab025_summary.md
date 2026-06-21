# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off-k8-edge4+path-family-cert-focus_fault_family-f0.25-thr0.35-t0.05-d0.75-g0.35-stab0.25-fam2@0.50+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@1.00@8+path-aux@0.05+router@0.05 | 3 | 0.6284 +/- 0.0082 | 0.6406 +/- 0.0095 | 0.0000 | 0.0000 | 0.0832 | 0.3445 | 0.8083 | 1.0000 | 0.3596 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7258.7 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2269 | 0.8923 | 0.3599 | 0.6489 | 0.7540 | 1.0 |
| xmeas_34 -> xmeas_10 | xmeas_34 -> xmeas_10 | 0.2266 | 0.8656 | 0.0382 | 0.4238 | 0.7518 | 1.0 |
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2223 | 0.8189 | 0.7954 | 0.0000 | 0.1572 | 1.0 |
| xmeas_38 -> xmeas_19 | xmeas_38 -> xmeas_19 | 0.2184 | 0.2723 | 0.5545 | 0.0000 | 0.0738 | 1.0 |
| xmeas_30 -> xmeas_18 | xmeas_30 -> xmeas_18 | 0.2045 | 0.3069 | 0.4573 | 0.0000 | 0.0249 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.4819 | 0.7958 | 0.1134 | 0.4880 | 0.6198 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.2955 | 0.7736 | 0.7616 | 0.0000 | 0.7187 | 1.0 |
| xmeas_29 -> xmv_03 | xmeas_29 -> xmv_03 | 0.1940 | 0.6355 | 0.0444 | 0.4561 | 0.6520 | 1.0 |
| xmv_05 -> xmv_09 | xmv_05 -> xmv_09 | 0.1918 | 0.4717 | 0.4984 | 0.0000 | 0.7015 | 1.0 |
| xmeas_22 -> xmeas_11 | xmeas_22 -> xmeas_11 | 0.1901 | 0.6148 | 0.6263 | 0.0000 | 0.3568 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.5130 | 0.8562 | 0.1258 | 0.5767 | 0.8346 | 1.0 |
| xmeas_41 -> xmeas_25 | xmeas_41 -> xmeas_25 | 0.3557 | 0.6520 | 0.4191 | 0.0000 | 0.0187 | 1.0 |
| xmeas_11 -> xmeas_13 | xmeas_11 -> xmeas_13 | 0.2435 | 0.7025 | 0.0751 | 0.6384 | 0.7177 | 1.0 |
| xmeas_18 -> xmeas_19 | xmeas_18 -> xmeas_19 | 0.2261 | 0.7295 | 0.3897 | 0.4117 | 0.3565 | 1.0 |
| xmeas_20 -> xmeas_29 | xmeas_20 -> xmeas_29 | 0.2187 | 0.5264 | 0.1059 | 0.5156 | 0.6076 | 1.0 |

