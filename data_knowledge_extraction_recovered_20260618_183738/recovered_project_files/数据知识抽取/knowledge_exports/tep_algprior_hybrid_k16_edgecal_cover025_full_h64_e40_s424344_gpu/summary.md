# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+edge-cal-f0.05-b2.0+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6107 +/- 0.0039 | 0.6317 +/- 0.0049 | 0.0000 | 0.0000 | 0.2560 | 0.3409 | 0.7164 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 18591.0 | 153678 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_08 -> xmv_05 | xmeas_08 -> xmv_05 | 0.4088 | 0.7340 | 0.3964 | 0.0000 | 0.9926 | 1.0 |
| xmeas_17 -> xmv_11 | xmeas_17 -> xmv_11 | 0.3463 | 0.8447 | 0.6059 | 0.5330 | 0.5771 | 1.0 |
| xmeas_06 -> xmv_05 | xmeas_06 -> xmv_05 | 0.3165 | 0.7380 | 0.4737 | 0.0000 | 0.9903 | 1.0 |
| xmeas_38 -> xmv_05 | xmeas_38 -> xmv_05 | 0.2536 | 0.7616 | 0.4217 | 0.0000 | 0.9925 | 1.0 |
| xmv_08 -> xmeas_35 | xmv_08 -> xmeas_35 | 0.2377 | 0.7867 | 0.4459 | 0.0000 | 0.3732 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_12 -> xmv_11 | xmeas_12 -> xmv_11 | 0.5383 | 0.5472 | 0.4013 | 0.0000 | 0.4258 | 1.0 |
| xmeas_06 -> xmv_11 | xmeas_06 -> xmv_11 | 0.4992 | 0.6945 | 0.3858 | 0.0000 | 0.2873 | 1.0 |
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.4874 | 0.6358 | 0.4242 | 0.0000 | 0.3276 | 1.0 |
| xmeas_25 -> xmv_11 | xmeas_25 -> xmv_11 | 0.4685 | 0.6605 | 0.1370 | 0.6891 | 0.5946 | 1.0 |
| xmv_11 -> xmv_10 | xmv_11 -> xmv_10 | 0.4198 | 0.7850 | 0.0979 | 0.7559 | 0.8805 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_01 | xmv_10 -> xmeas_01 | 0.2694 | 0.9340 | 0.4615 | 0.0000 | 0.4798 | 1.0 |
| xmv_10 -> xmeas_21 | xmv_10 -> xmeas_21 | 0.2296 | 0.9007 | 0.5029 | 0.0000 | 0.7123 | 1.0 |
| xmv_10 -> xmv_02 | xmv_10 -> xmv_02 | 0.2287 | 0.7634 | 0.4982 | 0.0000 | 0.5292 | 1.0 |
| xmeas_01 -> xmv_03 | xmeas_01 -> xmv_03 | 0.2246 | 0.9523 | 0.3576 | 0.6707 | 0.8517 | 1.0 |
| xmv_01 -> xmv_05 | xmv_01 -> xmv_05 | 0.2092 | 0.7788 | 0.2042 | 0.6320 | 0.8068 | 1.0 |

