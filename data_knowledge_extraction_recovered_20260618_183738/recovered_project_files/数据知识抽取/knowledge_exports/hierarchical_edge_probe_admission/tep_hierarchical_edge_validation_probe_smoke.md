# TEP Hierarchical Edge Validation Probe

- Protocol: hierarchical_validation_gain_then_safety_then_cf
- Seeds: [42]
- Candidate edges tested: 50
- Probe levels: ['source_family', 'target_group', 'lag_group', 'single_edge']
- Probe rows: 20
- Validation-admitted edges: 1
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
| tep_fault_04_xmv_10_to_xmeas_21 | single_edge | expert | cooling | lag2 | 1 | 0.0941 | 0.1250 | 0.2308 | -0.0523 | n/a | False | far_increase |
| composition | target_group | None | composition | None | 10 | 0.0510 | 0.1053 | 0.0000 | 0.0105 | n/a | False | mar_increase |
| tep_fault_01_xmeas_06_to_xmeas_35 | single_edge | expert | composition | lag2 | 1 | 0.0461 | 0.0000 | -0.3846 | 0.0244 | n/a | False | mar_increase |
| tep_fault_01_xmeas_04_to_xmeas_06 | single_edge | expert | reactor_feed | lag2 | 1 | 0.0379 | 0.0606 | 0.0769 | 0.0035 | n/a | False | far_increase |
| tep_fault_02_xmeas_04_to_xmeas_06 | single_edge | expert | reactor_feed | lag2 | 1 | 0.0379 | 0.0606 | 0.0769 | 0.0035 | n/a | False | far_increase |
| reactor_feed | target_group | None | reactor_feed | None | 7 | 0.0347 | 0.0000 | 0.0769 | -0.0279 | n/a | False | far_increase |
| stripper | target_group | None | stripper | None | 3 | 0.0346 | 0.0800 | 0.2308 | -0.0557 | n/a | False | far_increase |
| expert | source_family | expert | None | None | 43 | 0.0314 | 0.0000 | -0.3077 | 0.0244 | n/a | False | mar_increase |
| tep_fault_02_xmeas_06_to_xmeas_36 | single_edge | expert | composition | lag2 | 1 | 0.0305 | 0.0000 | -0.1538 | -0.0035 | 0.0117 | True |  |
| llm | source_family | llm | None | None | 7 | 0.0284 | 0.0000 | -0.2308 | 0.0488 | n/a | False | mar_increase |
| tep_fault_03_xmeas_09_to_xmeas_11 | single_edge | expert | separator | lag2 | 1 | 0.0229 | 0.0000 | -0.2308 | 0.0557 | n/a | False | mar_increase |
| tep_fault_03_xmeas_02_to_xmeas_09 | single_edge | expert | reactor | lag2 | 1 | 0.0222 | 0.0000 | 0.2308 | -0.0557 | n/a | False | far_increase |
| tep_global | single_edge | expert | feed_flow | lag1 | 1 | 0.0219 | 0.0000 | -0.3077 | 0.0244 | n/a | False | mar_increase |
| lag2 | lag_group | None | None | lag2 | 46 | 0.0208 | 0.0000 | -0.1538 | -0.0035 | 0.0455 | True |  |
| lag1 | lag_group | None | None | lag1 | 4 | 0.0167 | 0.0000 | -0.1538 | 0.0836 | n/a | False | mar_increase |
| feed_flow | target_group | None | feed_flow | None | 3 | 0.0145 | 0.0000 | 0.2308 | -0.0941 | n/a | False | far_increase |
| compressor | target_group | None | compressor | None | 3 | 0.0122 | 0.0000 | 0.0000 | 0.0348 | n/a | False | mar_increase |
| separator | target_group | None | separator | None | 9 | 0.0111 | 0.0000 | -0.3077 | 0.0244 | n/a | False | mar_increase |
| reactor | target_group | None | reactor | None | 11 | 0.0044 | 0.0000 | 0.0000 | 0.0418 | n/a | False | mar_increase |
| cooling | target_group | None | cooling | None | 4 | 0.0008 | 0.0000 | -0.0769 | -0.0383 | 0.0482 | True |  |

## Interpretation

This measured probe enforces the fixed order: validation gain first, low-tail/FAR/MAR safety second, and CF only for candidates that pass those guards. A candidate with strong counterfactual sensitivity but negative validation gain or safety harm is rejected before deployment.
