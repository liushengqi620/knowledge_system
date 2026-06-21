# V1 Evidence Package for Reliability-Calibrated Mechanism Evidence Fusion

Date: 2026-06-16

## 1. Scope

This package freezes the current experimental evidence for the reliability-calibrated mechanism evidence fusion framework. The central claim is not that observational industrial data reveal a true causal graph. The claim is narrower and safer: expert knowledge, LLM mechanism suggestions, statistical lag relations, and temporal residuals can be treated as candidate mechanism evidence, and only evidence that passes validation benefit, stability, non-degradation, and counterfactual checks is allowed to correct a strong main model.

The current main datasets are:

| Dataset | Task | Paper Role |
|---|---|---|
| TEP | 22-class process fault diagnosis | Primary positive mechanism-evidence benchmark |
| SKAB | Binary anomaly detection | Dynamic LLM/graph reliability filtering benchmark |
| Hydraulic | Four-target state diagnosis | Near-ceiling safety and non-degradation benchmark |
| C-MAPSS | Degradation-stage diagnosis | Temporal residual transfer and tail-risk routing benchmark |

SECOM should remain appendix-level or robustness-only evidence because it does not strongly match the temporal mechanism propagation theory.

## 2. Current Main Evidence Matrix

| Dataset | Main | Proposed/Reliable Variant | Delta | Current Evidence Level |
|---|---:|---:|---:|---|
| TEP | 0.9122 +/- 0.0134 | 0.9549 +/- 0.0023 | +0.0428 | method-evidence, strongest current benchmark |
| SKAB | 0.8343 +/- 0.0341 | 0.8532 +/- 0.0339 | +0.0189 | method-evidence, reliability-filtered LLM/graph evidence |
| Hydraulic | 0.9773 +/- 0.0321 | 0.9784 +/- 0.0301 | +0.0011 | method-evidence, near-ceiling non-degradation evidence |
| C-MAPSS | 0.7972 +/- 0.0228 | 0.8030 +/- 0.0236 | +0.0058 | safety-evidence, fixed ERE deployment evidence |

The strongest current conclusion is that reliable mechanism evidence helps across multiple industrial settings, but the work should not yet claim universal SOTA. TEP is the best candidate for the main SOTA-style claim after stronger matched baselines are completed.

## 3. TEP Evidence

TEP is the primary benchmark because it contains clear process-fault propagation structure, weak fault classes, expert mechanism paths, and a strict 22-class diagnosis setting. The strict mechanism result is:

```text
Strict mechanism / KIEP-GL-style result:
Target-F1 0.9549 +/- 0.0023
No-pairwise/support-gated baseline:
Target-F1 0.9122 +/- 0.0134
Delta:
+0.0428
```

Matched tree-free sequence baselines show an important limitation and an important positive pattern. TCN, GRU, and FT-Transformer do not currently replace the strict mechanism model, but residual-gated lagged graph evidence improves each no-graph temporal family:

| Family | No Graph | Residual-Gated Lagged Graph | Delta |
|---|---:|---:|---:|
| TCN | 0.5754 +/- 0.0141 | 0.6034 +/- 0.0096 | +0.0280 |
| GRU | 0.6150 +/- 0.0030 | 0.6217 +/- 0.0073 | +0.0067 |
| FT-Transformer | 0.4644 +/- 0.0110 | 0.5136 +/- 0.0218 | +0.0491 |

Interpretation: direct tree-free replacement is not enough, but the residual graph channel gives a reproducible theory signal. Graph evidence should enter as a reliability-calibrated residual verifier, not as naive all-edge smoothing.

Remaining TEP gaps:

- Add strict-protocol GDN-style and MTAD-GAT-style baselines.
- Add stronger Transformer/Anomaly Transformer style sequence baselines if feasible.
- Complete the final ablation table: no expert graph, no LLM graph, all edges, no reliability, no residual gate, no low-tail guard, no counterfactual validation.
- Align with published TEP protocol tables before making a final SOTA claim.

