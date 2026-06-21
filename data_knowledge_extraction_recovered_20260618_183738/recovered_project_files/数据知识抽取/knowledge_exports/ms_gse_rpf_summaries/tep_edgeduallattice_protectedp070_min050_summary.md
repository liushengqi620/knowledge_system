# MS-GSE + RPF Result Summary

| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| tep | event_quality_class_id | full | none | dedup-exact+salience-class@0.00+class-prior-admit-f0.15-adaptive@0.25t0.05+candidate-prior-admit-f0.00-thr0.70-t0.08-relative_evidence-s0.20-proposal_feature-minsup0.50-pmin0.70+path-rel-cal-s0.50-reg0.005+prior-cover@0.20+candidate-cover@0.08+alg-prior-edge_dual_lattice-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40@0.05+class-evidence-focus-low_train_separation6@8+path-aux@0.05+router@0.05 | 3 | 0.6364 +/- 0.0029 | 0.6478 +/- 0.0035 | 0.0175 | 0.0175 | 0.0437 | 0.7768 | 0.8191 | 1.0000 | 0.0000 | 0.05 | 0.00 | 0.00 | 0.0000 | on | 6007.2 | 162321 |

## Top Evidence Paths

### tep / event_quality_class_id / full / prior=none / seed=42

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_10 -> xmeas_22 | xmv_10 -> xmeas_22 | 0.2878 | 0.5414 | 0.6222 | 0.0000 | 0.7837 | 1.0 |
| xmv_10 -> xmv_05 | xmv_10 -> xmv_05 | 0.2372 | 0.7184 | 0.1508 | 0.2346 | 0.7838 | 1.0 |
| xmeas_37 -> xmeas_19 | xmeas_37 -> xmeas_19 | 0.2353 | 0.8178 | 0.4949 | 0.0000 | 0.8025 | 1.0 |
| xmeas_08 -> xmeas_10 | xmeas_08 -> xmeas_10 | 0.2258 | 0.8190 | 0.5598 | 0.0000 | 1.0000 | 1.0 |
| xmv_10 -> xmeas_31 | xmv_10 -> xmeas_31 | 0.2151 | 0.4874 | 0.4035 | 0.0031 | 0.9035 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=43

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmv_05 -> xmeas_01 | xmv_05 -> xmeas_01 | 0.4808 | 0.5949 | 0.2482 | 0.0195 | 0.8735 | 1.0 |
| xmeas_09 -> xmv_10 | xmeas_09 -> xmv_10 | 0.4640 | 0.6443 | 0.3612 | 0.1610 | 0.8050 | 1.0 |
| xmeas_34 -> xmv_03 | xmeas_34 -> xmv_03 | 0.3585 | 0.6952 | 0.4717 | 0.0000 | 0.9905 | 1.0 |
| xmeas_13 -> xmv_03 | xmeas_13 -> xmv_03 | 0.3025 | 0.6743 | 0.4853 | 0.0000 | 0.9905 | 1.0 |
| xmeas_19 -> xmv_03 | xmeas_19 -> xmv_03 | 0.2934 | 0.6196 | 0.5788 | 0.0000 | 0.9905 | 1.0 |

### tep / event_quality_class_id / full / prior=none / seed=44

| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |
|---|---|---:|---:|---:|---:|---:|---:|
| xmeas_41 -> xmv_05 | xmeas_41 -> xmv_05 | 0.2657 | 0.6662 | 0.5812 | 0.0000 | 0.7850 | 1.0 |
| xmeas_28 -> xmv_09 | xmeas_28 -> xmv_09 | 0.2483 | 0.6392 | 0.3466 | 0.0000 | 0.8877 | 1.0 |
| xmeas_01 -> xmeas_35 | xmeas_01 -> xmeas_35 | 0.1767 | 0.7610 | 0.4346 | 0.0000 | 0.8782 | 1.0 |
| xmeas_08 -> xmv_03 | xmeas_08 -> xmv_03 | 0.1604 | 0.6008 | 0.3574 | 0.0000 | 0.9903 | 1.0 |
| xmv_09 -> xmeas_19 | xmv_09 -> xmeas_19 | 0.1548 | 0.6031 | 0.1355 | 0.2577 | 0.8155 | 1.0 |

