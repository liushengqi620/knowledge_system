# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-hybrid-k8-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6115 +/- 0.0119 | 0.6213 +/- 0.0105 | 0.0000 | 0.0000 | 0.2667 | 0.3202 | 0.7467 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9597.2 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_11 -> xmv_06 | xmv_11 -> xmv_06 | 0.4636 | 0.9138 | 0.2979 | 0.0000 | 0.6525 | 1.0 |
| xmv_11 -> xmeas_11 | xmv_11 -> xmeas_11 | 0.2993 | 0.8507 | 0.3050 | 0.0000 | 0.7416 | 1.0 |
| xmv_11 -> xmeas_21 | xmv_11 -> xmeas_21 | 0.2845 | 0.8713 | 0.3436 | 0.0000 | 0.5251 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.2691 | 0.7546 | 0.3699 | 0.0000 | 0.3643 | 1.0 |
| xmeas_38 -> xmeas_11 | xmeas_38 -> xmeas_11 | 0.2105 | 0.7885 | 0.2988 | 0.0000 | 0.6772 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_01 -> xmv_04 | xmeas_01 -> xmv_04 | 0.6844 | 0.8418 | 0.3177 | 0.0000 | 0.6080 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.6808 | 0.7298 | 0.3003 | 0.6175 | 0.4920 | 1.0 |
| xmeas_19 -> xmv_11 | xmeas_19 -> xmv_11 | 0.4586 | 0.6707 | 0.3303 | 0.0000 | 0.3175 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.4211 | 0.8017 | 0.1357 | 0.7514 | 0.7794 | 1.0 |
| xmv_11 -> xmv_05 | xmv_11 -> xmv_05 | 0.3978 | 0.6213 | 0.1044 | 0.7921 | 0.8480 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_04 -> xmv_11 | xmeas_04 -> xmv_11 | 0.5425 | 0.8455 | 0.2366 | 0.0000 | 0.6019 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.4762 | 0.7106 | 0.2978 | 0.0000 | 0.2820 | 1.0 |
| xmeas_02 -> xmv_05 | xmeas_02 -> xmv_05 | 0.3946 | 0.5781 | 0.2934 | 0.0000 | 0.6976 | 1.0 |
| xmv_01 -> xmv_05 | xmv_01 -> xmv_05 | 0.3535 | 0.8374 | 0.1543 | 0.6681 | 0.8836 | 1.0 |
| xmeas_33 -> xmv_05 | xmeas_33 -> xmv_05 | 0.3220 | 0.8049 | 0.2535 | 0.0000 | 0.7783 | 1.0 |

