# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+edge-family-router-t0.50-f0.05-b0.50-bal0.050+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6199 +/- 0.0042 | 0.6316 +/- 0.0033 | 0.0351 | 0.0351 | 0.0838 | 0.4113 | 1.0145 | 1.0000 | 0.3057 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 10935.3 | 162644 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_06 -> xmeas_22 | xmv_06 -> xmeas_22 | 0.6360 | 0.3261 | 0.7948 | 0.0000 | 0.3915 | 1.0 |
| xmv_05 -> xmv_01 | xmv_05 -> xmv_01 | 0.3039 | 0.7721 | 0.2117 | 0.4855 | 0.9610 | 1.0 |
| xmeas_22 -> xmv_10 | xmeas_22 -> xmv_10 | 0.3017 | 0.4053 | 0.7462 | 0.0000 | 0.1551 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.2960 | 0.7696 | 0.6792 | 0.4648 | 0.7780 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.2901 | 0.6513 | 0.4427 | 0.4219 | 0.5228 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_37 -> xmeas_01 | xmeas_37 -> xmeas_01 | 0.8225 | 0.7558 | 0.8527 | 0.0000 | 0.9975 | 1.0 |
| xmv_10 -> xmv_03 | xmv_10 -> xmv_03 | 0.5116 | 0.8270 | 0.1193 | 0.4241 | 0.6343 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.3403 | 0.8297 | 0.2474 | 0.4593 | 0.8901 | 1.0 |
| xmeas_23 -> xmv_03 | xmeas_23 -> xmv_03 | 0.3190 | 0.8220 | 0.2176 | 0.4744 | 0.5828 | 1.0 |
| xmeas_18 -> xmeas_22 | xmeas_18 -> xmeas_22 | 0.3015 | 0.6787 | 0.2236 | 0.3799 | 0.7717 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmeas_21 | xmeas_30 -> xmeas_21 | 0.4031 | 0.4376 | 0.7297 | 0.0000 | 0.0017 | 1.0 |
| xmeas_19 -> xmeas_16 | xmeas_19 -> xmeas_16 | 0.3423 | 0.4258 | 0.6040 | 0.0000 | 0.1128 | 1.0 |
| xmeas_30 -> xmeas_41 | xmeas_30 -> xmeas_41 | 0.3412 | 0.5292 | 0.6694 | 0.0000 | 0.0116 | 1.0 |
| xmv_09 -> xmeas_32 | xmv_09 -> xmeas_32 | 0.3225 | 0.5254 | 0.7617 | 0.0000 | 0.5336 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3172 | 0.8053 | 0.6988 | 0.5475 | 0.8760 | 1.0 |

