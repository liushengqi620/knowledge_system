# TEP GPU Algorithmic Edge Prior Follow-Up

This follow-up tests train-only edge initialization strategies for TEP. The prior is not an external expert/LLM prior. The completed `hybrid` prior is built from training windows only and combines three algorithmic signals:

- contemporaneous and descriptor correlation;
- directed lag support from source at `t-lag` to target at `t`;
- class-conditioned fault path evidence collapsed into a global edge bank.

Because this only gives a modest gain, the next edge-initialization branch now broadens the prior to `multiview`: extended descriptors, ridge partial-correlation residual edges, fault-response/onset ordering edges, bootstrap-stability votes, and optional group-level capping.

The prior is then injected into the same adjacency space used by the graph learner and RPF path prior features. The useful setting also reserves part of the RPF proposal budget for prior-covered paths.

| Setting | Seeds | Macro-F1 | Balanced accuracy | Prior mass | Interpretation |
|---|---:|---:|---:|---:|---|
| class-conditioned RPF, no external prior | 42/43/44 | 0.6095 +/- 0.0105 | 0.6185 +/- 0.0108 | 0.0000 | previous safest TEP GPU default |
| algorithmic edge prior, k=8, no prior coverage | 42/43/44 | 0.6051 +/- 0.0090 | 0.6132 +/- 0.0089 | 0.1104 | graph bias alone is insufficient; many final paths still have zero prior weight |
| algorithmic edge prior, k=8, prior coverage 0.25 | 42/43/44 | 0.6115 +/- 0.0119 | 0.6213 +/- 0.0105 | 0.2667 | coupling edge initialization with RPF path coverage is the first stable positive direction |
| algorithmic edge prior, k=16, prior coverage 0.25 | 42/43/44 | 0.6155 +/- 0.0055 | 0.6229 +/- 0.0088 | 0.3290 | current best algorithmic edge-prior screen; wider edge bank improves seed stability |
| algorithmic edge prior, k=16, prior coverage 0.25, strength 0.10 | 42/43/44 | 0.6125 +/- 0.0047 | 0.6239 +/- 0.0046 | 0.3337 | stronger graph bias does not improve Macro-F1; keep the graph prior mild |
| stability-aware validation admission over edge-prior candidates | 42/43/44 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | mixed | selects k8 for seed42 and k16 for seeds43/44 using validation gain, strength burden, and group-path stability |
| unified algorithm/expert/LLM admission with source burden | 42/43/44 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | mixed | expert and LLM candidates are considered but rejected after source burden; selected source-family counts are `algorithmic: 3` |
| corroborated expert+LLM + algorithmic edge prior | 42/43/44 | 0.6106 +/- 0.0053 | 0.6226 +/- 0.0055 | 0.3324 | external-only edges are dampened and overlap edges are boosted, but this still underperforms the pure algorithmic edge bank |
| unified admission including corroborated expert+LLM | 42/43/44 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | mixed | corroborated expert+LLM is proposed but rejected; selected source-family counts remain `algorithmic: 3` |
| expert+LLM anchored algorithmic subgraph | 42/43/44 | 0.6121 +/- 0.0070 | 0.6214 +/- 0.0097 | 0.3116 | external endpoints focus the algorithmic bank and improve path stability versus simple corroboration, but accuracy remains below pure algorithmic admission |
| unified admission including anchored expert+LLM | 42/43/44 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | mixed | anchored expert+LLM is proposed but rejected; selected source-family counts remain `algorithmic: 3` |
| full-row h64/e40 class-conditioned baseline | 42/43/44 | 0.6252 +/- 0.0129 | 0.6438 +/- 0.0118 | 0.0000 | stronger training budget improves TEP substantially even without algorithmic prior |
| full-row h64/e40 algorithmic edge prior, k=8 | 42/43/44 | 0.6262 +/- 0.0050 | 0.6443 +/- 0.0056 | 0.2484 | k=8 is more stable but only slightly better than baseline |
| full-row h64/e40 algorithmic edge prior, k=16 | 42/43/44 | 0.6283 +/- 0.0125 | 0.6487 +/- 0.0080 | 0.3078 | k=16 gives the best fixed full-budget mean but hurts some seeds |
| full-row h64/e40 validation admission over k8/k16/baseline | 42/43/44 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | mixed | selects k16 for seed42 and baseline for seeds43/44; strongest current TEP result under the updated protocol |
| full-row h64/e40 multiview edge prior, k=16, group cap 4 | 42/43/44 | 0.6156 +/- 0.0079 | 0.6354 +/- 0.0043 | 0.1891 | broad edge sources with hard group cap are rejected by validation; global prior becomes too sparse |
| full-row h64/e40 multiview-light edge prior, k=16 | 42/43/44 | 0.6158 +/- 0.0077 | 0.6351 +/- 0.0062 | 0.2819 | retaining hybrid-dominant weights restores edge density but still underperforms, so the issue is global coverage rather than only weighting |
| full-row h64/e40 admission incl. multiview variants | 42/43/44 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | mixed | rejects both multiview candidates; keeps k16 for seed42 and baseline for seeds43/44 |
| full-row h64/e40 class-evidence salience coverage 0.25 | 42/43/44 | 0.6155 +/- 0.0033 | 0.6335 +/- 0.0021 | 0.0000 | sample-level evidence coverage is implemented, but broad class evidence still hurts |
| full-row h64/e40 salience coverage + router top1 + aux 0.05 | 42/43/44 | 0.6146 +/- 0.0030 | 0.6359 +/- 0.0009 | 0.0000 | evidence router is sharp and supervised, but all-class prototypes still do not generalize |
| full-row h64/e40 low-tail focused class evidence | 42/43/44 | 0.6110 +/- 0.0041 | 0.6318 +/- 0.0021 | 0.0000 | focusing validation-low classes does not fix the prototype quality problem |
| full-row h64/e40 edge-bank prior, dense k16 | 42/43/44 | 0.6177 +/- 0.0045 | 0.6425 +/- 0.0030 | 0.2592 | per-source candidate voting works technically, but the resulting 813-edge prior is still too dense |
| full-row h64/e40 edge-bank prior, global budget 4x | 42/43/44 | 0.6209 +/- 0.0052 | 0.6450 +/- 0.0035 | 0.2231 | sparse edge-bank is better than dense edge-bank, confirming prior density is one failure mode |
| full-row h64/e40 edge-bank as weak RPF recall only | 42/43/44 | 0.6138 +/- 0.0062 | 0.6377 +/- 0.0036 | 0.1060 | removing graph bias and reducing prior coverage is worse; weak recall alone does not repair noisy edge quality |
| full-row h64/e40 dynamic-only edge-bank | 42/43/44 | 0.6194 +/- 0.0046 | 0.6402 +/- 0.0041 | 0.2241 | removing correlation/class/residual sources avoids some dense pseudo-edges but still does not pass admission |
| full-row h64/e40 admission incl. all edge-bank variants | 42/43/44 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | mixed | rejects all edge-bank variants; keeps k16 for seed42 and baseline for seeds43/44 |
| full-row h64/e40 hybrid k16 + identity-regularized edge calibrator v2 | 42/43/44 | 0.6203 +/- 0.0078 | 0.6419 +/- 0.0056 | 0.3039 | preserves original backbone initialization and keeps gate near 0.999, but still underperforms |
| full-row h64/e40 admission incl. edge-calibrator v2 | 42/43/44 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | mixed | rejects edge-calibrator candidates; keeps k16 for seed42 and baseline for seeds43/44 |
| full-row h64/e40 wide edge-pool k20/g4/global 6x, prior coverage 0.20 | 42/43/44 | 0.6264 +/- 0.0082 | 0.6384 +/- 0.0104 | 0.1582 | broad recall improves over edge-bank variants but remains below admission best |
| full-row h64/e40 wide edge-pool + bounded path reliability scale 0.50 | 42/43/44 | 0.6299 +/- 0.0089 | 0.6418 +/- 0.0073 | 0.1609 | path-level calibration helps versus pure edge-pool but does not pass validation admission |
| full-row h64/e40 wide edge-pool + class-prior admission floor 0.15 | 42/43/44 | 0.6284 +/- 0.0130 | 0.6363 +/- 0.0119 | 0.0827 | class-routed prior filtering is active but too aggressive for weak seeds |
| full-row h64/e40 wide edge-pool + class-prior admission floor 0.50 | 42/43/44 | 0.6296 +/- 0.0042 | 0.6415 +/- 0.0043 | 0.1056 | conservative filtering improves stability and validation scores but still misses admission |
| full-row h64/e40 wide edge-pool + adaptive prior admission f0.15/t0.25 | 42/43/44 | 0.6307 +/- 0.0045 | 0.6438 +/- 0.0037 | 0.0848 | confidence-adaptive fallback stabilizes class-prior filtering |
| full-row h64/e40 wide edge-pool + adaptive prior admission f0.15/t0.25 + bounded path reliability | 42/43/44 | 0.6361 +/- 0.0051 | 0.6477 +/- 0.0044 | 0.0867 | strongest fixed TEP candidate; path reliability and adaptive prior admission are complementary |
| full-row h64/e40 wide edge-pool + adaptive prior admission f0.15/t0.20 + bounded path reliability | 42/43/44 | 0.6298 +/- 0.0069 | 0.6430 +/- 0.0069 | 0.0817 | more aggressive trust threshold hurts seed43 |
| full-row h64/e40 admission incl. edge-pool/path-rel variants | 42/43/44 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | mixed | considers edge-pool candidates but still selects k16 for seed42 and baseline for seeds43/44 |

