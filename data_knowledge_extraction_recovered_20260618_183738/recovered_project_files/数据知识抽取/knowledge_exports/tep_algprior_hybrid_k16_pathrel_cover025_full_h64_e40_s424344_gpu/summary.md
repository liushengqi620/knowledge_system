# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-rel-cal+prior-cover@0.25+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6220 +/- 0.0102 | 0.6424 +/- 0.0067 | 0.0175 | 0.0175 | 0.3034 | 0.3338 | 0.7475 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 18828.4 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_41 -> xmv_09 | xmeas_41 -> xmv_09 | 0.3173 | 0.8546 | 0.3960 | 0.0000 | 0.2526 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3016 | 0.9360 | 0.2221 | 0.8651 | 0.6391 | 1.0 |
| xmv_11 -> xmeas_01 | xmv_11 -> xmeas_01 | 0.2803 | 0.7886 | 0.7055 | 0.0000 | 0.5409 | 1.0 |
| xmv_11 -> xmeas_18 | xmv_11 -> xmeas_18 | 0.2789 | 0.6014 | 0.4159 | 0.0000 | 0.2478 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2708 | 0.8804 | 0.7196 | 0.0000 | 0.1300 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_25 -> xmv_04 | xmeas_25 -> xmv_04 | 0.5597 | 0.9903 | 0.1622 | 0.6384 | 0.8554 | 1.0 |
| xmeas_18 -> xmv_04 | xmeas_18 -> xmv_04 | 0.5291 | 0.8686 | 0.4822 | 0.0000 | 0.7401 | 1.0 |
| xmv_11 -> xmv_04 | xmv_11 -> xmv_04 | 0.3770 | 0.9358 | 0.2034 | 0.6623 | 0.7562 | 1.0 |
| xmeas_30 -> xmv_03 | xmeas_30 -> xmv_03 | 0.3763 | 0.9168 | 0.6802 | 0.0000 | 0.6629 | 1.0 |
| xmeas_24 -> xmeas_20 | xmeas_24 -> xmeas_20 | 0.3707 | 0.7514 | 0.6169 | 0.0000 | 0.8004 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmeas_05 | xmeas_14 -> xmeas_05 | 0.3761 | 0.9585 | 0.4503 | 0.2793 | 0.4340 | 1.0 |
| xmv_05 -> xmeas_13 | xmv_05 -> xmeas_13 | 0.2429 | 0.6995 | 0.1104 | 0.6853 | 0.9614 | 1.0 |
| xmv_08 -> xmeas_28 | xmv_08 -> xmeas_28 | 0.2296 | 0.3710 | 0.4555 | 0.0000 | 0.0001 | 1.0 |
| xmeas_13 -> xmv_05 | xmeas_13 -> xmv_05 | 0.2229 | 0.5660 | 0.2204 | 0.6950 | 0.7889 | 1.0 |
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.2131 | 0.9168 | 0.5387 | 0.8202 | 0.2987 | 1.0 |

