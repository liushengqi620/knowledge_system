# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_universe-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+path-aux@0.05 | 3 | 0.6240 +/- 0.0076 | 0.6352 +/- 0.0061 | 0.0175 | 0.0175 | 0.2004 | 0.0000 | 0.7734 | 0.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11559.6 | 160569 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_08 -> xmv_11 | xmv_08 -> xmv_11 | 0.7025 | 0.7160 | 0.3516 | 0.0000 | 0.0000 | 1.0 |
| xmeas_04 -> xmv_11 | xmeas_04 -> xmv_11 | 0.4567 | 0.5297 | 0.3081 | 0.0000 | 0.0000 | 1.0 |
| xmeas_17 -> xmv_11 | xmeas_17 -> xmv_11 | 0.4004 | 0.5147 | 0.1175 | 0.8240 | 0.0000 | 1.0 |
| xmv_09 -> xmv_11 | xmv_09 -> xmv_11 | 0.3384 | 0.4305 | 0.3284 | 0.0000 | 0.0000 | 1.0 |
| xmeas_40 -> xmv_11 | xmeas_40 -> xmv_11 | 0.2969 | 0.6538 | 0.2847 | 0.0000 | 0.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmeas_18 | xmeas_30 -> xmeas_18 | 0.4390 | 0.8180 | 0.3183 | 0.0000 | 0.0000 | 1.0 |
| xmeas_28 -> xmeas_35 | xmeas_28 -> xmeas_35 | 0.3171 | 0.7934 | 0.4154 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.2786 | 0.7235 | 0.2087 | 0.8736 | 0.0000 | 1.0 |
| xmv_04 -> xmv_05 | xmv_04 -> xmv_05 | 0.2599 | 0.5856 | 0.5018 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmv_01 | xmv_10 -> xmv_01 | 0.2597 | 0.7716 | 0.5594 | 0.0000 | 0.0000 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_39 | xmv_10 -> xmeas_39 | 0.6066 | 0.8070 | 0.3201 | 0.0000 | 0.0000 | 1.0 |
| xmeas_23 -> xmv_10 | xmeas_23 -> xmv_10 | 0.4543 | 0.9231 | 0.1705 | 0.7974 | 0.0000 | 1.0 |
| xmeas_19 -> xmv_10 | xmeas_19 -> xmv_10 | 0.3527 | 0.8901 | 0.3203 | 0.0000 | 0.0000 | 1.0 |
| xmv_10 -> xmeas_29 | xmv_10 -> xmeas_29 | 0.3395 | 0.8343 | 0.1753 | 0.7492 | 0.0000 | 1.0 |
| xmv_10 -> xmv_06 | xmv_10 -> xmv_06 | 0.3343 | 0.8224 | 0.1488 | 0.7919 | 0.0000 | 1.0 |

