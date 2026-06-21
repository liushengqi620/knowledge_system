# TEP Tree-Free Baseline Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use $superpower-subagents (recommended) or $superpower-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking via update_plan.

**Goal:** Add a reproducible summary for the current TEP tree-free risk-head baseline and connect it to the multi-benchmark paper evidence.

**Architecture:** Keep the change narrow: a dedicated summarizer reads one or more TEP result JSON files, extracts the `full_model` row from `summary_table`, and writes a markdown report comparing tree-free risk heads against the strongest strict-protocol mechanism result. The report is then referenced from the paper experiment structure and reliability progress notes.

**Tech Stack:** Python standard library, existing `knowledge_exports` result JSON files, unittest, markdown reports.

---

### Task 1: Add TEP Tree-Free Summary Tests

**Files:**
- Create: `Scripts/test_summarize_tep_treefree_baselines.py`

- [ ] **Step 1: Write the failing test**

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_tep_treefree_baselines import summarize


class TepTreeFreeSummaryTest(unittest.TestCase):
    def test_summary_extracts_full_model_metrics_and_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            full = root / "full.json"
            tcn = root / "tcn.json"
            full.write_text(
                json.dumps(
                    {
                        "summary_table": [
                            {
                                "experiment_name": "full_model",
                                "target_defect_macro_f1_mean": 0.952,
                                "target_defect_macro_f1_std": 0.007,
                                "macro_f1_mean": 0.943,
                                "macro_f1_std": 0.006,
                                "event_macro_recall_mean": 0.841,
                                "event_macro_recall_std": 0.022,
                                "path_hit_rate_mean": 0.714,
                                "path_hit_rate_std": 0.0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            tcn.write_text(
                json.dumps(
                    {
                        "risk_head": "tcn",
                        "tep_prior_mode": "none",
                        "summary_table": [
                            {
                                "experiment_name": "full_model",
                                "target_defect_macro_f1_mean": 0.2645,
                                "target_defect_macro_f1_std": 0.0085,
                                "macro_f1_mean": 0.2526,
                                "macro_f1_std": 0.0082,
                                "event_macro_recall_mean": 0.2857,
                                "event_macro_recall_std": 0.0389,
                                "path_hit_rate_mean": 0.0476,
                                "path_hit_rate_std": 0.0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = summarize(reference=("StrictMechanism", full), variants=[("TCN-NoPrior", tcn)])

        self.assertIn("TCN-NoPrior", report)
        self.assertIn("0.2645 +/- 0.0085", report)
        self.assertIn("-0.6875", report)
        self.assertIn("tree-free", report)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
$env:PYTHONPATH='Scripts'; python -m unittest test_summarize_tep_treefree_baselines
```

Expected: FAIL because `summarize_tep_treefree_baselines` does not exist.

### Task 2: Implement The Summarizer

**Files:**
- Create: `Scripts/summarize_tep_treefree_baselines.py`

- [ ] **Step 1: Write minimal implementation**

Implement:
- `_load(path: Path) -> dict`
- `_first_full_row(data: dict) -> dict`
- `_metric_text(row: dict, metric: str) -> tuple[str, float]`
- `summarize(reference: tuple[str, Path], variants: list[tuple[str, Path]]) -> str`
- CLI args: `--output`, `--reference Label=path`, repeated `--variant Label=path`

- [ ] **Step 2: Run test to verify it passes**

Run:

```powershell
$env:PYTHONPATH='Scripts'; python -m unittest test_summarize_tep_treefree_baselines
```

Expected: PASS.

### Task 3: Generate The Current Report

**Files:**
- Create: `knowledge_exports/tep_treefree_baseline_summary.md`

- [ ] **Step 1: Run summarizer**

Run:

```powershell
python Scripts\summarize_tep_treefree_baselines.py --output knowledge_exports\tep_treefree_baseline_summary.md --reference StrictMechanism=archive\cleanup_20260612_175255\knowledge_exports_loose_results\tep_20k_t160_d16_l1_pairwise_support_gated_prior_s80_p025_s035_w25_seeds42_43_44.json --variant TCN-NoPrior=knowledge_exports\tep_20k_raw_tcn_risk_head_no_prior_seeds42_43_44.json
```

Expected: markdown table showing TCN-NoPrior Target-F1 `0.2645 +/- 0.0085` and a large negative delta relative to the strict mechanism result.

### Task 4: Update Paper Evidence Docs

**Files:**
- Modify: `knowledge_exports/paper_experiment_structure.md`
- Modify: `docs/reliability_calibrated_mechanism_graph_progress.md`

- [ ] **Step 1: Add tree-free evidence paragraph**

State that direct TCN replacement under the same raw 52-variable protocol currently collapses relative to the strict mechanism result, so the paper should not claim “tree-free replacement” yet. Use it as evidence that the research problem is coupling reliable mechanism evidence with a strong anchor, not simply replacing ExtraTrees.

### Task 5: Verify

**Files:**
- Test: `Scripts/test_summarize_tep_treefree_baselines.py`
- Compile: `Scripts/summarize_tep_treefree_baselines.py`

- [ ] **Step 1: Run targeted verification**

```powershell
$env:PYTHONPATH='Scripts'; python -m unittest test_summarize_tep_treefree_baselines
python -m py_compile Scripts\summarize_tep_treefree_baselines.py Scripts\test_summarize_tep_treefree_baselines.py
```

Expected: all commands pass.
