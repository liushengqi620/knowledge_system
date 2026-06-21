# Expert Audit Scoring Report

- Audit file: `outputs\traceability_assistant_precheck\assistant_technical_audit.csv`
- Status: `audit_scored`
- Audit rows: `80`
- Total scored cells: `240`
- Complete scored cases: `80`

## Dimension Scores

| Dimension | Scored Cases | Mean Score | Strict Acceptance | Usable Acceptance | 95% CI |
|---|---:|---:|---:|---:|---:|
| Root-cause correctness | 80 | 1.0000 | 1.0000 | 1.0000 | 0.9542-1.0000 |
| Trace-path plausibility | 80 | 0.2250 | 0.2250 | 0.2250 | 0.1473-0.3279 |
| Action usefulness | 80 | 0.2250 | 0.2250 | 0.2250 | 0.1473-0.3279 |

## Scenario Coverage

| Scenario | Audit Rows | Rows With Any Score | Mean Available Score |
| --- | --- | --- | --- |
| balanced_group_only | 20 | 20 | 0.3333 |
| balanced_label_masked_text | 30 | 30 | 0.3333 |
| full_weak_label_masked_text | 30 | 30 | 0.7333 |

## Inter-Reviewer Agreement

| Dimension | Reviewer Pairs | Pairwise Agreement |
| --- | --- | --- |
| Root-cause correctness | 0 |  |
| Trace-path plausibility | 0 |  |
| Action usefulness | 0 |  |

## Current Interpretation

Expert-score cells are present. Use the dimension scores and complete-case acceptance rates as the human-evaluation evidence in the paper.