Conclusion: global edge initialization is useful only when it changes the RPF candidate path set, not merely when it biases the graph layer. The current default candidate for the next TEP round is the stability-aware admission route over edge-prior candidates. Its best fixed candidate is:

```text
--algorithmic-edge-prior-mode hybrid
--algorithmic-edge-prior-top-k 16
--algorithmic-edge-prior-max-lag 3
--algorithmic-edge-prior-strength 0.05
--prior-coverage-fraction 0.25
```

This is still a screening result rather than a final SOTA claim. The next algorithmic step should replace fixed prior coverage with validation-aligned admission over edge-bank variants, because the improvement is real but still modest.
The first version of that admission step is implemented in `summarize_ms_gse_rpf_admission.py` as:

```text
adjusted_validation = validation_macro_f1 - source_or_strength_burden
                    + stability_bonus_weight * top10_group_path_jaccard
```

For the current TEP screen the admitted route uses `--candidate-penalty alg_k16_s010=0.005` and `--stability-bonus-weight 0.20`.
The unified algorithm/expert/LLM route additionally uses `--candidate-penalty expert_cal=0.010` and `--candidate-penalty expert_llm_cal=0.025`. Under this rule, expert and LLM evidence remains part of the candidate set, but it does not overwrite the algorithmic edge bank unless its validation gain clears a stronger source-burden threshold.
The corroborated expert+LLM run uses `--prior-algorithmic-combine-mode corroborated_max`, `--prior-external-isolated-scale 0.25`, and `--prior-overlap-boost 0.20`. Its diagnostics show about 41 calibrated external edges, only 19-21 of which overlap the 803-edge algorithmic bank. This sparse overlap explains why expert/LLM evidence does not yet improve TEP: the external candidates are too narrow and not sufficiently aligned with the fault-family path structure learned from training data.
The anchored-subgraph run uses the same external evidence as endpoints rather than forcing all algorithmic edges equally. It keeps 640-641 algorithmic edges adjacent to 29 external anchor nodes and downweights the remaining 162-163 non-anchor algorithmic edges by 0.35. This raises group-path stability for the external candidate (`0.0351`) but still does not pass validation admission after source burden.

