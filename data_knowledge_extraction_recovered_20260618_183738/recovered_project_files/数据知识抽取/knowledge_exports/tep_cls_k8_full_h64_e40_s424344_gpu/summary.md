# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6252 +/- 0.0129 | 0.6438 +/- 0.0118 | 0.0000 | 0.0000 | 0.0000 | 0.2944 | 0.7696 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11367.1 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_25 -> xmv_11 | xmeas_25 -> xmv_11 | 0.5899 | 0.7710 | 0.3195 | 0.0000 | 0.6779 | 1.0 |
| xmeas_36 -> xmv_11 | xmeas_36 -> xmv_11 | 0.4733 | 0.7328 | 0.2825 | 0.0000 | 0.6676 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.4650 | 0.6959 | 0.3038 | 0.0000 | 0.4321 | 1.0 |
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.4640 | 0.7516 | 0.2977 | 0.0000 | 0.8265 | 1.0 |
| xmeas_38 -> xmv_11 | xmeas_38 -> xmv_11 | 0.4267 | 0.8076 | 0.2865 | 0.0000 | 0.7667 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_25 -> xmv_04 | xmeas_25 -> xmv_04 | 0.4732 | 0.6912 | 0.3321 | 0.0000 | 0.7974 | 1.0 |
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.4070 | 0.7839 | 0.2801 | 0.0000 | 0.7471 | 1.0 |
| xmeas_21 -> xmv_10 | xmeas_21 -> xmv_10 | 0.4051 | 0.6778 | 0.5468 | 0.0000 | 0.1345 | 1.0 |
| xmeas_30 -> xmv_04 | xmeas_30 -> xmv_04 | 0.3975 | 0.7868 | 0.3058 | 0.0000 | 0.7207 | 1.0 |
| xmeas_11 -> xmv_05 | xmeas_11 -> xmv_05 | 0.3531 | 0.5342 | 0.2577 | 0.0000 | 0.4702 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_08 -> xmv_05 | xmeas_08 -> xmv_05 | 0.2832 | 0.7899 | 0.2687 | 0.0000 | 0.9769 | 1.0 |
| xmeas_21 -> xmv_05 | xmeas_21 -> xmv_05 | 0.2776 | 0.7602 | 0.3936 | 0.0000 | 0.7811 | 1.0 |
| xmv_03 -> xmeas_09 | xmv_03 -> xmeas_09 | 0.2740 | 0.7080 | 0.2750 | 0.0000 | 0.5632 | 1.0 |
| xmeas_28 -> xmeas_09 | xmeas_28 -> xmeas_09 | 0.2413 | 0.7152 | 0.3428 | 0.0000 | 0.4199 | 1.0 |
| xmeas_39 -> xmv_10 | xmeas_39 -> xmv_10 | 0.2394 | 0.8051 | 0.3072 | 0.0000 | 0.3335 | 1.0 |

