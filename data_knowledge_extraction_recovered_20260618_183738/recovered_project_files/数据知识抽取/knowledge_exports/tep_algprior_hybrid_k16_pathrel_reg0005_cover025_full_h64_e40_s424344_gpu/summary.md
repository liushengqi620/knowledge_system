# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-rel-cal-reg0.005+prior-cover@0.25+alg-prior-hybrid-k16-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6205 +/- 0.0028 | 0.6407 +/- 0.0069 | 0.0370 | 0.0370 | 0.2974 | 0.3504 | 0.7354 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 18365.1 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3262 | 0.9003 | 0.2598 | 0.8651 | 0.6656 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2829 | 0.8162 | 0.6912 | 0.0000 | 0.1606 | 1.0 |
| xmeas_14 -> xmeas_21 | xmeas_14 -> xmeas_21 | 0.2659 | 0.9512 | 0.3138 | 0.3160 | 0.4534 | 1.0 |
| xmv_06 -> xmeas_35 | xmv_06 -> xmeas_35 | 0.2430 | 0.8955 | 0.3747 | 0.7227 | 0.0363 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.1909 | 0.9858 | 0.5339 | 0.6934 | 0.8487 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_18 -> xmv_04 | xmeas_18 -> xmv_04 | 0.5845 | 0.8174 | 0.4403 | 0.0000 | 0.6625 | 1.0 |
| xmeas_25 -> xmv_04 | xmeas_25 -> xmv_04 | 0.4534 | 0.9733 | 0.1733 | 0.6384 | 0.7838 | 1.0 |
| xmeas_21 -> xmv_10 | xmeas_21 -> xmv_10 | 0.4523 | 0.9303 | 0.7257 | 0.0000 | 0.9470 | 1.0 |
| xmv_01 -> xmv_04 | xmv_01 -> xmv_04 | 0.4522 | 0.9660 | 0.1568 | 0.8112 | 0.7514 | 1.0 |
| xmv_05 -> xmv_03 | xmv_05 -> xmv_03 | 0.3747 | 0.9393 | 0.3984 | 0.6991 | 0.6164 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_08 -> xmeas_33 | xmeas_08 -> xmeas_33 | 0.3316 | 0.9808 | 0.4929 | 0.0000 | 0.6484 | 1.0 |
| xmeas_25 -> xmeas_18 | xmeas_25 -> xmeas_18 | 0.2675 | 0.6116 | 0.4251 | 0.0000 | 0.3393 | 1.0 |
| xmeas_14 -> xmv_06 | xmeas_14 -> xmv_06 | 0.2139 | 0.0253 | 0.4456 | 0.0000 | 0.0054 | 1.0 |
| xmeas_08 -> xmeas_18 | xmeas_08 -> xmeas_18 | 0.2121 | 0.8454 | 0.2047 | 0.5854 | 0.1708 | 1.0 |
| xmv_10 -> xmeas_37 | xmv_10 -> xmeas_37 | 0.2096 | 0.8845 | 0.5788 | 0.0000 | 0.2010 | 1.0 |

