# Label Quality and Single-Line Curation

## Problem

The previous v5 event-bag dataset mixed several different sources of label uncertainty into one hard multiclass target. This is risky for KIEP-GL because the model is asked to distinguish defect subtypes even when one event anchor contains multiple target abnormal groups.

The main ambiguity is `quality_abnormal_groups` with more than one target group among:

- `temperature_flux`
- `mold_level_slag_risk`
- `process_fluctuation`
- `speed_stopper_flow`
- `heat_transfer_imbalance`

These samples are valid risk events, but they are not reliable single-subtype labels.

## Implemented Curation

`Scripts/build_kiepgl_event_bag_dataset_v5.py` now supports two curation controls.

First, each output y row carries explicit label-quality metadata:

- `quality_target_group_count`
- `label_confidence`
- `label_ambiguity_reason`

For hard multiclass training, `strict_single_target_group=True` removes anchors with multiple target abnormal groups. Such mixed events should instead be used in hierarchical or partial-label settings.

Second, the builder can restrict the dataset to one continuous-casting line:

```powershell
python build_kiepgl_event_bag_dataset_v5.py --input-dir ..\knowledge_exports\quality_traceability_dataset_v4_multiclass --output-dir ..\knowledge_exports\quality_traceability_dataset_v5_event_bag_clean_line_2_1 --negative-stride 1 --event-min-gap 24 --caster-id 2 --strand-parity 1 --line-analysis-mode required
```

The line key is derived from `process_sequence_key` as `(caster_id, strand_parity)`.

## Current Clean Single-Line Dataset

Output directory:

`knowledge_exports/quality_traceability_dataset_v5_event_bag_clean_line_2_1`

Summary:

- Source rows: 76,981
- Rows on line `(caster_id=2, strand_parity=1)`: 22,503
- Source multi-target rows on this line: 2,470
- Window samples after strict hard-label curation: 20,384
- Positive event anchors: 6,743
- Negative anchors: 55

Window class distribution:

| Class | Windows |
|---|---:|
| temperature_flux | 8,768 |
| mold_level_slag_risk | 6,744 |
| process_fluctuation | 4,068 |
| speed_stopper_flow | 639 |
| no_quality_abnormal | 165 |

Label ambiguity distribution:

| Reason | Windows |
|---|---:|
| single_target_group | 20,219 |
| clear_normal | 165 |

## Interpretation

The single-line strict dataset removes the most ambiguous hard subtype labels, but it exposes a second data-quality issue: clean negative anchors are still extremely sparse. This means the current dataset is better suited for event-risk / partial-label modeling than direct flat multiclass classification unless more reliable normal windows are added.

Recommended next step: build a risk-first dataset where mixed target groups remain positive risk samples but are excluded or down-weighted for subtype supervision.