## 4. SKAB Evidence

SKAB validates whether dynamic LLM/graph evidence can help under a protocol-stable anomaly detection setting. The current learned-reliability route reaches:

```text
Main baseline:
Macro-F1 0.8343 +/- 0.0341
Learned reliability dynamic LLM/graph route:
Macro-F1 0.8532 +/- 0.0339
Delta:
+0.0189
```

External-style reconstruction baselines under the same matched run-level split are much weaker:

| Method | Macro-F1 | Binary F1 | FAR | MAR |
|---|---:|---:|---:|---:|
| USAD-style | 0.4759 +/- 0.0415 | 0.4062 +/- 0.0407 | 52.3516 +/- 5.6355 | 49.6254 +/- 5.2281 |
| TranAD-style | 0.5366 +/- 0.0325 | 0.4675 +/- 0.0788 | 46.5718 +/- 7.7522 | 41.5024 +/- 17.1670 |
| GDN-style | 0.5409 +/- 0.0396 | 0.4248 +/- 0.0670 | 37.0108 +/- 1.0286 | 53.9256 +/- 9.8447 |
| MTAD-GAT-style | 0.5310 +/- 0.0383 | 0.4672 +/- 0.0941 | 47.8332 +/- 11.4412 | 40.0434 +/- 19.7830 |

Counterfactual edge perturbation supports that admitted edges are not decorative explanations:

| Perturbation | Macro-F1 Drop |
|---|---:|
| Reverse admitted edge direction | -0.0234 |
| Shift admitted lag | -0.0106 |
| Replace target randomly | -0.0203 |

Remaining SKAB gaps:

- Align external baselines with official repositories or leaderboard-style settings.
- Report whether the current protocol uses run-level splits, threshold tuning, and binary-event scoring consistently.
- Add reliability ablations for LLM all-edges, no reliability, static graph, dynamic graph, and counterfactual-free graph.

## 5. Hydraulic and C-MAPSS Evidence

Hydraulic is a near-ceiling state diagnosis benchmark. Its value is mainly safety: the method should preserve strong targets and only improve where there is room.

| Target | Main | Safe Learned | Best Interpretation |
|---|---:|---:|---|
| Cooler | 1.0000 +/- 0.0000 | 1.0000 +/- 0.0000 | Saturated target, no degradation |
| Valve | 0.9280 +/- 0.0272 | 0.9315 +/- 0.0237 | Hardest target, small positive route |
| Pump | 0.9960 +/- 0.0030 | 0.9960 +/- 0.0030 | Near-ceiling preservation |
| Accumulator | 0.9850 +/- 0.0028 | 0.9860 +/- 0.0037 | Small positive route |

C-MAPSS tests whether temporal residual and reliability routing transfer to degradation-stage diagnosis:

| Dataset | Main | Fixed ERE | Delta | TailGuarded Non-Degradation |
|---|---:|---:|---:|---:|
| FD001 | 0.7786 +/- 0.0175 | 0.7879 +/- 0.0185 | +0.0093 | 3/3 |
| FD002 | 0.7932 +/- 0.0130 | 0.7964 +/- 0.0156 | +0.0031 | 3/3 |
| FD003 | 0.8250 +/- 0.0059 | 0.8327 +/- 0.0096 | +0.0078 | 3/3 |
| FD004 | 0.7918 +/- 0.0203 | 0.7949 +/- 0.0183 | +0.0031 | 3/3 |
| Pooled | 0.7972 +/- 0.0228 | 0.8030 +/- 0.0236 | +0.0058 | 12/12 |

Interpretation: Hydraulic and C-MAPSS currently support reliability and non-degradation claims, not standalone SOTA claims.

## 6. Reproducibility Index

Core reports:

