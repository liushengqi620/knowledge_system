# Project Recovery Notes

This package was created from Codex session patch records because the original `E:\lsq\Project\??????` workspace is not visible in the current tool environment. It is a best-effort reconstruction, not a byte-for-byte disk clone.

## Restored contents

- Source files and paper/experiment scripts whose full content appeared in Codex `apply_patch` change records.
- AAAI paper construction scripts, core figure rendering scripts, experiment/audit scripts, and tests.
- Codex generated PNG image cache.
- CSV manifests mapping recovered files back to original paths and session records.

## Current research state from chat history

The latest manuscript direction is an algorithmic paper titled `Reliability-Calibrated Mechanism Evidence Admission for Causal-Unverifiable Multivariate Time Series`. The core problem is how to safely use imperfect mechanism evidence in observational multivariate time series where true causal relations cannot be directly verified because of feedback control, lagged propagation, hidden confounding, regime shifts, and noise.

The method uses a strong anchor predictor as the default decision model. Expert knowledge, LLM-generated weak-class rules, lagged statistical evidence, residual dynamics, and graph paths become candidate mechanism evidence. Evidence cannot directly edit logits unless it passes a reliability certificate and a local Evidence Reliability Estimator. Final prediction follows an anchor-challenger rule: use the anchor unless an admitted challenger has sufficient reliability.

Before the data loss, the strongest confirmed progress was mainly on SKAB binary anomaly detection rather than fully public-claim-ready TEP 22-class SOTA. PatchTST, Anomaly Transformer, and Graph WaveNet exact external alignment were still pending public-claim gates.

## Caveats

- Runtime outputs such as compiled PDFs, deterministic rendered figures, result JSON files, and model checkpoints are included only if they appeared in patch records or image cache. Most should be regenerated from scripts after datasets are restored.
- API keys matching `sk-...` were redacted to `sk-REDACTED`.
- Deleted-file records are listed separately and were not restored into the active recovered tree.