Full-row h64/e40 follow-up changes the TEP conclusion. Increasing training budget improves the class-conditioned baseline from `0.6095 +/- 0.0105` under the 8000-window screen to `0.6252 +/- 0.0129`. Fixed algorithmic edge banks provide only a small additional mean gain (`0.6262` for k=8, `0.6283` for k=16), but validation admission over baseline/k8/k16 reaches `0.6335 +/- 0.0090`. This supports the paper's core claim more strongly than fixed edge injection: edge banks should be admitted per validation evidence, not globally enabled.

Multiview edge initialization has been implemented and evaluated under the same full-row h64/e40 protocol. The hard group-cap version produced a 206-edge train-only prior and collapsed to `0.6156 +/- 0.0079`; the light version restored 811 edges with hybrid-dominant weights but still reached only `0.6158 +/- 0.0077`. Validation admission rejects both. This changes the next algorithmic direction: the bottleneck is no longer whether the global edge prior has enough raw edge sources. TEP needs class/fault-family conditional edge admission so a high-prior edge for one fault does not globally occupy RPF coverage for unrelated faults.

The first code hook for this has been added as `--salience-coverage-fraction`: RPF can reserve path slots for sample-level train-only evidence without requiring a static global prior edge. The first full-row probe with `salience-cover@0.25+class-evidence@8` reaches only `0.6155 +/- 0.0033`, so the mechanism works technically but the evidence source must be sharper. The next candidate should use low-tail fault-family conditional evidence rather than broad all-class evidence.

