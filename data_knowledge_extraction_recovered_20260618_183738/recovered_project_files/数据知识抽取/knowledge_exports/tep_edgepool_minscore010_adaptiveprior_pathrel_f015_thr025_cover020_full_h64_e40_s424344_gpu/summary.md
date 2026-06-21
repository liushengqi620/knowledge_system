# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.15-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40-min0.10@0.05+class-evidence@8+path-aux@0.05 | 3 | 0.6291 +/- 0.0035 | 0.6408 +/- 0.0103 | 0.0000 | 0.0000 | 0.0956 | 0.2450 | 0.7902 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 9986.9 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.4295 | 0.7012 | 0.1001 | 0.4503 | 0.3315 | 1.0 |
| xmv_10 -> xmeas_25 | xmv_10 -> xmeas_25 | 0.3878 | 0.6007 | 0.4466 | 0.0000 | 0.2860 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3557 | 0.6948 | 0.3798 | 0.2057 | 0.4484 | 1.0 |
| xmeas_19 -> xmv_09 | xmeas_19 -> xmv_09 | 0.3345 | 0.6615 | 0.2215 | 0.4808 | 0.2006 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3234 | 0.8877 | 0.0828 | 0.4480 | 0.7049 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmv_10 | xmv_05 -> xmv_10 | 0.3849 | 0.6444 | 0.2084 | 0.5396 | 0.5785 | 1.0 |
| xmeas_35 -> xmeas_09 | xmeas_35 -> xmeas_09 | 0.3517 | 0.4786 | 0.3173 | 0.0000 | 0.2613 | 1.0 |
| xmeas_22 -> xmv_01 | xmeas_22 -> xmv_01 | 0.2370 | 0.5636 | 0.4624 | 0.0000 | 0.2873 | 1.0 |
| xmeas_30 -> xmeas_03 | xmeas_30 -> xmeas_03 | 0.2073 | 0.4758 | 0.3929 | 0.0000 | 0.0752 | 1.0 |
| xmeas_24 -> xmeas_01 | xmeas_24 -> xmeas_01 | 0.2038 | 0.6225 | 0.4326 | 0.0000 | 0.2220 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_33 -> xmeas_09 | xmeas_33 -> xmeas_09 | 0.5501 | 0.7846 | 0.4425 | 0.0000 | 0.0214 | 1.0 |
| xmv_10 -> xmeas_28 | xmv_10 -> xmeas_28 | 0.4185 | 0.5570 | 0.3806 | 0.0000 | 0.6271 | 1.0 |
| xmv_10 -> xmeas_30 | xmv_10 -> xmeas_30 | 0.3231 | 0.6279 | 0.3916 | 0.0000 | 0.0329 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.3006 | 0.8011 | 0.3871 | 0.0000 | 0.0776 | 1.0 |
| xmv_10 -> xmeas_24 | xmv_10 -> xmeas_24 | 0.2956 | 0.5518 | 0.3640 | 0.0000 | 0.0259 | 1.0 |

