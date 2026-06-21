# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+path-rel-cal+prior-cover@0.25+alg-prior-hybrid-k8-lag3@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.0776 +/- 0.0000 | 0.1142 +/- 0.0000 | n/a | n/a | 0.2924 | 0.2274 | 0.1875 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 18912.1 | 59697 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_14 -> xmeas_10 | xmeas_14 -> xmeas_10 | 0.2004 | 0.5039 | 0.1711 | 0.0000 | 0.0361 | 1.0 |
| xmeas_36 -> xmeas_12 | xmeas_36 -> xmeas_12 | 0.1872 | 0.5138 | 0.2003 | 0.0000 | 0.1388 | 1.0 |
| xmeas_13 -> xmv_07 | xmeas_13 -> xmv_07 | 0.1827 | 0.4783 | 0.1842 | 0.0000 | 0.3341 | 1.0 |
| xmeas_32 -> xmv_05 | xmeas_32 -> xmv_05 | 0.1825 | 0.5288 | 0.1666 | 0.0000 | 0.2845 | 1.0 |
| xmeas_15 -> xmeas_24 | xmeas_15 -> xmeas_24 | 0.1753 | 0.4700 | 0.1697 | 0.0000 | 0.0851 | 1.0 |