Router sharpening was also tested with `--class-evidence-router-top-k 1`, `--class-evidence-router-temperature 0.50`, and `--evidence-router-aux-weight 0.05`. It reaches only `0.6146 +/- 0.0030` despite high salience mass. This rules out a simple explanation that the router was too diffuse; the class evidence prototypes themselves are too broad for TEP. The next algorithmic step should construct low-tail fault-family prototypes for weak classes rather than mixing all 22 fault prototypes.

The edge initialization branch was then widened from a single fused prior matrix to `edge_bank`: correlation, lag, class evidence, residual partial correlation, fault-response ordering, and bootstrap stability each propose edges independently; edges keep source/vote diagnostics; optional global budget limits final prior density; zero-weight sources can be removed from voting. This is a better algorithmic interface for later expert/LLM evidence, but the TEP results are negative. Dense edge-bank produces too many high-vote edges, sparse edge-bank improves but remains below `hybrid k16`, weak recall-only edge-bank is worse, and dynamic-only edge-bank still fails validation admission.

A learnable edge calibrator was then added as a stricter test of this direction. It converts a static candidate prior into a sample-wise calibrated prior, reports `mean_edge_calibrator_gate` and `mean_calibrated_prior`, supports an identity regularizer, and is instantiated after the original backbone modules so enabling it does not change the original RPF/head initialization order. The corrected identity-regularized v2 run keeps the average gate near `0.999`, but still reaches only `0.6203 +/- 0.0078` and is rejected by admission. This indicates that the next main optimization should not be another fixed prior or prior-matrix calibrator. Calibration needs to happen after path construction: class/sample-conditioned path reliability should decide whether a selected path is useful for the current fault, rather than trying to make one global prior matrix correct before RPF.

The next wider initialization test is `edge_pool`. It expands each per-source candidate list before final caps, keeps single-source dynamic candidates as weak edges, boosts multi-source agreement, and mixes raw edge strength with rank consistency. A k20/g4/global-6x TEP run reaches `0.6264 +/- 0.0082`, better than strict edge-bank but still below the validation-admitted baseline/k16 route. Adding bounded path-reliability calibration (`--path-reliability-context-scale 0.50`, reg `0.005`) raises this to `0.6299 +/- 0.0089`.

Class-conditioned prior admission was then added so the graph can still see the broad candidate prior while RPF prior coverage receives a sample-wise prior filtered by routed class path evidence. Floor `0.15` is too aggressive: prior mass drops to `0.0827`, seed42 improves, but weak seeds degrade. Floor `0.50` is more stable (`0.6296 +/- 0.0042`) and improves validation scores versus pure edge-pool, but admission still keeps k16/baseline.

The latest version adds confidence-adaptive prior admission: class-router confidence interpolates between the broad edge pool and the class-filtered prior. This avoids over-filtering uncertain samples. Adaptive prior admission alone reaches `0.6307 +/- 0.0045`; adding bounded path reliability reaches `0.6361 +/- 0.0051`, the strongest fixed TEP candidate so far. Threshold `0.20` is worse than `0.25`, confirming that over-trusting class filtering hurts weaker seeds. The broader conclusion is now stronger: wide initialization is useful as a candidate pool, but final prior admission and path weighting must be sample-adaptive.

The next stability-admission probe has been implemented but should not be promoted as a default yet. `--use-stable-path-evidence` rebuilds class/lag path evidence over stratified train subsets, keeps cross-split edges, applies an endpoint cap, and scales the retained evidence. The first seed42 probes show why this must stay weak: the uncapped stable matrix was almost fully dense (`0.973`) and reached only `0.6314`; edge-capping reduced density to `0.064` but class filtering stayed at `0.6319`; weak class-off evidence (`strength=0.25`) recovered to `0.6384`, close to the original seed42 `0.6398` but still not a gain. Stable evidence is therefore a useful diagnostic feature for a future learned admission gate, not a hard initialization rule.

