# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full_admitted | none | group_pair_inclusive+dedup-hard+class-evidence@8+path-aux@0.05+router@0.05 | 2 | 0.6320 +/- 0.0106 | 0.6499 +/- 0.0097 | 0.0000 | 0.0000 | 0.0000 | 0.2968 | 0.7156 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11485.7 | 149322 |
| tep | event_quality_class_id | full_admitted | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6367 +/- 0.0000 | 0.6506 +/- 0.0000 | n/a | n/a | 0.3127 | 0.3137 | 0.8216 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11090.0 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full_admitted / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_03 | xmv_10 -> xmv_03 | 0.3521 | 0.8174 | 0.4908 | 0.6606 | 0.2540 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.3449 | 0.8323 | 0.3649 | 0.0000 | 0.8147 | 1.0 |
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.2874 | 0.6837 | 0.4320 | 0.0000 | 0.2673 | 1.0 |
| xmeas_38 -> xmeas_19 | xmeas_38 -> xmeas_19 | 0.2632 | 0.7282 | 0.3093 | 0.0000 | 0.0485 | 1.0 |
| xmeas_35 -> xmv_11 | xmeas_35 -> xmv_11 | 0.2576 | 0.6454 | 0.1443 | 0.7618 | 0.7559 | 1.0 |

### tep / event_quality_class_id / full_admitted / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_25 -> xmv_04 | xmeas_25 -> xmv_04 | 0.4732 | 0.6912 | 0.3321 | 0.0000 | 0.7974 | 1.0 |
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.4070 | 0.7839 | 0.2801 | 0.0000 | 0.7471 | 1.0 |
| xmeas_21 -> xmv_10 | xmeas_21 -> xmv_10 | 0.4051 | 0.6778 | 0.5468 | 0.0000 | 0.1345 | 1.0 |
| xmeas_30 -> xmv_04 | xmeas_30 -> xmv_04 | 0.3975 | 0.7868 | 0.3058 | 0.0000 | 0.7207 | 1.0 |
| xmeas_11 -> xmv_05 | xmeas_11 -> xmv_05 | 0.3531 | 0.5342 | 0.2577 | 0.0000 | 0.4702 | 1.0 |

### tep / event_quality_class_id / full_admitted / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_08 -> xmv_05 | xmeas_08 -> xmv_05 | 0.2832 | 0.7899 | 0.2687 | 0.0000 | 0.9769 | 1.0 |
| xmeas_21 -> xmv_05 | xmeas_21 -> xmv_05 | 0.2776 | 0.7602 | 0.3936 | 0.0000 | 0.7811 | 1.0 |
| xmv_03 -> xmeas_09 | xmv_03 -> xmeas_09 | 0.2740 | 0.7080 | 0.2750 | 0.0000 | 0.5632 | 1.0 |
| xmeas_28 -> xmeas_09 | xmeas_28 -> xmeas_09 | 0.2413 | 0.7152 | 0.3428 | 0.0000 | 0.4199 | 1.0 |
| xmeas_39 -> xmv_10 | xmeas_39 -> xmv_10 | 0.2394 | 0.8051 | 0.3072 | 0.0000 | 0.3335 | 1.0 |

