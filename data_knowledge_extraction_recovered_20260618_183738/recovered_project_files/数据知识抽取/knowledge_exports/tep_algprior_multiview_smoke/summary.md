# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | prior-cover@0.25+alg-prior-multiview-k16-g4-lag3@0.05+class-evidence@8 | 1 | 0.0266 +/- 0.0000 | 0.0617 +/- 0.0000 | n/a | n/a | 0.2508 | 0.2011 | 0.2239 | 1.0000 | 0.0077 | 0.00 | 0.00 | 0.00 | 0.0000 | on | 10026.3 | 23562 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_06 -> xmeas_24 | xmv_06 -> xmeas_24 | 0.1257 | 0.5837 | 0.1494 | 0.0000 | 0.2129 | 1.0 |
| xmeas_07 -> xmv_05 | xmeas_07 -> xmv_05 | 0.1223 | 0.5643 | 0.1570 | 0.0000 | 0.2878 | 1.0 |
| xmeas_02 -> xmv_05 | xmeas_02 -> xmv_05 | 0.1204 | 0.5817 | 0.1614 | 0.0000 | 0.1363 | 1.0 |
| xmeas_17 -> xmeas_32 | xmeas_17 -> xmeas_32 | 0.1164 | 0.5657 | 0.1536 | 0.0000 | 0.0558 | 1.0 |
| xmeas_23 -> xmv_04 | xmeas_23 -> xmv_04 | 0.1050 | 0.6209 | 0.1603 | 0.0000 | 0.1247 | 1.0 |

