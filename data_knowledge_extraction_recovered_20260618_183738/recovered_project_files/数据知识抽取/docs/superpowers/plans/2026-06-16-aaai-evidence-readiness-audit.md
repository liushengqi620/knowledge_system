# AAAI Evidence Readiness Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use $superpower-subagents (recommended) or $superpower-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking via update_plan.

**Goal:** Build a reproducible audit that distinguishes current performance evidence, SOTA-claim readiness, and remaining AAAI-level evidence gaps across TEP, SKAB, Hydraulic, and C-MAPSS.

**Architecture:** Add a small summarizer that reads existing JSON/Markdown experiment artifacts, applies explicit readiness gates, and writes a Markdown table plus action list. The audit should not inflate claims; it should classify each dataset as primary claim, supporting claim, safety claim, or gap until stronger baselines exist.

**Tech Stack:** Python standard library, existing `knowledge_exports` artifacts, `unittest`.

---

### Task 1: Readiness Gate Tests

**Files:**
- Create: `Scripts/test_aaai_readiness_audit.py`

- [ ] **Step 1: Write failing tests**

```python
def test_dataset_with_strong_result_but_missing_external_baseline_is_not_sota_ready():
    evidence = DatasetEvidence(dataset="TEP", proposed=0.9549, main=0.9122, strong_baselines=[])
    audit = classify_dataset(evidence)
    assert audit["claim_level"] == "method-evidence"
    assert "missing strong baselines" in audit["gaps"][0]
```

- [ ] **Step 2: Verify RED**

Run: `python -m unittest Scripts.test_aaai_readiness_audit`
Expected: import failure because `aaai_readiness_audit.py` does not exist yet.

### Task 2: Audit Implementation

**Files:**
- Create: `Scripts/aaai_readiness_audit.py`

- [ ] **Step 1: Implement dataset evidence model**

```python
@dataclass(frozen=True)
class DatasetEvidence:
    dataset: str
    task: str
    main: float | None
    proposed: float | None
    delta: float | None
    strong_baselines: list[str]
    external_gap: str
```

- [ ] **Step 2: Implement conservative claim classification**

Rules:
- `primary-sota-candidate` only if proposed score is high, delta is positive, at least two strong external baselines exist, and no protocol gap is present.
- `method-evidence` if delta is positive but strong baselines are missing.
- `safety-evidence` if the primary role is non-degradation or negative-transfer prevention.
- `gap` if score or reproducibility evidence is missing.

- [ ] **Step 3: Implement Markdown report**

Output columns:
`Dataset`, `Task`, `Main`, `Proposed`, `Delta`, `Evidence Level`, `Claim`, `Missing Evidence`, `Next Action`.

### Task 3: Generate Current Report

**Files:**
- Create: `knowledge_exports/aaai_sota_readiness_audit.md`
- Modify: `docs/reliability_calibrated_mechanism_graph_progress.md`
- Modify: `docs/ugmc_public_benchmark_first_round.md`

- [ ] **Step 1: Run audit script**

Run: `python Scripts/aaai_readiness_audit.py --output knowledge_exports/aaai_sota_readiness_audit.md`

- [ ] **Step 2: Append concise progress note to docs**

Summarize that current evidence supports AAAI method development but not universal SOTA claims until strong external baselines are completed.

### Task 4: Verification

**Files:**
- Test: `Scripts/test_aaai_readiness_audit.py`
- Test: existing summarizer tests

- [ ] **Step 1: Run targeted unit tests**

Run: `python -m unittest Scripts.test_aaai_readiness_audit Scripts.test_summarize_multi_benchmark_evidence`

- [ ] **Step 2: Syntax check edited scripts**

Run: `python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['Scripts/aaai_readiness_audit.py', 'Scripts/test_aaai_readiness_audit.py']]"`
