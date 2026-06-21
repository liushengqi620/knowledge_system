# TEP Official-Style Protocol Alignment Note

## Protocol-aligned claim boundary

- Task: TEP 22-class process fault diagnosis.
- Current protocol: Strict 22-class matched protocol using raw 52-variable graph interface, metadata split, 20k training rows, seeds 42/43/44, Target-F1 as the primary metric, and event/path metrics as secondary diagnostics.
- Primary metric: Target-F1.
- Secondary diagnostics: Event Macro-Recall, Path Hit.

## Matched strict mechanism evidence

| Method | Target-F1 | Role | Source |
|---|---:|---|---|
| StrictMechanism | 0.9549 +/- 0.0023 | anchor plus reliability-admitted mechanism evidence | `tep_main_model_ablation_evidence.md` |
| NoExpertNoSequenceGraph | 0.7432 +/- 0.0102 | removes expert/LLM graph evidence from main prior and sequence branch | `tep_main_model_ablation_evidence.md` |
| NoLLMExpertOnlyGraph | 0.9337 +/- 0.0229 | keeps expert graph while removing LLM graph refinement | `tep_main_model_ablation_evidence.md` |
| AllEdgesNoReliability | 0.9260 +/- 0.0344 | admits all graph edges without sequence reliability pruning | `tep_main_model_ablation_evidence.md` |

## Matched tree-free and graph-temporal evidence

| Method | Target-F1 | Role | Source |
|---|---:|---|---|
| TCN20k-NoGraph | 0.5754 +/- 0.0141 | tree-free temporal no-graph baseline | `tep_matched_strong_baseline_evidence.md` |
| TCN20k-ResidualGatedLagged | 0.6034 +/- 0.0096 | TCN with residual-gated lagged graph evidence | `tep_matched_strong_baseline_evidence.md` |
| GRU20k-NoGraph | 0.6150 +/- 0.0030 | tree-free temporal no-graph baseline | `tep_matched_strong_baseline_evidence.md` |
| GRU20k-ResidualGatedLagged | 0.6217 +/- 0.0073 | GRU with residual-gated lagged graph evidence | `tep_matched_strong_baseline_evidence.md` |
| FT20k-NoGraph | 0.4644 +/- 0.0110 | tree-free tabular transformer no-graph baseline | `tep_matched_strong_baseline_evidence.md` |
| FT20k-ResidualGatedLagged | 0.5136 +/- 0.0218 | FT-Transformer with residual-gated lagged graph evidence | `tep_matched_strong_baseline_evidence.md` |
| GDN20k-NoGraph | 0.3922 +/- 0.0510 | GDN-style no-graph baseline under matched budget | `tep_gdn_20k_e10_recovered.json` |
| GDN20k-ResidualGatedLagged | 0.5179 +/- 0.0372 | GDN-style residual-gated lagged graph channel | `tep_gdn_20k_e10_recovered.json` |
| MTADGAT20k-NoGraph | 0.6369 +/- 0.0050 | MTAD-GAT-style no-graph baseline under matched budget | `tep_mtad_20k_e10_recovered.json` |
| MTADGAT20k-ResidualGatedLagged | 0.6447 +/- 0.0038 | MTAD-GAT-style residual-gated lagged graph channel | `tep_mtad_20k_e10_recovered.json` |

## Official-style boundary

These results are matched-protocol method evidence. They are not a direct leaderboard claim unless an external paper's exact split, preprocessing, class taxonomy, training regime, delay handling, and metric definition are reproduced.

Do not compare directly against 2-class anomaly detection, 21-fault-only settings, random point splits, normal-only detection protocols, point-adjusted event metrics, or any report that changes the fault taxonomy or delay treatment.

## Safe claim

Under our strict 22-class matched TEP protocol, reliability-calibrated mechanism evidence strongly outperforms tree-free graph/temporal baselines, and ablations show that the mechanism evidence is not merely decorative.

## Unsafe claim

Universal official SOTA on TEP.

## Next action

When citing external TEP papers, reproduce their exact protocol or report their numbers only as non-identical reference evidence.
