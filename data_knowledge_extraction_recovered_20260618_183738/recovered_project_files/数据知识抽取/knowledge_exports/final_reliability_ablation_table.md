# Final Reliability Ablation Table

Date: 2026-06-17

This table is the paper-facing reliability ablation summary. It should be used together with `reliability_term_evidence_table.md` for detailed provenance and with `reliability_ablation_matrix.md` for completion status.

## Main Reliability Evidence

| Reliability question | Dataset | Controlled contrast | Main result | Paper interpretation |
|---|---|---|---:|---|
| Does validation-benefit admission matter? | SKAB | Learned reliability vs prior-only edge admission | learned `0.8532 +/- 0.0339`; prior-only `0.8327 +/- 0.0477` | Prior scores alone are unstable; validation-benefit admission prevents raw-edge negative transfer. |
| Is reliability more than dense graph injection? | SKAB | Learned reliability vs all 8 candidate LLM edges | learned delta `+0.0189 +/- 0.0015`; all-edge delta `+0.0185 +/- 0.0146` | All-edge can match mean performance, but learned reliability achieves the same level with fewer admitted edges and much lower gain variance. |
| Does counterfactual structure matter? | SKAB | Reverse direction, shift lag, random target | drops `-0.0234`, `-0.0106`, `-0.0203` | Direction, lag, and target assignment are used as decision evidence, not only explanation text. |
| Can counterfactual checks act before deployment? | SKAB | CF-guarded admission | `0.8398 +/- 0.0297`, delta `+0.0054 +/- 0.0077`, kept edges `0.3333 +/- 0.4714` | CF guard is conservative: it rejects unsafe edges and falls back when no edge passes. |
| Does source/complexity pruning help? | SKAB | Full MSFG vs pruned MSFG | e5 `0.6730 +/- 0.0519 -> 0.7093 +/- 0.0572`; FAR `17.4899 -> 12.2486` | Unsupported multi-source edge accumulation should be constrained before graph use. |
| Does low-tail safety matter? | C-MAPSS | Fixed ERE vs TailGuardedERE | FixedERE delta `+0.0058 +/- 0.0038`; TailGuardedERE `12/12` non-degradation | Reliability is constrained by worst-group behavior, not only mean validation gain. |
| Is reliability just an edge gate? | TEP sequence family | edge-gate all-lagged vs reliability-pruned residual gate | `0.5501 +/- 0.0089` vs `0.5514 +/- 0.0109` | Gate-only graph use is competitive but does not replace externally validated admission. |
| Is mechanism evidence decorative? | TEP strict 22-class | Full mechanism vs no expert/no sequence graph | `0.9549 +/- 0.0023` vs `0.7432 +/- 0.0102` | Mechanism evidence materially affects the decision process. |

## Manuscript Claim

The reliability module is not an experience-weighted edge score, an attention weight, or ordinary graph pruning. It is an evidence admission mechanism: candidate expert, LLM, statistical, and residual evidence may affect the anchor model only after validation-benefit, low-tail, counterfactual, and source/complexity checks. The strongest current wording is:

```text
Reliability-calibrated evidence admission provides sparse and verifiable mechanism correction under non-interventional industrial time series. It can match or exceed dense graph injection while reducing unstable raw-edge transfer and preserving explicit safeguards against unsupported LLM/expert edges.
```

## Remaining Paper Work

The reliability ablation evidence is now table-ready. The remaining work is not another reliability-term experiment by default; it is manuscript integration, exact protocol alignment for SOTA wording, and optional pure no-CF multi-seed training if the appendix needs a stricter counterfactual-free deployment row.
