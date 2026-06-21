# Traceability Expert Audit Protocol

## Purpose

This protocol turns the paper-demo traceability output into an expert-reviewed benchmark subset. The current weak labels are useful for engineering iteration, but paper-level claims require human review of root-cause correctness, trace-path plausibility, and action usefulness.

## Files

- Source template: `outputs/paper_demo_traceability/expert_audit_template.csv`
- Blinded review file: `outputs/traceability_paper_evidence_pack/expert_audit_blind.csv`
- Admin key file: `outputs/traceability_paper_evidence_pack/expert_audit_key.csv`
- Scoring report: `outputs/traceability_paper_evidence_pack/expert_audit_scoring_report.md`

Reviewers should fill the blinded file. The admin key should not be shown during review unless the study intentionally uses a non-blind setup.

## Review Fields

Use the following scores:

- `1`: correct, plausible, or useful.
- `0.5`: partially correct, plausible with reservations, or useful only under additional constraints.
- `0`: incorrect, implausible, or not useful.
- blank: not reviewable from the provided information.

Fields:

- `expert_root_cause_correct`: whether the predicted root-cause category is acceptable for the case evidence.
- `expert_path_plausible`: whether the KG trace path is mechanistically reasonable.
- `expert_action_useful`: whether the implied traceability direction would support a useful engineering action.
- `expert_notes`: short reason for rejection or reservation.

## Recommended Review Design

Use at least two independent reviewers for the first paper-grade subset. Recommended minimum sample:

- 20 to 30 cases from `full_weak_label_masked_text`.
- 20 to 30 cases from `balanced_label_masked_text`.
- 20 to 30 cases from `balanced_group_only`.
- Include a smaller stress subset from `balanced_feature_anonymized` to demonstrate the expected failure mode.

When multiple reviewers score the same case, duplicate the case row and add a `reviewer_id` column. The scoring script will compute pairwise agreement when duplicate case IDs are present.

## Metrics For The Paper

Primary human-evaluation metrics:

- Root-cause usable acceptance rate.
- Trace-path usable acceptance rate.
- Action usefulness rate.
- Complete-case usable acceptance rate.
- Pairwise reviewer agreement.

Secondary automatic metrics:

- Hit@1, Hit@3, MRR, and Macro F1 on weak labels.
- Explanation coverage.
- Path-quality proxy.
- Faithful path rate.

The paper should treat the automatic metrics as reproducible demo evidence and the expert-audit metrics as the main validity evidence.

## Commands

Build the evidence pack:

```powershell
python experiments/build_traceability_paper_evidence_pack.py --demo-dir outputs/paper_demo_traceability --output-dir outputs/traceability_paper_evidence_pack
```

After experts fill the blinded CSV, rerun the same command to refresh the scoring report and paper tables.