A zero-initialized learned path-admission gate was then added inside RPF. It uses path token, sample context, edge weight, prior weight, and stable/task evidence to add a bounded residual to path-fusion logits. The neutral initialization works, but TEP seed42 shows unrestricted learned admission is unsafe: strength `0.75` with reg `0.002` reaches only `0.6179`, and strength `0.20` with reg `0.02` reaches `0.6117`. The gate learns large enough path-logit shifts to keep validation high while damaging test. This rules out a simple "learn the path gate end-to-end" story. The next version should be a constrained reliability certificate or validation-admitted path-family selector, not a free learned gate.

The next code version therefore changes the edge-initialization interface again. `edge_universe` keeps a broader edge universe but admits structural, dynamic, and task edges under separate family quotas before merging them. This is meant to avoid the failure mode where generic structural/correlation edges consume the whole candidate budget and suppress lag, innovation, fault-response, or class-local evidence. The validation admission script now also has `--require-candidate-certificate`, which rejects a candidate before per-seed selection if it lacks mean validation gain, drops any seed too far, or harms low-tail per-class validation F1.

The first TEP h64/e40 `edge_universe` screen is negative: it reaches `0.6240 +/- 0.0076` Macro-F1 and `0.6352 +/- 0.0061` balanced accuracy. The candidate certificate rejects it against the current `edge_pool + adaptive prior admission + bounded path reliability` baseline with mean validation gain `-0.0008`, worst seed validation gain `-0.0293`, and low-tail per-class validation F1 gain `-0.1065`. This confirms that the current bottleneck is not missing edge families; it is path-level/class-level reliability admission after a broad edge set has been proposed.

The next implemented RPF change is deterministic path-prior consistency. It adds a bounded path-logit adjustment for prior-covered paths only when the prior edge also has enough dynamic/salience support. This is different from the failed learned path-admission gate because it has no free classifier and is auditable from diagnostics (`mean_path_prior_consistency_support`, `gate`, and `adjustment`). A no-class-evidence screen with strength `0.25`, threshold `0.35`, temperature `0.05` reaches `0.6389 +/- 0.0080` Macro-F1 and `0.6514 +/- 0.0097` balanced accuracy, but this is not strict-protocol comparable with the current class-evidence baseline. Under the strict class-conditioned protocol the same setting reaches `0.6368 +/- 0.0034` Macro-F1 and `0.6469 +/- 0.0027` balanced accuracy: lower variance but no certificate pass. The candidate certificate rejects it because mean validation gain is negative and low-tail per-class validation F1 drops by `0.0643`. A stricter dynamic/class agreement mode reaches only `0.6327 +/- 0.0020`. A softer `class_blend` support mode, which keeps a dynamic-support floor under weak class evidence, reaches only `0.6261 +/- 0.0069` and is rejected with mean validation gain `-0.0112` and low-tail F1 gain `-0.0629`. This says the path-consistency idea is useful, but the next version must be validation-guided and low-tail aware rather than globally weakened or made into a hard agreement rule.

A direct initialized-edge quality screen was also tested by setting `edge_pool` `pool_min_score=0.10` under the current adaptive-prior/path-reliability protocol. It reaches `0.6291 +/- 0.0035` Macro-F1 and `0.6408 +/- 0.0103` balanced accuracy, and the certificate rejects it with mean validation gain `-0.0148` and low-tail F1 gain `-0.1091`. This rules out a simple global score threshold: it removes useful recall for weak classes while still leaving enough noisy paths to hurt transfer. The next edge-initialization idea should therefore be a family/class-aware candidate audit, not a larger edge universe or a uniform score cutoff.

That audit is now implemented as `summarize_ms_gse_rpf_edge_audit.py`. Against the current edge-pool/adaptive-prior/path-reliability baseline, the validation-low-tail TEP classes are `9`, `15`, `3`, `10`, `16`, and `0`. The failed candidates all have low top-path overlap with the baseline: `edge_universe` `0.0364`, path-prior consistency `0.1154`, `class_blend` `0.0769`, and min-score filtering `0.0943`. A current-backbone static-lag class-evidence probe was also run with max lag `3` and lag weight `0.25`; it reaches `0.6306 +/- 0.0061` Macro-F1, `0.6453 +/- 0.0064` balanced accuracy, and is rejected with mean validation gain `-0.0086` and low-tail F1 gain `-0.0740`. Therefore the next main branch should not be another global edge initializer or a global class-evidence sharpening. It should be a low-tail protected candidate admission layer that checks whether algorithmic, expert, and LLM evidence preserve weak fault classes before changing the RPF path set.

