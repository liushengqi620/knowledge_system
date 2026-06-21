# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+prior-cover@0.25+edge-cal-f0.05-b2.0+alg-prior-edge_bank-k8-lag3-vote2-sv0.55-vb0.15-gb4.0@0.05+class-evidence@8+path-aux@0.05+router@0.05 | 1 | 0.0627 +/- 0.0000 | 0.0882 +/- 0.0000 | n/a | n/a | 0.2090 | 0.2426 | 0.1735 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 15653.9 | 57422 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_30 -> xmv_11 | xmeas_30 -> xmv_11 | 0.2108 | 0.5549 | 0.1848 | 0.0000 | 0.1334 | 1.0 |
| xmeas_13 -> xmeas_22 | xmeas_13 -> xmeas_22 | 0.1909 | 0.5306 | 0.1774 | 0.0000 | 0.3444 | 1.0 |
| xmeas_30 -> xmeas_04 | xmeas_30 -> xmeas_04 | 0.1785 | 0.5926 | 0.1718 | 0.0000 | 0.0938 | 1.0 |
| xmv_09 -> xmeas_32 | xmv_09 -> xmeas_32 | 0.1783 | 0.5008 | 0.1657 | 0.0000 | 0.2755 | 1.0 |
| xmeas_36 -> xmeas_18 | xmeas_36 -> xmeas_18 | 0.1716 | 0.5102 | 0.1783 | 0.0000 | 0.2673 | 1.0 |

