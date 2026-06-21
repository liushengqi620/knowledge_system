# Mechanism Gate Validation Protocol - 2026-06-20

## Question

Have we already verified how much mechanism gating improves the model?

Current answer: partially. We have evidence that expert mechanism evidence can help SKAB when used as late RPF/path-side evidence, and evidence that raw or overly strong edge injection can hurt. We do not yet have a complete AAAI-ready mechanism-gating ablation matrix across full seeds.

## Existing Evidence

Confirmed from current run artifacts:

- `C:\kg_runs\skab_full_expert_proto_probe`
  - expert evidence with `prior_strength=0`
  - seeds 42,43,44
  - Macro-F1 mean/std: `0.8419 / 0.0183`
  - interpretation: expert mechanism evidence is useful as late path-side evidence, not proof that early expert graph injection is beneficial.
- `C:\kg_runs\skab_candidate_only_edge_probe_s42`
  - algorithmic candidate-only plus candidate admission
  - seed42 Macro-F1: `0.8497`
  - interpretation: candidate admission is safer than strong edge-family routing but does not beat the best seed42 expert-path run.
- `C:\kg_runs\skab_tri_source_edge_probe_s42`
  - tri-source plus edge-family router
  - seed42 Macro-F1: `0.6865`
  - interpretation: strong multi-source routing can cause negative transfer.
- `C:\kg_runs\skab_trisource_extcand_probe` and `C:\kg_runs\skab_llm_candidate_probe`
  - Macro-F1 around `0.52`, but the protocol was not comparable and SKAB currently has no effective LLM edge family.
  - interpretation: these runs should not be used as formal claims.

## New Reproducible Matrix Tool

Implemented script:

```powershell
Scripts\mechanism_gate_ablation_matrix.py
```

It defines seven SKAB variants under one protocol:

1. `no_mechanism`
2. `raw_expert_graph`
3. `late_expert_path`
4. `expert_candidate_no_gate`
5. `expert_candidate_data_gate`
6. `expert_candidate_data_gate_consistency`
7. `algorithmic_candidate_gate_control`

The certificate reports:

- validation Macro-F1 gain over `no_mechanism`
- minimum seed-level validation gain
- low-tail validation per-class F1 gain
- test Macro-F1 gain
- baseline path Jaccard
- rejection reasons

## Smoke Verification

Smoke run:

```powershell
C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe -B Scripts\mechanism_gate_ablation_matrix.py `
  --profile smoke --seeds 42 --device cpu `
  --python C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe `
  --output-root C:\kg_runs\mechanism_gate_smoke_matrix `
  --report-dir knowledge_exports\ms_gse_rpf_mechanism_gate_ablation_smoke `
  --execute
```

Smoke result summary:

| Variant | Status | Test Macro-F1 | Val gain | Test gain | Low-tail val F1 gain |
|---|---|---:|---:|---:|---:|
| no_mechanism | baseline_complete | 0.5717 | 0.0000 | 0.0000 | 0.0000 |
| raw_expert_graph | rejected | 0.6023 | -0.0081 | 0.0306 | -0.0100 |
| late_expert_path | admitted | 0.5695 | 0.0058 | -0.0023 | 0.0031 |
| expert_candidate_no_gate | rejected | 0.5646 | -0.0014 | -0.0071 | -0.0044 |
| expert_candidate_data_gate | admitted | 0.5255 | 0.0117 | -0.0463 | 0.0063 |
| expert_candidate_data_gate_consistency | admitted | 0.5675 | 0.0300 | -0.0043 | 0.0023 |
| algorithmic_candidate_gate_control | admitted | 0.5239 | 0.0116 | -0.0478 | 0.0099 |

This smoke is not a performance claim. It only proves that the matrix is executable and that validation admission alone is not enough for a paper claim, because several admitted variants hurt test Macro-F1 under the tiny smoke setting.

## Formal Full-Seed Run

Run this next for the formal SKAB mechanism-gating claim:

```powershell
$env:PYTHONPATH='Scripts'; $env:KMP_DUPLICATE_LIB_OK='TRUE'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe -B Scripts\mechanism_gate_ablation_matrix.py `
  --profile full --seeds 42,43,44 --device cuda `
  --python C:\Users\CPILAB\.conda\envs\Py312torch290\python.exe `
  --output-root C:\kg_runs\mechanism_gate_full_matrix `
  --report-dir knowledge_exports\ms_gse_rpf_mechanism_gate_ablation_full `
  --execute
```

## Paper Claim Rule

We can claim mechanism gating improves the model only if all of the following hold in the full matrix:

1. `expert_candidate_data_gate` or `expert_candidate_data_gate_consistency` completes all planned seeds.
2. It improves validation Macro-F1 over `no_mechanism`.
3. It does not violate the low-tail per-class F1 safety threshold.
4. It improves test Macro-F1 over `no_mechanism`.
5. It is better than both `raw_expert_graph` and `expert_candidate_no_gate`, proving that the gain comes from data-supported admission rather than raw mechanism injection.
6. It is not worse than `algorithmic_candidate_gate_control`; otherwise the effect is algorithmic gating rather than expert mechanism gating.

Until those conditions are met, the rigorous statement is:

> Expert mechanism evidence is useful in SKAB as late path-side evidence, but the standalone benefit of mechanism gating is not yet fully verified under AAAI-level full-seed evidence.

