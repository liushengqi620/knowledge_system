# LLM Expert-Condition Verifier Probe Findings

## Status

The `expert_condition_verifier` branch is implemented and executable. Live LLM access is configured through environment variables, but the current endpoint/model request returns HTTP 403, so no live LLM evidence is available yet.

To validate the pipeline without contaminating the official ready graph, a separate probe root was created:

- `knowledge_exports/public_benchmark_ready_llm_probe/skab`

An offline protocol-probe response was merged only into that copied graph:

- `knowledge_exports/llm_evidence_probe/skab_anomaly_condition_verifier_response_offline_probe.json`

This probe is not paper evidence and must not be reported as LLM-generated evidence.

## SKAB Smoke Comparison

Both runs used one seed, one epoch, and `max_rows_per_split=256`; these are execution checks, not performance claims.

| Setting | Macro-F1 | Balanced Accuracy | Notes |
| --- | ---: | ---: | --- |
| Expert + algorithmic candidate baseline | 0.4810 | 0.5586 | No verifier metadata admitted |
| Expert + algorithmic candidate + verifier probe | 0.4957 | 0.5234 | Verifier branch active |

Verifier admission diagnostics:

- Status: `ok`
- Activated condition edges: 3
- Suppressed condition edges: 1
- Class/path evidence edges before: 0
- Class/path evidence edges after: 6

Interpretation: the new branch changes the model path as intended. It should be evaluated with real LLM verifier records and multi-seed/full-epoch runs before any performance conclusion.

## C-MAPSS Original RUL Smoke

The original C-MAPSS RUL protocol executes through the current backbone:

- Target: `rul`
- Seed: 42
- Epochs: 1
- `max_rows_per_split=512`
- RMSE: 90.1441
- MAE: 67.1340

This only confirms that the original RUL task path still runs. The score is not competitive because this was a minimal smoke run.

## Tests

Passed after this change:

- `python -B -m unittest Scripts.test_llm_public_benchmark_evidence`
- `python -B -m unittest Scripts.test_ms_gse_rpf_model`
- In-memory syntax check for `Scripts/llm_public_benchmark_evidence.py` and `Scripts/run_public_ms_gse_rpf_experiment.py`

## Next Required Step

Resolve live LLM API access or provide a valid response file generated externally. Then run the formal ablation:

- A0 algorithmic-only
- A1 expert prior as late path candidate
- A2 independent LLM candidate edges
- A3 LLM expert graph correction
- A4 LLM expert-condition verifier
- A5 weak-class verifier enhancement

The formal comparison should use seeds 42, 43, and 44, full data, full epochs, and both performance and efficiency metrics.
