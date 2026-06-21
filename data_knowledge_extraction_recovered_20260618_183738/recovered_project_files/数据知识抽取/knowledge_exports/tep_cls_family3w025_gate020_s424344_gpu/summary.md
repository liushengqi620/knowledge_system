# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-evidence-family3@0.25-gate@0.20@8+path-aux@0.05+router@0.05 | 3 | 0.6074 +/- 0.0101 | 0.6142 +/- 0.0111 | 0.0000 | 0.0000 | 0.0000 | 0.2651 | 0.7434 | 0.9565 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 8939.9 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.4428 | 0.9043 | 0.2501 | 0.0000 | 0.3270 | 1.0 |
| xmv_10 -> xmeas_38 | xmv_10 -> xmeas_38 | 0.4111 | 0.8701 | 0.2676 | 0.0000 | 0.5724 | 1.0 |
| xmv_11 -> xmeas_06 | xmv_11 -> xmeas_06 | 0.3093 | 0.8520 | 0.4493 | 0.0000 | 0.3049 | 1.0 |
| xmv_10 -> xmeas_41 | xmv_10 -> xmeas_41 | 0.3012 | 0.7465 | 0.2867 | 0.0000 | 0.2516 | 1.0 |
| xmv_11 -> xmeas_41 | xmv_11 -> xmeas_41 | 0.2894 | 0.8087 | 0.2749 | 0.0000 | 0.3299 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmv_04 | xmeas_14 -> xmv_04 | 0.7331 | 0.8662 | 0.3013 | 0.0000 | 0.5361 | 1.0 |
| xmv_02 -> xmv_04 | xmv_02 -> xmv_04 | 0.6740 | 0.7721 | 0.3697 | 0.0000 | 0.3567 | 1.0 |
| xmeas_31 -> xmv_04 | xmeas_31 -> xmv_04 | 0.5545 | 0.8226 | 0.3049 | 0.0000 | 0.4117 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.4987 | 0.6811 | 0.2971 | 0.0000 | 0.3185 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.3955 | 0.7769 | 0.2521 | 0.0000 | 0.5669 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.5479 | 0.7697 | 0.2880 | 0.0000 | 0.3260 | 1.0 |
| xmv_02 -> xmv_10 | xmv_02 -> xmv_10 | 0.4343 | 0.7129 | 0.4128 | 0.0000 | 0.2788 | 1.0 |
| xmv_10 -> xmv_11 | xmv_10 -> xmv_11 | 0.2884 | 0.5858 | 0.3112 | 0.0000 | 0.6154 | 1.0 |
| xmeas_07 -> xmv_09 | xmeas_07 -> xmv_09 | 0.2622 | 0.7479 | 0.2708 | 0.0000 | 0.0960 | 1.0 |
| xmeas_07 -> xmeas_18 | xmeas_07 -> xmeas_18 | 0.2369 | 0.6934 | 0.2971 | 0.0000 | 0.3268 | 1.0 |

