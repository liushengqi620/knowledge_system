# TEP Hierarchical Edge Validation Probe

- Protocol: hierarchical_validation_gain_then_safety_then_cf
- Seeds: [42, 43, 44]
- Candidate edges tested: 50
- Probe levels: ['source_family', 'target_group', 'lag_group', 'single_edge']
- Probe rows: 20
- Validation-admitted edges: 0
- Gate order: validation_gain, low_tail_far_mar_safety, cf_guard
- Admission rule: only `single_edge` probes can materialize `validation_admitted_edges`; group probes are screening diagnostics.

## Probe Level Counts

| Level | Measured probes |
|---|---:|
| lag_group | 2 |
| single_edge | 8 |
| source_family | 2 |
| target_group | 8 |

## Top Aggregated Edge Probes

| Probe | Level | Family | Target group | Lag group | Edges | Val gain | Low-tail delta | FAR delta | MAR delta | CF sensitivity | Gate passed | Reject reasons |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| lag2 | lag_group | None | None | lag2 | 46 | 0.0179 | 0.0092 | 0.1333 | -0.0336 | n/a | False | far_increase |
| stripper | target_group | None | stripper | None | 3 | 0.0166 | 0.0752 | -0.1227 | 0.0372 | n/a | False | mar_increase |
| cooling | target_group | None | cooling | None | 4 | 0.0099 | 0.0011 | -0.0667 | 0.0241 | 0.0556 | False | mar_increase |
| compressor | target_group | None | compressor | None | 3 | 0.0080 | 0.0167 | -0.1013 | 0.0262 | 0.0263 | False | mar_increase |
| expert | source_family | expert | None | None | 43 | 0.0027 | 0.0491 | -0.0907 | 0.0275 | n/a | False | mar_increase |
| tep_fault_01_xmeas_04_to_xmeas_06 | single_edge | expert | reactor_feed | lag2 | 1 | 0.0023 | 0.0532 | -0.0427 | 0.0146 | 0.0073 | False | mar_increase |
| tep_fault_02_xmeas_04_to_xmeas_06 | single_edge | expert | reactor_feed | lag2 | 1 | 0.0023 | 0.0532 | -0.0427 | 0.0146 | 0.0073 | False | mar_increase |
| tep_fault_03_xmeas_09_to_xmeas_11 | single_edge | expert | separator | lag2 | 1 | 0.0015 | 0.0701 | -0.1040 | 0.0225 | n/a | False | mar_increase |
| tep_fault_01_xmeas_06_to_xmeas_35 | single_edge | expert | composition | lag2 | 1 | -0.0006 | 0.0579 | 0.0720 | -0.0265 | n/a | False | validation_gain_not_positive |
| llm | source_family | llm | None | None | 7 | -0.0007 | 0.0108 | -0.1520 | 0.0357 | n/a | False | validation_gain_not_positive |
| tep_fault_02_xmeas_06_to_xmeas_36 | single_edge | expert | composition | lag2 | 1 | -0.0024 | 0.0177 | 0.0800 | -0.0168 | n/a | False | validation_gain_not_positive |
| tep_fault_03_xmeas_02_to_xmeas_09 | single_edge | expert | reactor | lag2 | 1 | -0.0029 | 0.0534 | 0.0187 | -0.0016 | n/a | False | validation_gain_not_positive |
| tep_fault_04_xmv_10_to_xmeas_21 | single_edge | expert | cooling | lag2 | 1 | -0.0030 | 0.0227 | -0.1600 | 0.0497 | n/a | False | validation_gain_not_positive |
| separator | target_group | None | separator | None | 9 | -0.0047 | -0.0000 | -0.0213 | -0.0016 | 0.0470 | False | validation_gain_not_positive |
| tep_global | single_edge | expert | feed_flow | lag1 | 1 | -0.0056 | 0.0196 | 0.1520 | -0.0393 | n/a | False | validation_gain_not_positive |
| lag1 | lag_group | None | None | lag1 | 4 | -0.0103 | 0.0084 | -0.1013 | 0.0331 | n/a | False | validation_gain_not_positive |
| reactor | target_group | None | reactor | None | 11 | -0.0169 | -0.0169 | -0.1760 | 0.0651 | n/a | False | validation_gain_not_positive |
| composition | target_group | None | composition | None | 10 | -0.0172 | 0.0030 | -0.2480 | 0.0690 | n/a | False | validation_gain_not_positive |
| feed_flow | target_group | None | feed_flow | None | 3 | -0.0227 | -0.0037 | 0.0693 | -0.0283 | 0.0362 | False | validation_gain_not_positive |
| reactor_feed | target_group | None | reactor_feed | None | 7 | -0.0235 | -0.0003 | 0.0613 | -0.0094 | n/a | False | validation_gain_not_positive |

## Interpretation

This measured probe enforces the fixed order: validation gain first, low-tail/FAR/MAR safety second, and CF only for candidates that pass those guards. A candidate with strong counterfactual sensitivity but negative validation gain or safety harm is rejected before deployment.