The admission layer now contains this path protection. `summarize_ms_gse_rpf_admission.py` reports candidate-vs-baseline top-path Jaccard, supports a path-disruption penalty `weight * (1 - Jaccard)`, and supports a certificate threshold `--certificate-min-baseline-path-jaccard`. The first protected report is `knowledge_exports/ms_gse_rpf_validation_admission/tep_lowtail_path_protected_candidate_admission`. With top-10 path overlap, path-disruption penalty `0.01`, low-tail F1 protection, and minimum path Jaccard `0.05`, all current candidates are rejected and the selected runs remain the edge-pool/adaptive/path-reliability baseline (`0.6361 +/- 0.0051`). This is a stronger and more defensible paper story than another failed edge source: candidate evidence is proposed broadly but admitted only when it clears validation, weak-class, source-burden, stability, and path-disruption checks.

The broader edge-initializer rewrite is now implemented and evaluated. `edge_sieve` forms a wide train-only edge canvas from structural, dynamic, task, residual, response, and stability evidence, then removes reciprocal directions and keeps stability/corroboration-supported mechanism edges. `edge_overlay` preserves the current edge-pool prior and adds only a small number of non-replacing `edge_sieve` candidates. On TEP seed42, `edge_sieve` reduced reciprocal candidate pairs from 489 to 0 and kept 200 final edges; `edge_overlay` preserved 206 edge-pool base edges and added 42 overlay edges. The full h64/e40 results are still below the fixed baseline: `edge_sieve` cover0.15 `0.6285 +/- 0.0068`, soft cover0.05 `0.6260 +/- 0.0055`, `edge_sieve + edge_calibrator` `0.6321 +/- 0.0048`, `edge_overlay` `0.6303 +/- 0.0019`, and `edge_pool + edge_calibrator` `0.6307 +/- 0.0072`. The protected report `knowledge_exports/ms_gse_rpf_validation_admission/tep_edge_initializer_broadening_lowtail_path_protected_admission` rejects all of them. The audit `knowledge_exports/ms_gse_rpf_edge_audit/tep_edge_initializer_broadening_audit` shows repeated damage to low-tail classes 16, 9, 10, and 15. This rules out another global initialized-edge expansion as the main branch; the next branch should perform low-tail/fault-family path admission after paths are proposed.

The follow-up path-admission branch is also implemented and negative under the protected protocol. `path_evidence_consistency` adds an auditable deterministic RPF path-logit adjustment from routed path/class evidence, with an optional `relative` support mode that normalizes selected-path evidence by the per-sample maximum. This fixes the raw evidence-scale issue seen in smoke diagnostics, but does not improve TEP: relative strength `0.10` reaches `0.6277 +/- 0.0039`, relative strength `0.03` reaches `0.6304 +/- 0.0029`, salience path coverage `0.10` reaches `0.6309 +/- 0.0010`, and weak cross-split stable path evidence reaches `0.6340 +/- 0.0073`. Protected admission selects the original `edge_pool + adaptive prior admission + bounded path reliability` baseline for all seeds and rejects these candidates for validation loss and low-tail class harm. The strongest next direction is therefore a class/fault-family evidence quality certificate before path proposal or path weighting, rather than stronger global evidence boosts.

The first class-evidence quality certificate now exists, but the simple edge-stability version is not enough. It can compute stable evidence only as a certificate (`stable_path_evidence_path_mode=off`, `stable_path_evidence_class_mode=off`) and soft-filter the low-separation focus classes. TEP rejects both tested floors: `0.05` reaches `0.6263 +/- 0.0064`, and `0.50` reaches `0.6266 +/- 0.0032`. Both have candidate-vs-baseline path Jaccard around `0.095` and harm low-tail classes in validation. This means the certificate must preserve reliable path families, not only stable individual edges.