| Artifact | Purpose |
|---|---|
| `knowledge_exports/multi_benchmark_evidence_matrix.md` | Cross-dataset result matrix |
| `knowledge_exports/aaai_sota_readiness_audit.md` | Conservative SOTA/readiness judgment |
| `knowledge_exports/tep_matched_treefree_baseline_evidence.md` | TEP strict and tree-free matched baseline evidence |
| `knowledge_exports/skab_external_reconstruction_baselines_summary.md` | SKAB external-style reconstruction baseline summary |
| `knowledge_exports/hydraulic_four_target_summary.md` | Hydraulic four-target result summary |
| `knowledge_exports/cmapss_fd001_fd004_deployment_policy_table.md` | C-MAPSS fixed ERE and tail-guarded summary |
| `docs/ugmc_theoretical_framework.md` | Current mathematical and theoretical framework |
| `docs/reliability_calibrated_mechanism_graph_progress.md` | Chronological progress and interpretation record |

Core scripts:

| Script | Purpose |
|---|---|
| `Scripts/run_kiepgl_multiclass_experiment.py` | Strict TEP mechanism experiment entry |
| `Scripts/run_tep_sequence_graph_ablation.py` | TEP TCN/GRU/FT graph ablation runner |
| `Scripts/tep_sequence_auxiliary.py` | Residual-gated lagged graph auxiliary features |
| `Scripts/tep_sequence_heads.py` | Tree-free sequence heads |
| `Scripts/skab_external_baselines.py` | SKAB USAD/TranAD/GDN/MTAD-GAT-style baselines |
| `Scripts/run_skab_dynamic_llm_graph_experiment.py` | SKAB dynamic LLM graph route |
| `Scripts/public_benchmark_experiment.py` | Public benchmark and reliability evaluator utilities |
| `Scripts/aaai_readiness_audit.py` | Readiness audit generator |

Key verification already run in the current branch:

```text
python -m unittest Scripts.test_summarize_tep_matched_baselines Scripts.test_summarize_tep_treefree_baselines Scripts.test_aaai_readiness_audit Scripts.test_summarize_multi_benchmark_evidence
Result: OK
```

## 7. Current Claim Boundary

Safe claim:

```text
We propose a reliability-calibrated mechanism evidence fusion framework for industrial time-series diagnosis. It treats expert knowledge, LLM suggestions, statistical lag relations, and temporal residuals as falsifiable candidate evidence rather than guaranteed causal truth. Across TEP, SKAB, Hydraulic, and C-MAPSS, reliable evidence admission improves or safely preserves strong main models, with TEP providing the strongest positive mechanism-diagnosis result.
```

Unsafe claim for now:

```text
The method is universal SOTA on all benchmarks.
```

Reason: official/matched strong baselines are not complete for every dataset, and Hydraulic/C-MAPSS currently serve more as safety/generalization benchmarks than final leaderboard claims.

## 8. Immediate Next Work

Priority 1: TEP strong baseline completion.

- Implement strict-protocol GDN-style and MTAD-GAT-style baselines.
- Add stronger Transformer-style sequence comparator if runtime permits.
- Produce a final TEP table with strict mechanism model, tree-free heads, graph baselines, and ablations.

Priority 2: ERE theory and ablation completion.

- Formalize the reliability score with validation gain, low-tail group benefit, counterfactual drop, complexity, and source trust.
- Add ablations for each reliability term.
- Report admitted and rejected evidence as part of the method, not just final predictions.

Priority 3: SKAB official-alignment check.

- Compare the current matched baselines against official repository settings.
- Clarify split, threshold, FAR/MAR, and event scoring protocol.
- Keep SKAB as reliability-filtered dynamic graph evidence unless official SOTA alignment is completed.

Priority 4: Supporting benchmark cleanup.

- Hydraulic: align the table format with published four-target results and add one temporal neural baseline.
- C-MAPSS: add stronger degradation-stage baselines and keep TailGuardedERE as safety evidence.

