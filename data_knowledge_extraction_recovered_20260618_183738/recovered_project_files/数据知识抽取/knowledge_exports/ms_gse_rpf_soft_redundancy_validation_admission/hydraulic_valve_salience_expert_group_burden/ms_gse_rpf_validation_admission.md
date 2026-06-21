# MS-GSE + RPF Validation Admission

- dataset: hydraulic
- target: valve
- selection metric: validation macro_f1
- min validation gain: 0.0000
- candidate penalties: {'expert_prior0': 0.01, 'expert_group_prior0': 0.02}

| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.7641 +/- 0.0350 | 0.7738 +/- 0.0335 | n/a | 0.5381 +/- 0.3816 | 295.7 |

## Seed Decisions

| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |
|---:|---|---:|---:|---:|---|
| 42 | salience_s005 | 0.8161 | 0.8085 | 0.8181 | baseline=0.6993, expert_group_prior0=0.6814->adj0.6614, expert_prior0=0.6902->adj0.6802, salience_s005=0.8161 |
| 43 | salience_s005 | 0.8001 | 0.7611 | 0.7661 | baseline=0.7458, expert_group_prior0=0.6794->adj0.6594, expert_prior0=0.6507->adj0.6407, salience_s005=0.8001 |
| 44 | expert_prior0 | 0.7225 | 0.7228 | 0.7372 | baseline=0.6738, expert_group_prior0=0.6595->adj0.6395, expert_prior0=0.7225->adj0.7125, salience_s005=0.6486 |