The latest initialized-edge rewrite is `edge_lattice`. The first version added a feature-group lattice on top of the direct edge universe and then tested it with edge-family routing plus edge calibration; because TEP uses mostly unique variable groups, this first version did not create new lattice-only edges and reached only `0.6300 +/- 0.0015`. The corrected affinity version expands through data-driven feature neighborhoods and creates about `970-1000` raw candidates per seed, but it reaches only `0.6278 +/- 0.0044` with cover0.15. A graph-strength-zero, path-only cover0.05 version reaches `0.6235 +/- 0.0074`. All three are rejected by protected admission. The important diagnostic is that salience mass collapses from about `0.34` in the current edge-pool/adaptive/path-reliability baseline to about `0.05` in the lattice variants. This rules out another global edge-expansion branch and motivates a two-layer design: broad lattice recall for audit, followed by low-tail/class-evidence/path-stability admission before graph or RPF use.

Artifacts:

- `knowledge_exports/tep_algprior_hybrid_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_hybrid_cover025_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_hybrid_k16_cover025_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_hybrid_k16_s010_cover025_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_algorithmic_edge_prior_candidates_gpu_stability/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_unified_algorithm_expert_llm_candidates_gpu_burdened/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_k16_expllmc_corrob_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_unified_algorithm_expert_llm_corrob_candidates_gpu/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_k16_expllmc_anchor_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_unified_algorithm_expert_llm_anchor_candidates_gpu/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_cls_k8_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_hybrid_k8_cover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_hybrid_k16_cover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_algorithmic_edge_candidates/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_multiview_smoke/summary.md`
- `knowledge_exports/tep_algprior_multiview_k16_g4_cover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_multiview_light_k16_cover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_algorithmic_edge_candidates_with_multiview_light/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_cls_salcover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_algorithmic_edge_candidates_with_salcover_multiview/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_cls_salcover025_routertop1_aux005_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_algorithmic_edge_candidates_with_router_top1/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_cls_focus_valtail6_salcover025_routertop1_aux005_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgebank_k16_vote2_sv045_cover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgebank_k16_vote2_sv045_gb4_cover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgebank_k16_vote2_sv045_gb4_cover010_nograph_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgebank_dynamic_k16_gb4_cover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_algorithmic_edge_candidates_with_edge_bank_all/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_hybrid_k16_edgecal_reg1_v2_cover025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_edge_calibrator_v2_candidates/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_edgepool_k20_g4_gb6_pool25_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgepool_k20_g4_gb6_pool25_cover020_pathrel_s05_reg0005_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_edgepool_pathrel_candidates/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_edgepool_classprior_f015_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgepool_classprior_f050_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_classprior_floors_candidates/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_edgepool_adaptiveprior_f015_thr025_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgepool_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgepool_adaptiveprior_pathrel_f015_thr020_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_full_h64_e40_adaptiveprior_pathrel_candidates/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_edgeuniverse_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgepool_vs_edgeuniverse_certificate/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_edgepool_pathpriorcons_s025_thr035_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_pathpriorcons_s015_thr050_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgepool_pathpriorcons_candidates_certificate/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_edgepool_classpath_pathpriorcons_s025_thr035_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_classpath_pathpriorcons_agree_s025_thr035_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgepool_classpath_pathpriorcons_agreement_certificate/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_algprior_edgesieve_directed_adaptiveprior_pathrel_f015_thr025_cover015_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgesieve_directed_softcover005_pathrel_f010_thr025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgesieve_directed_edgecal_f005_b15_reg005_pathrel_cover010_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgeoverlay_directed_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_edgecal_f005_b15_reg005_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edge_initializer_broadening_lowtail_path_protected_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_edge_initializer_broadening_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/tep_edgepool_lowtail_path_evidcons_relative_s003_thr050_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_lowtail_saliencecover010_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_stablepath_s4_v075_w025_k8_edge4_classoff_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_stable_path_vs_saliencecover_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_stable_path_vs_saliencecover_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/tep_edgepool_classcert_focusstable_f005_thr075_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_classcert_focusstable_f050_thr075_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_class_evidence_quality_certificate_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_class_evidence_quality_certificate_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/tep_edgelattice_router_calibrator_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/tep_edgelattice_affinity_adaptiveprior_pathrel_cover015_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/tep_edgelattice_affinity_pathonly_cover005_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edge_lattice_router_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edge_lattice_affinity_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edge_lattice_pathonly_admission/ms_gse_rpf_validation_admission.md`
