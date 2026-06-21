# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6283 +/- 0.0125 | 0.6487 +/- 0.0080 | 0.0000 | 0.0000 | 0.3078 | 0.3246 | 0.7748 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11060.4 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_03 | xmv_10 -> xmv_03 | 0.3521 | 0.8174 | 0.4908 | 0.6606 | 0.2540 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.3449 | 0.8323 | 0.3649 | 0.0000 | 0.8147 | 1.0 |
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.2874 | 0.6837 | 0.4320 | 0.0000 | 0.2673 | 1.0 |
| xmeas_38 -> xmeas_19 | xmeas_38 -> xmeas_19 | 0.2632 | 0.7282 | 0.3093 | 0.0000 | 0.0485 | 1.0 |
| xmeas_35 -> xmv_11 | xmeas_35 -> xmv_11 | 0.2576 | 0.6454 | 0.1443 | 0.7618 | 0.7559 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_03 -> xmv_04 | xmeas_03 -> xmv_04 | 0.6058 | 0.6925 | 0.3463 | 0.0000 | 0.8837 | 1.0 |
| xmeas_30 -> xmv_04 | xmeas_30 -> xmv_04 | 0.4297 | 0.7643 | 0.3638 | 0.0000 | 0.6594 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.4261 | 0.6486 | 0.3222 | 0.0000 | 0.7735 | 1.0 |
| xmeas_10 -> xmv_11 | xmeas_10 -> xmv_11 | 0.4007 | 0.6600 | 0.3316 | 0.0000 | 0.0194 | 1.0 |
| xmv_09 -> xmv_04 | xmv_09 -> xmv_04 | 0.3745 | 0.7806 | 0.3117 | 0.0000 | 0.5592 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_25 -> xmeas_09 | xmeas_25 -> xmeas_09 | 0.3821 | 0.7866 | 0.3966 | 0.0000 | 0.4762 | 1.0 |
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.2783 | 0.7601 | 0.3030 | 0.8085 | 0.5909 | 1.0 |
| xmeas_28 -> xmeas_09 | xmeas_28 -> xmeas_09 | 0.2104 | 0.6490 | 0.3225 | 0.0000 | 0.4291 | 1.0 |
| xmeas_26 -> xmeas_18 | xmeas_26 -> xmeas_18 | 0.1823 | 0.7234 | 0.3218 | 0.0000 | 0.6188 | 1.0 |
| xmv_01 -> xmv_10 | xmv_01 -> xmv_10 | 0.1778 | 0.7128 | 0.3482 | 0.0000 | 0.3949 | 1.0 |

