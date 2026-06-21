# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full_admitted | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 2 | 0.6157 +/- 0.0067 | 0.6235 +/- 0.0107 | 0.0526 | 0.0526 | 0.3259 | 0.3279 | 0.7421 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9795.4 | 56266 |
| tep | event_quality_class_id | full_admitted | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-hybrid-k8-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.6258 +/- 0.0000 | 0.6337 +/- 0.0000 | n/a | n/a | 0.2770 | 0.3279 | 0.7447 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9185.0 | 56266 |

## Top Evidence Paths

### tep / event_quality_class_id / full_admitted / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_11 -> xmv_06 | xmv_11 -> xmv_06 | 0.4636 | 0.9138 | 0.2979 | 0.0000 | 0.6525 | 1.0 |
| xmv_11 -> xmeas_11 | xmv_11 -> xmeas_11 | 0.2993 | 0.8507 | 0.3050 | 0.0000 | 0.7416 | 1.0 |
| xmv_11 -> xmeas_21 | xmv_11 -> xmeas_21 | 0.2845 | 0.8713 | 0.3436 | 0.0000 | 0.5251 | 1.0 |
| xmv_10 -> xmeas_11 | xmv_10 -> xmeas_11 | 0.2691 | 0.7546 | 0.3699 | 0.0000 | 0.3643 | 1.0 |
| xmeas_38 -> xmeas_11 | xmeas_38 -> xmeas_11 | 0.2105 | 0.7885 | 0.2988 | 0.0000 | 0.6772 | 1.0 |

### tep / event_quality_class_id / full_admitted / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_04 | xmeas_19 -> xmv_04 | 0.5780 | 0.8357 | 0.2816 | 0.6175 | 0.5496 | 1.0 |
| xmeas_04 -> xmv_04 | xmeas_04 -> xmv_04 | 0.4645 | 0.8362 | 0.2334 | 0.7514 | 0.7193 | 1.0 |
| xmeas_36 -> xmv_04 | xmeas_36 -> xmv_04 | 0.4216 | 0.8298 | 0.2289 | 0.6419 | 0.6581 | 1.0 |
| xmeas_19 -> xmv_11 | xmeas_19 -> xmv_11 | 0.3925 | 0.7016 | 0.2588 | 0.6587 | 0.3992 | 1.0 |
| xmv_02 -> xmv_11 | xmv_02 -> xmv_11 | 0.2553 | 0.5973 | 0.3179 | 0.0000 | 0.3638 | 1.0 |

### tep / event_quality_class_id / full_admitted / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.3361 | 0.6286 | 0.1793 | 0.7678 | 0.3973 | 1.0 |
| xmeas_19 -> xmv_11 | xmeas_19 -> xmv_11 | 0.3008 | 0.7077 | 0.1796 | 0.6566 | 0.9690 | 1.0 |
| xmeas_27 -> xmv_11 | xmeas_27 -> xmv_11 | 0.2674 | 0.6675 | 0.3324 | 0.0000 | 0.2956 | 1.0 |
| xmeas_28 -> xmv_11 | xmeas_28 -> xmv_11 | 0.2363 | 0.5567 | 0.2745 | 0.0000 | 0.1773 | 1.0 |
| xmeas_29 -> xmv_11 | xmeas_29 -> xmv_11 | 0.2318 | 0.7820 | 0.1417 | 0.7713 | 0.6930 | 1.0 |

