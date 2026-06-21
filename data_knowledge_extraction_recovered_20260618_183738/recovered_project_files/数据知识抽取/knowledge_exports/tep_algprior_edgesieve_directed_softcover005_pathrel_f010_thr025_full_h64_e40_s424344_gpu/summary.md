# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | group_pair_inclusive+dedup-hard+class-prior-admit-f0.10-adaptive@0.25t0.05+path-rel-cal-s0.50-reg0.005+prior-cover@0.05+alg-prior-edge_sieve-k20-g4-lag3-vote2-sv0.25-vb0.12-gb5.0-pool3.0-rank0.25@0.03+class-evidence@8+path-aux@0.05+router@0.05 | 3 | 0.6260 +/- 0.0055 | 0.6419 +/- 0.0012 | 0.0351 | 0.0351 | 0.0428 | 0.3194 | 0.8015 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 11434.0 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_16 -> xmv_10 | xmeas_16 -> xmv_10 | 0.4197 | 0.8100 | 0.2930 | 0.0000 | 0.6299 | 1.0 |
| xmv_03 -> xmeas_01 | xmv_03 -> xmeas_01 | 0.3798 | 0.9143 | 0.9561 | 0.5728 | 0.8507 | 1.0 |
| xmeas_09 -> xmeas_21 | xmeas_09 -> xmeas_21 | 0.3003 | 0.7752 | 0.6857 | 0.0000 | 0.7527 | 1.0 |
| xmeas_40 -> xmeas_31 | xmeas_40 -> xmeas_31 | 0.2505 | 0.7965 | 0.3631 | 0.0000 | 0.7005 | 1.0 |
| xmv_05 -> xmeas_07 | xmv_05 -> xmeas_07 | 0.2288 | 0.8495 | 0.3890 | 0.0000 | 0.9325 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.5105 | 0.7230 | 0.4974 | 0.0000 | 0.9637 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.4228 | 0.7386 | 0.2782 | 0.7016 | 0.8396 | 1.0 |
| xmeas_39 -> xmv_03 | xmeas_39 -> xmv_03 | 0.4174 | 0.7194 | 0.4484 | 0.0000 | 0.6280 | 1.0 |
| xmeas_06 -> xmeas_01 | xmeas_06 -> xmeas_01 | 0.3630 | 0.7265 | 0.4601 | 0.0000 | 0.9317 | 1.0 |
| xmeas_39 -> xmv_05 | xmeas_39 -> xmv_05 | 0.3475 | 0.6903 | 0.5431 | 0.0000 | 0.9967 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_01 -> xmv_10 | xmv_01 -> xmv_10 | 0.6002 | 0.6810 | 0.2955 | 0.0000 | 0.1696 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.4459 | 0.6697 | 0.1958 | 0.5598 | 0.6744 | 1.0 |
| xmeas_29 -> xmv_10 | xmeas_29 -> xmv_10 | 0.3900 | 0.6749 | 0.1115 | 0.4671 | 0.6164 | 1.0 |
| xmv_10 -> xmeas_09 | xmv_10 -> xmeas_09 | 0.3146 | 0.8168 | 0.4161 | 0.0000 | 0.6102 | 1.0 |
| xmv_06 -> xmeas_10 | xmv_06 -> xmeas_10 | 0.2521 | 0.6999 | 0.0594 | 0.8339 | 0.8758 | 1.0 |

