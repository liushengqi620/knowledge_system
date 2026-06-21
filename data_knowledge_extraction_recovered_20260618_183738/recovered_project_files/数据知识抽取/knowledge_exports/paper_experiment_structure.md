# Paper Experiment Structure

## Main Evidence

Use TEP as the primary mechanism-evidence benchmark. It provides the strongest aligned evidence for the paper's research question: how to safely use noisy expert/LLM mechanism knowledge in observational industrial fault diagnosis.

## Main Table

| Dataset | Role | Current Evidence |
|---|---|---|
| TEP | Primary weak-class mechanism benchmark | Full target-F1 0.9520 +/- 0.0070 under matched strict protocol |
| SKAB | Dynamic LLM graph reliability benchmark | Learned reliability improves Macro-F1 by +0.0189 |
| Hydraulic | Negative-transfer safety benchmark | Safe routing preserves near-ceiling targets and improves valve/accumulator slightly |
| C-MAPSS | Degradation generalization stress test | Current ridge residual branch gives only small gains; needs stronger temporal pretraining |

## Required Ablations

The current TEP ablation table is now strong enough to serve as the main mechanism ablation:

```text
Full              target-F1 0.9520
NoPairwise        target-F1 0.9122  delta -0.0398
NoWeakSpecialist  target-F1 0.9404  delta -0.0115
NoSupportGated    target-F1 0.9384  delta -0.0135
ExpertOnly        target-F1 0.9398  delta -0.0121
```

## Remaining SOTA Work

The next missing block is not another internal module. It is matched external baselines:

1. TEP: add strong process-fault classifiers or sequence baselines under the same 22-class strict protocol.
2. SKAB: add anomaly detection baselines such as GDN, MTAD-GAT, TranAD, USAD, or Anomaly Transformer under the same run-level protocol.
3. C-MAPSS: replace ridge residual evidence with degradation-aware temporal pretraining before claiming SOTA.
