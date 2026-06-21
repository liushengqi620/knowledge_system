# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+alg-prior-edge_bank-k16-lag3-vote2-sv0.45-vb0.15-gb4.0@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6194 +/- 0.0046 | 0.6402 +/- 0.0041 | 0.0000 | 0.0000 | 0.2241 | 0.3367 | 0.7359 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 19018.2 | 149322 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmv_11 | xmeas_14 -> xmv_11 | 0.4632 | 0.8097 | 0.3830 | 0.0000 | 0.8945 | 1.0 |
| xmeas_23 -> xmv_11 | xmeas_23 -> xmv_11 | 0.2636 | 0.8336 | 0.1195 | 0.7144 | 0.6285 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2320 | 0.8610 | 0.6390 | 0.0000 | 0.7573 | 1.0 |
| xmeas_18 -> xmv_11 | xmeas_18 -> xmv_11 | 0.2264 | 0.8543 | 0.5575 | 0.0000 | 0.7888 | 1.0 |
| xmeas_19 -> xmv_11 | xmeas_19 -> xmv_11 | 0.2164 | 0.7957 | 0.4044 | 0.0000 | 0.6911 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_21 -> xmv_03 | xmeas_21 -> xmv_03 | 0.3667 | 0.7013 | 0.7934 | 0.0000 | 0.5538 | 1.0 |
| xmv_05 -> xmv_03 | xmv_05 -> xmv_03 | 0.3600 | 0.7236 | 0.3114 | 0.6519 | 0.5784 | 1.0 |
| xmeas_10 -> xmeas_01 | xmeas_10 -> xmeas_01 | 0.3150 | 0.7298 | 0.6447 | 0.0000 | 0.8982 | 1.0 |
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.2915 | 0.8061 | 0.6628 | 0.0000 | 0.9164 | 1.0 |
| xmeas_21 -> xmeas_01 | xmeas_21 -> xmeas_01 | 0.2749 | 0.7409 | 0.6545 | 0.0000 | 0.8583 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmv_05 | xmeas_30 -> xmv_05 | 0.2924 | 0.4748 | 0.3186 | 0.0000 | 0.9968 | 1.0 |
| xmeas_04 -> xmv_06 | xmeas_04 -> xmv_06 | 0.2240 | 0.5684 | 0.4303 | 0.0000 | 0.0671 | 1.0 |
| xmeas_16 -> xmv_05 | xmeas_16 -> xmv_05 | 0.2132 | 0.4446 | 0.1014 | 0.6981 | 0.8706 | 1.0 |
| xmeas_41 -> xmeas_03 | xmeas_41 -> xmeas_03 | 0.2076 | 0.4317 | 0.4140 | 0.0000 | 0.0002 | 1.0 |
| xmeas_20 -> xmv_06 | xmeas_20 -> xmv_06 | 0.2067 | 0.5185 | 0.4553 | 0.0000 | 0.7228 | 1.0 |

