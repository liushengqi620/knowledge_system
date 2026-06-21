# TEP Hierarchical Edge Validation Probe

- Protocol: hierarchical_validation_gain_then_safety_then_cf
- Seeds: [42]
- Candidate edges tested: 6
- Probe levels: ['single_edge']
- Probe rows: 6
- Validation-admitted edges: 1
- Gate order: validation_gain, low_tail_far_mar_safety, cf_guard
- Admission rule: only `single_edge` probes can materialize `validation_admitted_edges`; group probes are screening diagnostics.

## Probe Level Counts

| Level | Measured probes |
|---|---:|
| single_edge | 6 |

## Top Aggregated Edge Probes

| Probe | Level | Family | Target group | Lag group | Edges | Val gain | Low-tail delta | FAR delta | MAR delta | CF sensitivity | Gate passed | Reject reasons |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| tep_fault_01_xmeas_06_to_xmeas_35 | single_edge | expert | composition | lag2 | 1 | 0.0461 | 0.0000 | -0.3846 | 0.0244 | n/a | False | mar_increase |
| tep_fault_01_xmeas_04_to_xmeas_06 | single_edge | expert | reactor_feed | lag2 | 1 | 0.0379 | 0.0606 | 0.0769 | 0.0035 | n/a | False | far_increase |
| tep_fault_02_xmeas_04_to_xmeas_06 | single_edge | expert | reactor_feed | lag2 | 1 | 0.0379 | 0.0606 | 0.0769 | 0.0035 | n/a | False | far_increase |
| tep_fault_02_xmeas_06_to_xmeas_36 | single_edge | expert | composition | lag2 | 1 | 0.0305 | 0.0000 | -0.1538 | -0.0035 | 0.0117 | True |  |
| tep_fault_03_xmeas_02_to_xmeas_09 | single_edge | expert | reactor | lag2 | 1 | 0.0222 | 0.0000 | 0.2308 | -0.0557 | n/a | False | far_increase |
| tep_global | single_edge | expert | feed_flow | lag1 | 1 | 0.0219 | 0.0000 | -0.3077 | 0.0244 | n/a | False | mar_increase |

## Interpretation

This measured probe enforces the fixed order: validation gain first, low-tail/FAR/MAR safety second, and CF only for candidates that pass those guards. A candidate with strong counterfactual sensitivity but negative validation gain or safety harm is rejected before deployment.
