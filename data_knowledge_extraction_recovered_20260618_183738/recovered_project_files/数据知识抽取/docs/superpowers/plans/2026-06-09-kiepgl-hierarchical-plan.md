# KIEP-GL-H Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use $superpower-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking via update_plan.

**Goal:** Build a two-stage KIEP-GL-H workflow that separates event risk warning from five-class defect subtype attribution.

**Architecture:** The v6 dataset adds `risk_label`, `subtype_label`, and `hierarchical_sample_role` on top of v5 event-bag windows. The experiment runner supports `--model-mode hierarchical`, training one binary risk model and one abnormal-only subtype model, then composing final six-class probabilities as `P(normal)=1-P(risk)` and `P(class)=P(risk)*P(subtype_class)`.

**Tech Stack:** Python, pandas, numpy, scikit-learn ExtraTrees through the existing `UnifiedDefectGraphModel`, unittest.

---

### Task 1: v6 Hierarchical Dataset

**Files:**
- Create: `Scripts/build_kiepgl_hierarchical_dataset_v6.py`
- Test: `Scripts/test_kiepgl_hierarchical.py`

- [ ] Write a failing test that builds a tiny v5-style dataset and expects `risk_label`, `subtype_label`, and `hierarchical_sample_role`.
- [ ] Implement `build_kiepgl_hierarchical_dataset_v6(input_dir, output_dir)`.
- [ ] Copy v5 feature files and mapping metadata into v6 output.
- [ ] Run `python -m unittest test_kiepgl_hierarchical.KIEPGLHierarchicalTests`.

### Task 2: Hierarchical Probability Fusion

**Files:**
- Modify: `Scripts/run_kiepgl_multiclass_experiment.py`
- Test: `Scripts/test_kiepgl_hierarchical.py`

- [ ] Write a failing test for `combine_hierarchical_probabilities`.
- [ ] Implement the function so rows sum to one and normal probability is `1-risk`.
- [ ] Align subtype probabilities to original class ids 1-5.

### Task 3: Hierarchical Experiment Mode

**Files:**
- Modify: `Scripts/run_kiepgl_multiclass_experiment.py`
- Test: `Scripts/test_kiepgl_hierarchical.py`

- [ ] Write a failing smoke test that calls `run_kiepgl_multiclass_experiments(..., model_mode="hierarchical")` on a tiny dataset.
- [ ] Train a binary risk `UnifiedDefectGraphModel` on all rows.
- [ ] Train a subtype `UnifiedDefectGraphModel` only on abnormal training rows.
- [ ] Evaluate with existing multiclass event metrics and record `model_mode`, `risk_*`, and `subtype_*` diagnostics.

### Task 4: Verification

- [ ] Run `python -m unittest discover -s . -p "test*.py"` from `Scripts`.
- [ ] Build v6 from the latest v5 data.
- [ ] Run a quick hierarchical experiment.
- [ ] Commit the code changes.
