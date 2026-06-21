# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-edge_bank-k16-lag3-vote2-sv0.45-vb0.15@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6177 +/- 0.0045 | 0.6425 +/- 0.0030 | 0.0000 | 0.0000 | 0.2592 | 0.3478 | 0.7684 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 21451.3 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3409 | 0.7008 | 0.4116 | 0.8041 | 0.5979 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2918 | 0.9584 | 0.5084 | 0.6669 | 0.8529 | 1.0 |
| xmeas_39 -> xmeas_26 | xmeas_39 -> xmeas_26 | 0.2332 | 0.3385 | 0.3911 | 0.2211 | 0.0099 | 1.0 |
| xmv_03 -> xmv_11 | xmv_03 -> xmv_11 | 0.2217 | 0.6826 | 0.5608 | 0.0000 | 0.1328 | 1.0 |
| xmeas_10 -> xmeas_03 | xmeas_10 -> xmeas_03 | 0.2121 | 0.8173 | 0.7458 | 0.4098 | 0.8417 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3666 | 0.7729 | 0.4415 | 0.7794 | 0.6821 | 1.0 |
| xmeas_10 -> xmeas_01 | xmeas_10 -> xmeas_01 | 0.3367 | 0.7619 | 0.4614 | 0.2938 | 0.9677 | 1.0 |
| xmeas_19 -> xmv_03 | xmeas_19 -> xmv_03 | 0.3035 | 0.8577 | 0.2612 | 0.4578 | 0.6484 | 1.0 |
| xmv_08 -> xmv_03 | xmv_08 -> xmv_03 | 0.2841 | 0.7739 | 0.4768 | 0.0000 | 0.6472 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.2678 | 0.7359 | 0.3562 | 0.2698 | 0.8947 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmv_05 | xmeas_30 -> xmv_05 | 0.3161 | 0.5614 | 0.5362 | 0.0000 | 0.9997 | 1.0 |
| xmv_10 -> xmeas_23 | xmv_10 -> xmeas_23 | 0.2337 | 0.7158 | 0.2471 | 0.6852 | 0.6544 | 1.0 |
| xmeas_18 -> xmeas_22 | xmeas_18 -> xmeas_22 | 0.2269 | 0.6091 | 0.3365 | 0.2407 | 0.3190 | 1.0 |
| xmeas_13 -> xmv_05 | xmeas_13 -> xmv_05 | 0.2244 | 0.4975 | 0.1715 | 0.6376 | 0.9724 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.2224 | 0.7596 | 0.2866 | 0.6429 | 0.5970 | 1.0 |

