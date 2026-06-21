# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+alg-prior-hybrid-k8-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6051 +/- 0.0090 | 0.6132 +/- 0.0089 | 0.0000 | 0.0000 | 0.1104 | 0.2898 | 0.7640 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9072.4 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_41 | xmv_10 -> xmeas_41 | 0.3721 | 0.7968 | 0.3040 | 0.0000 | 0.3104 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3643 | 0.8565 | 0.2903 | 0.0000 | 0.6234 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.3579 | 0.7069 | 0.2756 | 0.0000 | 0.9467 | 1.0 |
| xmeas_37 -> xmv_10 | xmeas_37 -> xmv_10 | 0.3434 | 0.7785 | 0.2911 | 0.0000 | 0.5365 | 1.0 |
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.2876 | 0.7743 | 0.2965 | 0.7668 | 0.2959 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.6363 | 0.7580 | 0.3047 | 0.6175 | 0.4180 | 1.0 |
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.5827 | 0.7228 | 0.2370 | 0.0000 | 0.0609 | 1.0 |
| xmeas_13 -> xmv_04 | xmeas_13 -> xmv_04 | 0.5647 | 0.6947 | 0.3026 | 0.0000 | 0.6933 | 1.0 |
| xmeas_16 -> xmv_04 | xmeas_16 -> xmv_04 | 0.5298 | 0.7403 | 0.2592 | 0.0000 | 0.6159 | 1.0 |
| xmeas_16 -> xmv_11 | xmeas_16 -> xmv_11 | 0.5144 | 0.7944 | 0.2459 | 0.0000 | 0.2611 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_33 -> xmv_11 | xmeas_33 -> xmv_11 | 0.6495 | 0.5480 | 0.2522 | 0.0000 | 0.1600 | 1.0 |
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.6123 | 0.9009 | 0.2530 | 0.0000 | 0.9350 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.5306 | 0.7638 | 0.3680 | 0.0000 | 0.3838 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.3905 | 0.8274 | 0.2797 | 0.0000 | 0.4131 | 1.0 |
| xmeas_37 -> xmv_11 | xmeas_37 -> xmv_11 | 0.3524 | 0.8778 | 0.2668 | 0.0000 | 0.9132 | 1.0 |

