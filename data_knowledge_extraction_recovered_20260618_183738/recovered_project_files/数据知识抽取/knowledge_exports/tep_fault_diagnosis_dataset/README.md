# TEP Fault Diagnosis Dataset

Adapted from standard Tennessee Eastman `.dat` files.

- Normal class: `event_quality_class_id = 0`.
- Fault classes: `event_quality_class_id = 1..21`.
- Testing fault files are labeled normal before sample 160 and faulty afterward.
- `split_role` preserves the official train/test source split; validation is held out from training rows by the experiment runner.
