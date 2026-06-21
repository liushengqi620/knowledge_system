# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6155 +/- 0.0055 | 0.6229 +/- 0.0088 | 0.0175 | 0.0175 | 0.3290 | 0.3282 | 0.7304 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9815.1 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.4294 | 0.7807 | 0.4442 | 0.7579 | 0.3065 | 1.0 |
| xmeas_16 -> xmv_11 | xmeas_16 -> xmv_11 | 0.3647 | 0.7563 | 0.1579 | 0.8002 | 0.5807 | 1.0 |
| xmv_09 -> xmv_11 | xmv_09 -> xmv_11 | 0.3324 | 0.7789 | 0.3612 | 0.0000 | 0.5920 | 1.0 |
| xmeas_26 -> xmv_11 | xmeas_26 -> xmv_11 | 0.3173 | 0.7577 | 0.3578 | 0.0000 | 0.4838 | 1.0 |
| xmeas_07 -> xmv_11 | xmeas_07 -> xmv_11 | 0.3140 | 0.6870 | 0.1671 | 0.7519 | 0.6231 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.5780 | 0.8357 | 0.2816 | 0.6175 | 0.5496 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.4645 | 0.8362 | 0.2334 | 0.7514 | 0.7193 | 1.0 |
| xmeas_36 -> xmv_04 | xmeas_36 -> xmv_04 | 0.4216 | 0.8298 | 0.2289 | 0.6419 | 0.6581 | 1.0 |
| xmeas_19 -> xmv_11 | xmeas_19 -> xmv_11 | 0.3925 | 0.7016 | 0.2588 | 0.6587 | 0.3992 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.2553 | 0.5973 | 0.3179 | 0.0000 | 0.3638 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.3361 | 0.6286 | 0.1793 | 0.7678 | 0.3973 | 1.0 |
| xmeas_19 -> xmv_11 | xmeas_19 -> xmv_11 | 0.3008 | 0.7077 | 0.1796 | 0.6566 | 0.9690 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.2674 | 0.6675 | 0.3324 | 0.0000 | 0.2956 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.2363 | 0.5567 | 0.2745 | 0.0000 | 0.1773 | 1.0 |
| xmeas_29 -> xmv_11 | xmeas_29 -> xmv_11 | 0.2318 | 0.7820 | 0.1417 | 0.7713 | 0.6930 | 1.0 |

