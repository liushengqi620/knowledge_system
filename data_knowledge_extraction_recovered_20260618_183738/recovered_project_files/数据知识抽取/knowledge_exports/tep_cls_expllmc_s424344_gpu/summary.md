# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | expert_llm@0.00 | group_pair_inclusive+dedup-hard+prior-cover@0.05+prior-cal@0.10+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6040 +/- 0.0119 | 0.6140 +/- 0.0134 | 0.0000 | 0.0000 | 0.0295 | 0.2945 | 0.7698 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 7218.5 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=expert_llm@0.00 / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.4623 | 0.7474 | 0.2890 | 0.0000 | 0.2638 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.2904 | 0.7472 | 0.3027 | 0.0000 | 0.3763 | 1.0 |
| xmv_09 -> xmeas_09 | xmv_09 -> xmeas_09 | 0.2846 | 0.5838 | 0.2287 | 0.0000 | 0.1182 | 1.0 |
| xmv_10 -> xmeas_35 | xmv_10 -> xmeas_35 | 0.2437 | 0.7441 | 0.2707 | 0.0000 | 0.2278 | 1.0 |
| xmeas_18 -> xmv_05 | xmeas_18 -> xmv_05 | 0.2242 | 0.6123 | 0.3198 | 0.0000 | 0.9073 | 1.0 |

### tep / event_quality_class_id / full / prior=expert_llm@0.00 / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_16 -> xmv_04 | xmeas_16 -> xmv_04 | 0.6400 | 0.7651 | 0.2605 | 0.0000 | 0.6252 | 1.0 |
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.4924 | 0.7226 | 0.3012 | 0.0000 | 0.4745 | 1.0 |
| xmeas_24 -> xmv_04 | xmeas_24 -> xmv_04 | 0.4200 | 0.6588 | 0.2642 | 0.0000 | 0.6202 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.3749 | 0.6869 | 0.2957 | 0.0000 | 0.7330 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.3301 | 0.7110 | 0.3945 | 0.0000 | 0.8106 | 1.0 |

### tep / event_quality_class_id / full / prior=expert_llm@0.00 / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.5555 | 0.7814 | 0.3362 | 0.0000 | 0.4120 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.4775 | 0.8187 | 0.3133 | 0.0000 | 0.4847 | 1.0 |
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.4200 | 0.8197 | 0.2761 | 0.0000 | 0.7161 | 1.0 |
| xmeas_33 -> xmv_11 | xmeas_33 -> xmv_11 | 0.3705 | 0.7191 | 0.2849 | 0.0000 | 0.4984 | 1.0 |
| xmeas_03 -> xmeas_18 | xmeas_03 -> xmeas_18 | 0.3456 | 0.7650 | 0.2498 | 0.0000 | 0.0530 | 1.0 |

