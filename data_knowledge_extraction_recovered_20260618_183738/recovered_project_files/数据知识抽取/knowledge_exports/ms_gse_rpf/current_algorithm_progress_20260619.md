# MS-GSE + RPF Current Algorithm Progress

## What changed in this round

1. The RPF path budget protocol is now stable. `--max-paths` is respected by default, and `--auto-path-budget` is only an explicit ablation. This avoids silently mixing fixed 16-path and automatic 24-path Hydraulic results.
2. The result summarizer now reports both exact feature-level `Path Jaccard` and statistic-collapsed `Group Path Jaccard`. This separates unstable feature-statistic choices from truly unstable physical sensor-group paths.
3. A `group_pair` coverage selector was implemented as an explicit ablation mode, but it is not the default because it hurt Hydraulic valve seed42.
4. RPF group coverage now supports redundancy control. Hard de-duplication excludes global top paths from the coverage branch and is kept as a negative ablation. The default is now soft redundancy: previously selected paths are penalized, not forbidden. New result JSONs report `mean_path_duplicate_rate`.
5. TEP edge initialization has been widened to `edge_bank`: each algorithmic source proposes edges independently, source/vote diagnostics are recorded, global edge-budget capping is available, and zero-weight sources are excluded from voting. This is now the correct interface for later expert/LLM edge evidence, but it is not yet a better TEP performer.
6. A learnable edge calibrator has been added as a candidate module. It generates sample-wise calibrated priors, supports identity regularization, and preserves the original backbone initialization order when enabled. TEP admission still rejects it, so it remains an ablation rather than the default backbone.
7. A wider `edge_pool` initializer is now implemented. Unlike strict `edge_bank`, it uses broad per-source recall, keeps single-source weak dynamic edges with downweighting, boosts multi-source agreement, mixes raw score with rank consistency, and records candidate-pool diagnostics.
8. Path reliability calibration now has a bounded residual scale (`--path-reliability-context-scale`) so context corrections cannot dominate the original RPF reliability logits.
9. RPF now supports class-conditioned prior admission. The dynamic graph can still see the broad candidate prior, but RPF prior coverage receives a sample-wise prior filtered by the routed class path evidence. This is the first implemented step toward treating initialization edges as a candidate pool rather than as fixed global truths.
10. Class-conditioned prior admission has been upgraded with an adaptive trust gate. `--use-adaptive-prior-admission` uses class-router confidence to interpolate between the broad edge-pool prior and the class-filtered prior, so uncertain samples fall back to broader dynamic evidence.
11. A broader `edge_canvas` initializer has been implemented as a candidate overhaul. It adds directed-lag asymmetry, innovation/shock propagation, and class-local lag evidence, then stratifies structural, dynamic, and task evidence. A follow-up variant saturates high vote counts so generic consensus edges do not dominate lower-vote dynamic/task edges. RPF also has an optional `--deduplicate-exact-paths` switch for exact duplicate direct paths; this is an ablation, not the default.
12. A sample-wise edge-family router has been implemented for algorithmic priors. `edge_pool` and `edge_canvas` now expose structural/dynamic/task family prior matrices, and `--use-edge-family-router` routes these families before RPF prior admission. `--edge-family-router-balance-weight` adds a KL-to-uniform burden regularizer. Current TEP tests show this is diagnostic but not a default: it raises validation scores while hurting test, and simple burden balancing does not fix transfer.
13. A train-only cross-split stable path evidence module has been implemented. `--use-stable-path-evidence` reconstructs class/lag path evidence on stratified train subsets, keeps edges only when they reappear across folds, applies an endpoint edge cap (`--stable-path-evidence-edge-top-k`), and scales admitted evidence with `--stable-path-evidence-strength`. The first TEP probes show this is useful diagnostically but not a direct gain: dense stable evidence was almost all edges, sparse strong class filtering hurt seed42, and weak class-off evidence recovered the baseline but did not beat it.
14. A zero-initialized learned path-admission residual has been implemented inside RPF. `--use-learned-path-admission` adds a sample/path-level logit residual from path token, sample context, edge weight, prior weight, and task/stability evidence. It starts neutral, but current TEP probes show unrestricted learned admission overfits path logits and should remain a negative ablation.
15. A new `edge_universe` initializer has been implemented to make a larger structural/dynamic/task edge universe without letting generic structural edges consume the whole top-k budget. It selects candidate edges under family quotas, exports family prior matrices for the same router/RPF interface, and is now ready for TEP screening.
16. Validation admission now supports `--require-candidate-certificate`. Candidate families can be rejected before per-seed selection if mean validation gain is too small, any seed drops too far, or low-tail per-class validation F1 is harmed. This is the guardrail needed before trying broader edge initialization, expert edges, or LLM edges.
17. RPF now supports deterministic `--use-path-prior-consistency`. Prior paths receive a bounded logit adjustment only when their prior weight agrees with dynamic/salience support. This directly targets the path-fusion bottleneck exposed by `edge_universe`: candidate edges should not be trusted just because they exist in the prior.
18. Two additional edge-initialization stress tests were added after the negative `edge_universe` result. `class_blend` path-prior consistency keeps a floor of dynamic support when class evidence is weak, and `edge_pool` with `pool_min_score=0.10` screens weak per-source candidate edges before fusion. Both are rejected by the validation certificate, which confirms that the next gain is unlikely to come from globally wider or globally stricter initialized edges.
19. `summarize_ms_gse_rpf_edge_audit.py` now produces an edge/path audit report. It compares candidate runs against a baseline, identifies validation-low-tail classes, measures per-class F1 gains, top-path Jaccard, new candidate paths, and edge-source/family counts. This turns negative edge experiments into actionable evidence for the next admission module rather than another list of failed scores.
20. Validation admission now has a path-disruption guard. `summarize_ms_gse_rpf_admission.py` records candidate-vs-baseline top-path Jaccard, can subtract `--path-disruption-penalty-weight * (1 - Jaccard)` from candidate validation scores, and can enforce `--certificate-min-baseline-path-jaccard`. This is the first concrete implementation of low-tail/path-protected candidate evidence admission.
21. A broader `edge_lattice` initializer has been added. It first builds a direct structural/dynamic/task edge universe, then expands it through explicit feature groups and train-only feature-affinity neighborhoods derived from correlation, residual, lag, and stability components. It exports a fourth `group_lattice` edge family for later routing. TEP rejects all tested lattice variants, so it is now evidence that wide recall must stay behind a low-tail/class-evidence admission layer rather than becoming the default graph prior.
22. Graph prior and RPF prior are now separated. `MSGSERPFNet` can receive a compact `prior_adjacency` for graph bias and a separate `path_candidate_prior` for RPF candidate coverage. The experiment script adds `--use-certified-graph-prior-core`, which compresses broad initialized edges into a class/path-evidence-certified graph core, and `--use-separate-path-candidate-prior`, which keeps the broad pool available only as RPF candidates. TEP confirms the split is technically useful but not sufficient: core-only lattice improves over wide separate-candidate use, but both remain rejected by low-tail/path admission.
23. RPF now has an explicit path-proposal consistency gate. `--use-path-proposal-consistency` downweights candidate path-selection scores before RPF selection when dynamic edges are not supported by prior or class/salience evidence. This is different from path-prior consistency, which adjusts logits after paths are already selected. The first TEP screen shows the gate is directionally useful: it raises selected salience mass from about `0.34` to about `0.41` and cuts Macro-F1 variance, but the current settings still fail protected low-tail admission.
24. RPF path proposal retention has been added. `--path-proposal-retention-fraction` preserves a fraction of ungated dynamic proposal slots when proposal consistency is enabled, so the gate cannot globally replace all baseline-sensitive paths. TEP shows this improves candidate-vs-baseline path overlap but does not fix low-tail harm.
25. A train-only `stable_class_edge_overlay` initializer hook has been added. It overlays cross-split stable class path evidence onto the initialized edge prior before path-family and graph-core certificates. This is useful as an audit interface for low-tail/fault-family edges, but the first TEP run confirms that stable class edges still need sample-level admission before they can safely consume RPF path slots.
26. Candidate edge priors now support explicit evidence-gated admission. `--use-candidate-prior-admission` keeps the graph backbone prior intact, gates `path_candidate_prior` by routed class/path evidence, and can send admitted candidates either to RPF coverage (`coverage`) or only to selected-path prior features (`feature`). This implements the intended split between stable graph initialization and falsifiable candidate evidence, but TEP still rejects both tested settings, so it is a diagnostic interface rather than the new default.
27. Edge initialization now has a two-layer `edge_dual_lattice` path. The stable `edge_pool` core remains the graph/RPF base prior, while a wider `edge_lattice` exploratory layer is exposed only through admitted candidate evidence. RPF also supports `--candidate-coverage-fraction` and `candidate_prior_admission_target=proposal_feature`, so exploratory edges receive a small independent path quota and selected-path prior features without replacing core prior coverage.

## TEP Edge-Initialization Overhaul

The previous full-row TEP admission result remains the strongest current TEP setting:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Interpretation |
|---|---:|---:|---:|---|
| full-row baseline/k8/k16 validation admission | 3 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | selects k16 for seed42 and baseline for seeds43/44 |

New probes after widening initialization edges:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Interpretation |
|---|---:|---:|---:|---|
| low-tail focused class evidence | 3 | 0.6110 +/- 0.0041 | 0.6318 +/- 0.0021 | focus classes do not repair broad prototype quality |
| dense edge-bank k16 | 3 | 0.6177 +/- 0.0045 | 0.6425 +/- 0.0030 | independent source voting still yields about 813 prior edges |
| sparse edge-bank, global budget 4x | 3 | 0.6209 +/- 0.0052 | 0.6450 +/- 0.0035 | better than dense edge-bank, so edge density is a real issue |
| edge-bank weak RPF recall only | 3 | 0.6138 +/- 0.0062 | 0.6377 +/- 0.0036 | removing graph bias and lowering coverage does not help |
| dynamic-only edge-bank | 3 | 0.6194 +/- 0.0046 | 0.6402 +/- 0.0041 | lag/response/stability edges alone still underperform |
| admission incl. all edge-bank variants | 3 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | rejects all edge-bank variants |
| hybrid k16 + identity-regularized edge calibrator v2 | 3 | 0.6203 +/- 0.0078 | 0.6419 +/- 0.0056 | gate stays near 0.999 but still does not recover k16 |
| admission incl. edge-calibrator v2 | 3 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | rejects edge calibrator; keeps k16/baseline admission |
| wide edge-pool, k20/g4/global 6x, prior coverage 0.20 | 3 | 0.6264 +/- 0.0082 | 0.6384 +/- 0.0104 | better than edge-bank variants, but validation still rejects it |
| wide edge-pool + bounded path reliability scale 0.50 | 3 | 0.6299 +/- 0.0089 | 0.6418 +/- 0.0073 | improves seed42/44 and confirms path-level calibration is useful, but admission still keeps k16/baseline |
| wide edge-pool + class prior admission floor 0.15 | 3 | 0.6284 +/- 0.0130 | 0.6363 +/- 0.0119 | aggressively filters prior mass; helps seed42 but hurts weak seeds |
| wide edge-pool + class prior admission floor 0.50 | 3 | 0.6296 +/- 0.0042 | 0.6415 +/- 0.0043 | more stable than floor 0.15 and improves validation over edge-pool, but still not admitted |
| wide edge-pool + adaptive prior admission f0.15/t0.25 | 3 | 0.6307 +/- 0.0045 | 0.6438 +/- 0.0037 | confidence fallback improves seed43 stability versus fixed class-prior admission |
| wide edge-pool + adaptive prior admission f0.15/t0.25 + bounded path reliability | 3 | 0.6361 +/- 0.0051 | 0.6477 +/- 0.0044 | best fixed TEP candidate so far; beats current admission test mean but is not selected by validation admission |
| wide edge-pool + adaptive prior admission f0.15/t0.20 + bounded path reliability | 3 | 0.6298 +/- 0.0069 | 0.6430 +/- 0.0069 | stronger filtering hurts seed43, so t0.25 is the safer current setting |
| admission incl. edge-pool/path-rel variants | 3 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | edge-pool candidates are considered but not admitted |
| edge-canvas + adaptive prior admission + bounded path reliability | 3 | 0.6244 +/- 0.0037 | 0.6369 +/- 0.0022 | wider raw evidence raises validation but creates repeated path usage and does not improve test |
| edge-canvas vote-saturated + adaptive prior admission + bounded path reliability | 3 | 0.6311 +/- 0.0080 | 0.6369 +/- 0.0067 | better than raw edge-canvas, but still below edge-pool and unstable on seed43 |
| edge-canvas vote-saturated + exact path dedup | 3 | 0.6234 +/- 0.0039 | 0.6360 +/- 0.0033 | removes exact duplicates but hurts test, so exact dedup is a negative ablation |
| edge-canvas vote-saturated + prior coverage 0.10 | 3 | 0.6225 +/- 0.0091 | 0.6346 +/- 0.0082 | reducing prior-path slots does not solve the mismatch |
| edge-canvas + edge-family router t0.50/b0.50 | 3 | 0.6259 +/- 0.0039 | 0.6378 +/- 0.0034 | router makes sharp family choices but stays below edge-pool; path duplication remains high |
| edge-pool + edge-family router t0.50/b0.50 | 3 | 0.6209 +/- 0.0058 | 0.6336 +/- 0.0032 | hurts current strongest initializer despite higher validation |
| edge-pool + edge-family router t0.50/b0.25 | 3 | 0.6211 +/- 0.0022 | 0.6315 +/- 0.0016 | weaker injection is still negative |
| edge-pool + edge-family router t0.50/b0.50 + balance 0.05 | 3 | 0.6199 +/- 0.0042 | 0.6316 +/- 0.0033 | KL-to-uniform burden regularization does not recover transfer |
| edge-pool + stable path evidence, dense s4/v0.75/k8/filter | seed42 | 0.6314 | 0.6476 | global stable matrix density was 0.973; this over-amplifies generic stable edges |
| edge-pool + stable path evidence, sparse edge4/filter | seed42 | 0.6319 | 0.6476 | density fixed to 0.064, but strong class filtering still suppresses useful prior mass |
| edge-pool + stable path evidence, sparse edge4/weak0.25/class-off | seed42 | 0.6384 | 0.6513 | nearly recovers original seed42 baseline 0.6398/0.6526 but does not improve it |
| edge-pool + weak stable evidence + learned path admission s0.75/reg0.002 | seed42 | 0.6179 | 0.6347 | gate adjustment is too strong (`mean_path_admission_adjustment` about 0.57) and overfits path logits |
| edge-pool + weak stable evidence + learned path admission s0.20/reg0.02 | seed42 | 0.6117 | 0.6300 | stronger regularization still hurts; free learned path-logit admission is not a safe default |
| edge-universe + adaptive prior admission + bounded path reliability | 3 | 0.6240 +/- 0.0076 | 0.6352 +/- 0.0061 | structural/dynamic/task family quotas work technically, but a wider edge universe hurts transfer |
| edge-lattice + edge-family router + edge calibrator | 3 | 0.6300 +/- 0.0015 | 0.6443 +/- 0.0013 | first lattice version did not expand on unique TEP groups; router/calibrator reduced salience mass |
| edge-lattice affinity expansion + adaptive prior admission, cover0.15 | 3 | 0.6278 +/- 0.0044 | 0.6412 +/- 0.0010 | creates about 970-1000 raw lattice candidates, but selected salience mass drops to about 0.05 |
| edge-lattice affinity expansion as weak path recall only, cover0.05, graph strength0 | 3 | 0.6235 +/- 0.0074 | 0.6383 +/- 0.0068 | removing graph bias still hurts; weak wide recall disrupts RPF paths |
| edge-lattice certified graph core + separate RPF candidate, cover0.10 | 3 | 0.6238 +/- 0.0061 | 0.6372 +/- 0.0021 | interface works, but broad RPF candidates still keep salience around 0.05 and hurt low-tail classes |
| edge-lattice certified graph core only, cover0.10 | 3 | 0.6304 +/- 0.0116 | 0.6439 +/- 0.0084 | core compression is better than exposing the wide pool to RPF, but path overlap is too low and low-tail classes still drop |
| edge-pool + proposal consistency max s0.50/thr0.35/f0.20 | 3 | 0.6359 +/- 0.0015 | 0.6466 +/- 0.0040 | nearly preserves the best fixed mean while increasing selected salience to about 0.41 and reducing Macro-F1 variance |
| edge-pool + proposal consistency max s0.35/thr0.35/f0.20 | 3 | 0.6330 +/- 0.0071 | 0.6450 +/- 0.0063 | weaker gate helps seed42 but hurts seed43, so the benefit is not monotonic |
| edge-pool + proposal consistency prior-only s0.50/thr0.35/f0.20 | 3 | 0.6310 +/- 0.0052 | 0.6415 +/- 0.0066 | prior-only proposal support is too restrictive and loses useful dynamic/class paths |
| edge-pool + proposal consistency max s0.50 + retention0.50 | 3 | 0.6344 +/- 0.0055 | 0.6468 +/- 0.0008 | retention raises candidate-vs-baseline path Jaccard to 0.0741, but low-tail validation harm increases |
| edge-pool + stable-class edge overlay s0.25/k8/g2/focus6 | 3 | 0.6344 +/- 0.0032 | 0.6436 +/- 0.0056 | overlay raises path Jaccard to 0.1875 but still hurts low-tail classes 9/16/0 |
| edge-pool + stable-class overlay + proposal agreement gate | 3 | 0.6300 +/- 0.0053 | 0.6398 +/- 0.0076 | agreement gating suppresses too many useful paths and worsens low-tail admission |
| edge-pool + adaptive prior admission + bounded path reliability + path-prior consistency s0.25/thr0.35, no class evidence | 3 | 0.6389 +/- 0.0080 | 0.6514 +/- 0.0097 | useful screen, but not strict protocol-comparable to class-evidence baseline |
| edge-pool + class evidence + adaptive prior admission + bounded path reliability + path-prior consistency s0.25/thr0.35 | 3 | 0.6368 +/- 0.0034 | 0.6469 +/- 0.0027 | strict protocol: similar mean, lower variance, certificate still rejects due low-tail validation harm |
| edge-pool + class evidence + path-prior consistency agreement s0.25/thr0.35 | 3 | 0.6327 +/- 0.0020 | 0.6434 +/- 0.0055 | class/dynamic agreement is too strict and loses mean performance |
| edge-pool + class evidence + path-prior consistency class_blend f0.25/s0.25/thr0.35 | 3 | 0.6261 +/- 0.0069 | 0.6397 +/- 0.0084 | soft class gating still hurts; certificate rejects mean validation, seed stability, and low-tail F1 |
| edge-pool min-score 0.10 + adaptive prior admission + bounded path reliability | 3 | 0.6291 +/- 0.0035 | 0.6408 +/- 0.0103 | global source-score screening removes useful recall and sharply harms low-tail validation F1 |
| edge-pool + static-lag class evidence l3/w0.25 + adaptive prior admission + bounded path reliability | 3 | 0.6306 +/- 0.0061 | 0.6453 +/- 0.0064 | conservative lagged class evidence helps seed43 but is rejected by low-tail certificate |
| edge-pool + adaptive prior admission + bounded path reliability + path-prior consistency s0.15/thr0.50, no class evidence | 3 | 0.6307 +/- 0.0053 | 0.6448 +/- 0.0067 | too conservative; loses the benefit of prior-consistency weighting |

Conclusion: the problem is no longer that initialization edges use too few raw evidence sources. Fixed global priors are either too dense, too generic, or too brittle, and simply adding more evidence families can improve validation while hurting test. The wider `edge_pool` remains stronger than the larger `edge_canvas`, `edge_universe`, and `edge_lattice` variants. The latest retention and stable-class overlay experiments reinforce the same point from another angle: preserving more baseline-like paths or injecting stable low-tail edges can improve path overlap, but it still fails if those edges are not admitted for the right sample/class context. The adaptive prior admission + bounded path reliability run is still the strongest fixed TEP candidate (`0.6361 +/- 0.0051`). The next algorithmic step should therefore be a two-layer edge/path system: a wide candidate lattice for recall/audit, plus a low-tail/class-evidence/path-stability certificate that admits only a compact, sample-relevant core into graph bias or RPF prior coverage.

The new certificates confirm this: when `edge_universe` is compared against the current edge-pool/adaptive/path-reliability baseline, it is rejected with mean validation gain `-0.0008`, worst seed validation gain `-0.0293`, and low-tail per-class validation F1 gain `-0.1065`. Path-prior consistency improves the story and can improve fixed test Macro-F1 in a non-class-evidence screen, but under the strict class-conditioned protocol it only stabilizes the mean (`0.6368 +/- 0.0034`) and remains rejected by the certificate because low-tail validation F1 drops by `0.0643`. The softer `class_blend` support rule is worse (`0.6261 +/- 0.0069`) and is rejected with mean validation gain `-0.0112` and low-tail F1 gain `-0.0629`; global `edge_pool` source-score screening at `0.10` is also rejected with mean validation gain `-0.0148` and low-tail F1 gain `-0.1091`. Conservative static-lag class evidence reaches only `0.6306 +/- 0.0061` and is rejected with mean validation gain `-0.0086` and low-tail F1 gain `-0.0740`. The intended conclusion is not "bigger edge pool wins", "filter all weak edges", or "add lag to every class prototype"; it is that path fusion needs validation-guided class/low-tail-aware reliability admission after candidate edges have been proposed.

The edge/path audit makes this failure mode explicit. Against the current fixed baseline, the validation-low-tail classes are `9`, `15`, `3`, `10`, `16`, and `0`. The audited candidates all have very low top-path overlap with the baseline (`0.0364` for `edge_universe`, `0.1154` for strict path-prior consistency, `0.0769` for `class_blend`, `0.0943` for `edge_pool` min-score, and `0.0755` for static-lag class evidence). The harmful candidates introduce new high-weight paths but do not improve the weak fault classes; for example `class_blend` drops low-tail validation F1 by `0.0364`, min-score screening by `0.0354`, and static-lag class evidence by `0.0305` on the audited low-tail set. Therefore the next main algorithm should be a low-tail-protected candidate evidence admission layer: algorithmic, expert, and LLM edges may propose paths, but a candidate family must preserve weak-class validation behavior and path stability before it can alter the RPF path set.

The first low-tail/path-protected admission report is now materialized at `knowledge_exports/ms_gse_rpf_validation_admission/tep_lowtail_path_protected_candidate_admission`. It compares `edge_universe`, strict path-prior consistency, `class_blend`, `edgepool_minscore010`, and `class_staticlag_l3w025` against the strongest fixed TEP baseline. It uses top-10 path overlap, a path-disruption penalty weight of `0.01`, the existing low-tail F1 certificate, and a minimum baseline path Jaccard of `0.05`. All candidates are rejected; `edge_universe` is additionally rejected for baseline path overlap (`0.0364`) below threshold. This report is useful for the paper story because it makes the admission standard explicit: evidence candidates are allowed to be innovative, but they must either improve validation/low-tail behavior enough to justify changing paths or remain diagnostic ablations.

The new `edge_lattice` reports reinforce this standard. The router/calibrator version reaches only `0.6300 +/- 0.0015`; the affinity-expanded version with cover0.15 reaches `0.6278 +/- 0.0044`; and the weak path-only version with cover0.05 reaches `0.6235 +/- 0.0074`. The affinity version is especially diagnostic: it expands hundreds of candidate-only edges per seed before final caps, yet selected path salience stays around `0.05` instead of the baseline's `0.34`. This means initialized edges should now be treated as a recall universe, not as the final explanation budget. The next implementation should admit lattice edges only when they are supported by routed class evidence and do not harm the known low-tail classes `9`, `15`, `3`, `10`, `16`, and `0`.

The certified graph-core experiment tested that implementation direction. The separate-candidate version compresses about 252-256 final lattice edges to 115 graph-core edges per seed but still exposes the wide pool to RPF; it reaches only `0.6238 +/- 0.0061`. The core-only version keeps RPF coverage on the certified core and improves to `0.6304 +/- 0.0116`, but protected admission rejects both. Against the edge-pool/adaptive/path-reliability baseline, core-only has mean validation gain `-0.0078`, low-tail validation gain `-0.0452`, and top-path Jaccard `0.0357`; separate-candidate has mean validation gain `-0.0129`, low-tail validation gain `-0.0432`, and path Jaccard `0.0755`. The key conclusion is that edge initialization is no longer the primary bottleneck. The next hard algorithm change should be path proposal and path fusion: candidate edges must be converted into class/low-tail-stable path proposals, and high-weight new paths with near-zero prior/salience should be suppressed unless they pass validation-backed reliability evidence.

The first path-proposal consistency implementation targets that bottleneck. It gates the proposal scores before global/coverage/prior path selection instead of only adjusting final path logits. On the current edge-pool/adaptive/path-reliability setting, `support=max(prior, salience)`, strength `0.50`, threshold `0.35`, and floor `0.20` gives `0.6359 +/- 0.0015` Macro-F1 and `0.6466 +/- 0.0040` balanced accuracy, very close to the fixed baseline while reducing seed variance and raising salience mass to `0.4064`. Protected admission still rejects it because low-tail validation F1 is slightly negative and top-path overlap is only `0.0179`; the audit shows class `16` and class `0` remain the main damaged low-tail classes. Retaining 50% of ungated proposal slots increases path overlap to `0.0741`, but test Macro-F1 is only `0.6344 +/- 0.0055` and low-tail validation harm worsens. Stable-class edge overlay raises path overlap further to `0.1875`, but reaches only `0.6344 +/- 0.0032`; adding an agreement proposal gate drops to `0.6300 +/- 0.0053`. The useful next step is not stronger global gating or broader initialization. It is sample/class-aware admission: preserve low-tail-sensitive baseline paths while allowing stable or high-salience candidate paths only for samples/classes where validation evidence supports the replacement.

## Latest Dual-Layer Edge Initialization Result

This round tested whether the poor TEP results came from the initialized edge set being too narrow. The answer is more precise: expanding edges helps only when exploratory edges are kept out of the stable core prior and receive a small, de-duplicated proposal quota.

| Setting | Seeds | Macro-F1 | Balanced accuracy | Interpretation |
|---|---:|---:|---:|---|
| edge-dual-lattice + candidate coverage_feature, no exact dedup | 3 | 0.6237 +/- 0.0071 | 0.6322 +/- 0.0082 | wider candidate layer causes exact path duplication around 0.37 and strongly disrupts top paths |
| edge-dual-lattice + coverage_feature + exact dedup | 3 | 0.6341 +/- 0.0022 | 0.6454 +/- 0.0043 | exact path de-duplication recovers most of the baseline, proving path-slot waste is a real bottleneck |
| edge-dual-lattice + proposal_feature + exact dedup + candidate cover0.08 | 3 | 0.6365 +/- 0.0018 | 0.6480 +/- 0.0020 | best strict widening result; core prior is preserved while exploratory edges receive a small independent path quota |
| edge-dual-lattice + proposal_feature + exact dedup + candidate cover0.04 | 3 | 0.6334 +/- 0.0043 | 0.6448 +/- 0.0051 | too little exploratory quota loses the seed44 benefit and is not preferred |

Compared with the current fixed edge-pool/adaptive/path-reliability baseline (`0.6361 +/- 0.0051` Macro-F1, `0.6477 +/- 0.0044` balanced accuracy), `edge_dual_lattice + proposal_feature + candidate cover0.08` gives a small fixed-test improvement and lower variance. The validation/low-tail certificate still rejects it: mean validation gain is `-0.0023`, low-tail validation gain is `-0.0066`, and top-path Jaccard is only `0.0980`. The correct next step is not another global edge initializer. The candidate proposal layer needs class/low-tail-aware admission so exploratory paths can be used where they help without replacing weak-class-sensitive baseline paths.

Artifacts:

- `knowledge_exports/ms_gse_rpf_summaries/tep_edgeduallattice_proposalfeat_dedup_f000_thr070_s020_candcover008_adaptiveprior_pathrel_cover020_summary.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_edgeduallattice_proposalfeat_dedup_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgeduallattice_proposalfeat_dedup_admission/ms_gse_rpf_validation_admission.md`

## Current Hydraulic valve evidence

Fixed protocol:

```powershell
python -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset hydraulic --hydraulic-targets valve --variant full `
  --seeds 42,43,44 --window-size 48 --hidden-dim 64 --epochs 40 `
  --batch-size 256 --max-rows-per-split 8000 `
  --graph-top-k 4 --max-paths 16 `
  --forecast-weight 0.01 --graph-weight 0.002 `
  --evidence-prior-mode none --prior-strength 0.0
```

Current fixed `max_paths=16`, `path_coverage_mode=target_group` result:

| Target | Seeds | Macro-F1 | Balanced accuracy | Path Jaccard | Group Path Jaccard |
|---|---:|---:|---:|---:|---:|
| Hydraulic valve | 3 | 0.7088 +/- 0.0747 | 0.7259 +/- 0.0700 | 0.0000 | 0.0196 |

Seed42 reaches 0.8103 Macro-F1 / 0.8224 balanced accuracy, but seeds 43 and 44 are much lower. Therefore the current Hydraulic valve result is evidence of a promising path-fusion direction, not yet a publishable main-result claim.

Note: the table above was produced before the redundancy-control patch. It remains useful for historical diagnosis, but key Hydraulic/SKAB claims must be rerun under the updated RPF before entering the final paper tables.

Updated redundancy-control checks on Hydraulic valve:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Group Path Jaccard | Duplicate rate | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| hard de-dup coverage | 3 | 0.6569 +/- 0.0458 | 0.6701 +/- 0.0471 | 0.0000 | 0.0000 | too strict; removes useful repeated evidence |
| soft redundancy coverage | 3 | 0.7098 +/- 0.0196 | 0.7102 +/- 0.0179 | 0.0577 | 0.3671 | current default; stable without forbidding strong repeated evidence |
| soft redundancy + validation-admitted salience | 3 | 0.7564 +/- 0.0446 | 0.7601 +/- 0.0499 | 0.0417 | 0.3304 | current strongest updated Hydraulic valve result |

## Negative ablation

The new `group_pair` selector forces path coverage over physical source/target group pairs. On Hydraulic valve seed42 it achieved only 0.6884 Macro-F1 / 0.6916 balanced accuracy, below the default target-group selector. This suggests that stronger static de-duplication removes useful feature-level paths.

## Next algorithm step

The next optimization should be task-aware reliability admission, not stronger static coverage. A practical direction is:

1. build train-only group salience from class-separation or validation residual signals;
2. use salience as a soft path proposal feature rather than a graph hard bias;
3. keep expert/LLM edges as candidate priors with `prior_strength=0` first;
4. report whether RPF accepts them through prior mass, path stability, and validation gain.

This keeps the paper story aligned: the classifier is not the contribution; the contribution is reliable path construction, validation-gated evidence admission, and structured fusion of algorithmic, expert, and LLM candidate evidence.

## Task-Salience RPF Check

Implemented optional train-only group salience:

- `--use-task-salience --salience-selection-strength 0.0`: salience is only a path feature.
- `--use-task-salience --salience-selection-strength 0.05`: salience softly changes path proposal scores; the dynamic graph is unchanged.

Hydraulic valve results:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Group Path Jaccard | Salience mass |
|---|---:|---:|---:|---:|---:|
| default target-group RPF | 3 | 0.7088 +/- 0.0747 | 0.7259 +/- 0.0700 | 0.0196 | 0.0000 |
| salience feature only | 1 | 0.7956 | 0.7943 | n/a | 0.7798 |
| salience proposal 0.05 | 3 | 0.7360 +/- 0.0880 | 0.7433 +/- 0.0941 | 0.0809 | 0.7658 |
| validation-admitted salience 0.05 | 3 | 0.7570 +/- 0.0614 | 0.7686 +/- 0.0626 | 0.1201 | 0.5384 |
| soft redundancy + validation-admitted salience 0.05 | 3 | 0.7564 +/- 0.0446 | 0.7601 +/- 0.0499 | 0.0417 | 0.5381 |

Interpretation:

- The salience proposal improves the three-seed mean and group-level path stability, so train-only task evidence is a useful path-fusion signal.
- Seed44 still drops to 0.6204 / 0.6207, so this is not yet a final main-result configuration.
- Validation admission selects salience for seeds 42 and 43 but falls back to baseline for seed44. This is the current strongest Hydraulic valve configuration.
- Under the updated soft redundancy protocol, admitted salience keeps essentially the same mean as the older admitted checkpoint while reducing Macro-F1 variance from 0.0614 to 0.0446 and exposing duplicate-path usage through `mean_path_duplicate_rate`.
- The next refinement should validate this admission rule on the other Hydraulic targets, then extend the same validation gate to expert/LLM candidates.

Admission artifact:

- `knowledge_exports/ms_gse_rpf_validation_admission/hydraulic_valve_salience_s005/ms_gse_rpf_validation_admission.md`

## Updated SKAB Soft-Redundancy Check

The corrected SKAB public protocol was rerun under the updated soft-redundancy RPF setting:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Path Jaccard | Duplicate rate | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| old corrected RPF checkpoint | 3 | 0.8368 +/- 0.0238 | 0.8350 +/- 0.0254 | 0.4652 | n/a | useful historical checkpoint, pre soft-redundancy protocol |
| soft redundancy baseline | 3 | 0.8150 +/- 0.0257 | 0.8164 +/- 0.0246 | 0.1657 | 0.4616 | updated default alone is weaker on SKAB |
| soft redundancy salience candidate | 3 | 0.7765 +/- 0.0627 | 0.7774 +/- 0.0555 | 0.2810 | 0.4651 | seed42 negative transfer shows salience must be admitted |
| soft redundancy expert prior candidate | 3 | 0.8117 +/- 0.0297 | 0.8140 +/- 0.0260 | 0.2010 | 0.4705 | expert prior path feature helps seed42 but hurts seed44 |
| soft redundancy + validation-admitted salience | 3 | 0.8307 +/- 0.0141 | 0.8281 +/- 0.0164 | 0.2778 | 0.4630 | current updated SKAB result; admits salience for seeds 43/44 only |
| soft redundancy + burden-aware salience/expert admission | 3 | 0.8307 +/- 0.0141 | 0.8281 +/- 0.0164 | 0.2778 | 0.4630 | adds expert burden \(B_k=0.01\); rejects tiny expert validation gains |

Interpretation:

- Soft redundancy is not universally better by itself; it needs the same validation-admission logic as task salience.
- Validation admission correctly rejects the seed42 salience candidate and accepts seed43/44.
- Expert prior evidence has nonzero prior mass and can be adopted as a path feature, but it should carry a source-burden penalty. Without the penalty, seed43 expert wins by a tiny validation margin but gives lower test performance than salience. With \(B_\text{expert}=0.01\), expert is rejected unless it delivers a clearer validation gain.
- The updated SKAB mean is slightly below the old corrected checkpoint but has lower Macro-F1 variance. The old expert/LLM prior results should be rerun under soft redundancy before being used as final paper evidence.

Artifacts:

- `knowledge_exports/ms_gse_rpf_soft_redundancy/skab_anomaly_soft_redundancy_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_salience_s005/skab_anomaly_soft_salience_s005_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_validation_admission/skab_anomaly_salience_s005/selected_runs_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_expert_prior0/skab_anomaly_soft_expert_prior0_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_validation_admission/skab_anomaly_salience_expert_burden001/ms_gse_rpf_validation_admission.md`

## Hydraulic Expert Prior Stress Test

Hydraulic valve was rerun with expert/physics priors under the same soft-redundancy protocol:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Prior mass | Interpretation |
|---|---:|---:|---:|---:|---|
| soft redundancy expert prior, exact features | 3 | 0.6701 +/- 0.0423 | 0.6935 +/- 0.0363 | 0.0000 | exact expert mean-feature edges rarely enter top paths |
| soft redundancy expert group-expanded prior | 3 | 0.6375 +/- 0.0495 | 0.6550 +/- 0.0358 | 0.0093 | group expansion makes prior visible but injects noisy evidence |
| burden-aware salience/expert admission | 3 | 0.7641 +/- 0.0350 | 0.7738 +/- 0.0335 | mixed | selects salience for seeds 42/43 and exact expert for seed44 |

Interpretation:

- Group-level expansion is useful as a stress test but not as a default: it increases prior mass while lowering accuracy.
- Exact expert prior can still be useful on seed44, but it must overcome \(B_\text{expert}=0.01\).
- This is a stronger paper story than claiming expert knowledge always improves accuracy: external evidence is auditable, can be rejected, and is only admitted when validation gain exceeds its source burden.

Artifacts:

- `knowledge_exports/ms_gse_rpf_soft_redundancy_expert_prior0/hydraulic_valve_soft_expert_prior0_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_expert_group_prior0/hydraulic_valve_soft_expert_group_prior0_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_validation_admission/hydraulic_valve_salience_expert_group_burden/ms_gse_rpf_validation_admission.md`

## Hydraulic Accumulator Updated Soft-Redundancy Result

Hydraulic accumulator has now been rerun with the same soft-redundancy RPF protocol as SKAB and Hydraulic valve:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Duplicate rate | Interpretation |
|---|---:|---:|---:|---:|---|
| soft redundancy baseline | 3 | 0.9327 +/- 0.0078 | 0.9339 +/- 0.0052 | 0.3832 | strong and stable |
| soft redundancy + raw salience | 3 | 0.8978 +/- 0.0103 | 0.8994 +/- 0.0047 | 0.3472 | salience over-constrains the path search |
| validation-admitted salience | 3 | 0.9327 +/- 0.0078 | 0.9339 +/- 0.0052 | 0.3832 | selects baseline for all seeds |

Interpretation:

- Accumulator is the clearest current positive Hydraulic result under the updated path-fusion standard.
- The negative raw-salience result is useful rather than a failure: it shows the admission gate prevents a plausible evidence source from hurting performance.
- This strengthens the paper story that RPF treats algorithmic, expert, and future LLM evidence as falsifiable candidates rather than mandatory feature injection.

Artifacts:

- `knowledge_exports/ms_gse_rpf_soft_redundancy/hydraulic_accumulator_soft_redundancy_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_salience_s005/hydraulic_accumulator_soft_salience_s005_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_validation_admission/hydraulic_accumulator_salience_s005/ms_gse_rpf_validation_admission.md`

## Hydraulic Cooler and Pump Updated Soft-Redundancy Baselines

The remaining Hydraulic targets were rerun under the same soft-redundancy RPF baseline protocol:

| Target | Seeds | Macro-F1 | Balanced accuracy | Duplicate rate | Interpretation |
|---|---:|---:|---:|---:|---|
| cooler | 3 | 0.9994 +/- 0.0009 | 0.9994 +/- 0.0009 | 0.3257 | nearly saturated and stable |
| internal_pump_leakage | 3 | 0.9790 +/- 0.0118 | 0.9792 +/- 0.0116 | 0.3771 | strong, improved over the old 0.9220 checkpoint |

Per-seed notes:

- Cooler: seed42 1.0000, seed43 0.9982, seed44 1.0000 Macro-F1.
- Internal pump leakage: seed42 0.9679, seed43 0.9954, seed44 0.9737 Macro-F1.

Interpretation:

- Hydraulic is now mostly aligned under one backbone and one protocol; the method is not relying on target-specific classifiers.
- Valve remains the bottleneck target, so future Hydraulic optimization should focus on evidence admission and path quality for valve rather than changing the main discriminator per target.

Artifacts:

- `knowledge_exports/ms_gse_rpf_soft_redundancy/hydraulic_cooler_soft_redundancy_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy/hydraulic_internal_pump_leakage_soft_redundancy_summary.md`

## C-MAPSS Strict Split and Sensor-Group Diagnosis

C-MAPSS was rerun under a stricter protocol after the split audit:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Duplicate rate | Interpretation |
|---|---:|---:|---:|---:|---|
| broad-prefix groups, strict unit validation | 3 | 0.6860 +/- 0.0236 | 0.6811 +/- 0.0242 | 0.1252 | honest baseline under official test + unit-disjoint validation |
| corrected raw sensor groups, max_paths=24 | 1 | 0.6899 | 0.6824 | 0.4297 | n_groups=25; path budget under-covers groups |
| corrected raw sensor groups, max_paths=50 | 1 | 0.6975 | 0.6929 | 0.4221 | larger budget helps slightly but remains below target |
| group_pair_inclusive, max_paths=50, hard coverage dedup | 3 | 0.6958 +/- 0.0032 | 0.6915 +/- 0.0026 | 0.0000 | much cleaner paths and lower variance, but still below target |

Code/protocol changes:

- `build_split` now records `split_protocol` and `validation_group_cols`.
- C-MAPSS validation is engine-unit disjoint (`subset, unit`), not row-random.
- TEP validation uses tail blocks per source file, not random interleaved rows.
- `feature_group_name` now removes only statistic suffixes, so Hydraulic `PS2_mean` maps to `PS2`, while C-MAPSS `sensor_15`, TEP `xmeas_01`, and `xmv_04` remain distinct groups.

Interpretation:

- The split and grouping fixes improve rigor, but C-MAPSS is still not AAAI-main-result ready.
- `group_pair_inclusive` proves that the RPF standard can enforce non-redundant sensor-pair evidence, but accuracy remains limited.
- The next C-MAPSS optimization should target learned path compression or degradation-aware priors: first select sensor-level candidates, then compress them into reliability-calibrated lifecycle evidence.

Artifacts:

- `knowledge_exports/ms_gse_rpf_soft_redundancy/cmapss_stage_soft_redundancy_groupval_summary.md`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_sensor_groups/ms_gse_rpf_cmapss_degradation_stage_id_full_prior-none_seed42.json`
- `knowledge_exports/ms_gse_rpf_soft_redundancy_sensor_groups_p50/ms_gse_rpf_cmapss_degradation_stage_id_full_prior-none_seed42.json`
- `knowledge_exports/ms_gse_rpf_group_pair_inclusive_p50/cmapss_group_pair_inclusive_p50_summary.md`

## C-MAPSS Degradation-Evidence Follow-Up

Two additional optimization probes were implemented after the strict C-MAPSS diagnosis:

1. train-only lifecycle-aware algorithmic path evidence (`--salience-mode class_lifecycle`);
2. optional degradation-stage cumulative ordinal EMD loss (`--ordinal-loss-weight`);
3. optional RPF path entropy regularization (`--path-entropy-weight`).

Current C-MAPSS seed42 findings under the same strict unit-validation protocol:

| Setting | Epochs | Macro-F1 | Balanced accuracy | Interpretation |
|---|---:|---:|---:|---|
| group_pair_inclusive p50 baseline | 40 | 0.7003 | 0.6950 | strongest previous seed42 strict checkpoint |
| lifecycle evidence as path feature | 40 | 0.7094 | 0.7052 | positive seed42 signal, but three-seed mean is only 0.7001 +/- 0.0066 and path stability drops |
| lifecycle evidence with hard proposal strength 0.05 | 40 | 0.6942 | 0.6861 | negative; evidence should not be forced into path proposal |
| class-only algorithmic evidence | 40 | 0.6982 | 0.6926 | class salience alone is insufficient for degradation stages |
| lifecycle top-8 sparse evidence | 40 | 0.6989 | 0.6929 | sparse evidence does not recover the seed42 gain |
| ordinal EMD loss, weight 0.20 | 25 | 0.6939 | 0.6877 | negative; extra ordinal smoothing makes the classifier conservative |
| path entropy regularization, weight 0.005/0.020 | 25 | 0.6909 | 0.6842 | negative; forcing low path entropy causes premature path collapse |

Interpretation:

- Lifecycle-aware path evidence is useful only when RPF treats it as a weak path feature. Hard proposal bias and hard sparsity are not robust.
- The current bottleneck is not a generic classifier replacement problem. It is a degradation-path modeling problem: one-hop RPF edges and ordinary CE do not yet capture long-horizon degradation propagation reliably.
- Ordinal EMD and path entropy regularization are now implemented as explicit ablations, but neither should be a default main-paper configuration unless later validation proves otherwise.
- The next credible optimization should be learned multi-hop path compression or validation-admitted degradation evidence, not stronger hand-crafted constraints.

## Context-Routed RPF and Path-Auxiliary Supervision

The latest backbone update targets a specific weakness found in the C-MAPSS and Hydraulic valve diagnosis: selected paths were auditable, but their weights were still mostly determined by local path tokens and the final loss was dominated by sample-level cross entropy. This made RPF closer to a post-hoc evidence aggregator than a strongly task-bound algorithmic module.

Implemented changes:

1. `ReliablePathFusion` now includes a context router. Each path still receives a local importance score, but it also receives a sample-context compatibility score from the pooled variable state. The path weight is now based on local path importance, context-path compatibility, and calibrated reliability.
2. The model now emits `path_aux_logits`, a classifier over the fused RPF path context. Training exposes `--path-aux-weight`; when positive, selected evidence paths must support the task label directly instead of only helping the final node+path head.
3. Result JSONs now report `mean_path_context_importance`, `path_aux_weight`, and `use_context_router`. The CLI also exposes `--disable-context-router` for ablation against the previous local-only path routing.

Smoke checks:

| Check | Setting | Result | Interpretation |
|---|---|---:|---|
| related unit tests | model, summarizers, evidence loaders | 31 tests OK | no protocol/API regression |
| C-MAPSS smoke | 2 epochs, 1200 rows/split, `--path-aux-weight 0.10` | Macro-F1 0.3718 | pipeline only; not a performance claim |
| context-router diagnostic | same smoke | mean context importance about 0.224/0.228 | context router is active and recorded |
| router-off smoke | 1 epoch, 800 rows/split, `--disable-context-router` | mean context importance 0.0 | ablation switch works |

Interpretation:

- This update directly addresses the main algorithmic gap: path fusion now has a learnable sample-conditioned router and an optional path-level task loss.
- The smoke experiments only verify implementation and diagnostics; they are too small to judge SOTA performance.
- The next real experiment should rerun C-MAPSS strict `group_pair_inclusive p50` with `--path-aux-weight` in `{0.05, 0.10, 0.20}` and compare against `--disable-context-router`. If validation accepts the new router, then repeat on Hydraulic valve and SKAB before promoting it to the default paper configuration.

## C-MAPSS Context/Path-Aux Formal Screening

The C-MAPSS strict `group_pair_inclusive p50` seed42 screening was rerun for the new context router and path-auxiliary loss under the same 25-epoch budget:

| Setting | Epochs | Macro-F1 | Balanced accuracy | Context importance | Interpretation |
|---|---:|---:|---:|---:|---|
| context router, aux 0.00 | 25 | 0.6941 | 0.6894 | 0.4481 | active router, but below the stronger p50/lifecycle checkpoints |
| context router, aux 0.05 | 25 | 0.6933 | 0.6871 | 0.4901 | auxiliary path supervision hurts slightly |
| context router, aux 0.10 | 25 | 0.6915 | 0.6872 | 0.4615 | stronger path supervision hurts more |

Path diagnosis:

- Without anchor protection, the top paths are dominated by `sensor -> cycle`. This means the lifecycle coordinate is being treated as an explainable target rather than a context variable.
- With `--protect-order-anchor-target`, the direction flips to `cycle -> sensor`, but accuracy drops further: aux 0.00 reaches 0.6847, aux 0.05 reaches 0.6901, and router-off reaches 0.6855.
- With `--protect-order-anchor-path-nodes`, `cycle` is removed from source/target/bridge roles in RPF paths. The top paths become sensor-to-sensor or setting-to-sensor evidence, e.g. `sensor_15 -> sensor_11` and `sensor_04 -> sensor_14`, but performance remains limited: aux 0.00 reaches 0.6896 and aux 0.05 reaches 0.6944.

Conclusion:

- The new context router is implemented and auditable, but C-MAPSS does not validate it as a performance default yet.
- Path-auxiliary loss is not a default; it should remain an ablation unless another dataset admits it.
- Order-anchor path protection improves evidence semantics but not C-MAPSS accuracy. This is useful for paper rigor, but not enough for an AAAI main-result claim.
- The deeper C-MAPSS problem is no longer just path direction. It likely needs task-specific degradation representation: health-index/RUL auxiliary supervision or regime-aware degradation prototypes, not more path-selection constraints.

Artifacts:

- `knowledge_exports/ctxp50_a000_e25/summary.md`
- `knowledge_exports/ctxp50_a005_e25/summary.md`
- `knowledge_exports/ctxp50_a010_e25/summary.md`
- `knowledge_exports/anchorp50_a000_e25/summary.md`
- `knowledge_exports/anchorp50_a005_e25/summary.md`
- `knowledge_exports/anchorp50_off_a000_e25/summary.md`
- `knowledge_exports/nodep50_a000_e25/summary.md`
- `knowledge_exports/nodep50_a005_e25/summary.md`

## C-MAPSS Health-Index Auxiliary Screening

Because path constraints did not solve C-MAPSS, the backbone now includes an optional RUL-derived health-index auxiliary head. When a dataset provides `rul`, the training script can construct:

\[
h = 1 - \min(\mathrm{RUL}, C) / C,
\]

with `--health-rul-cap` defaulting to 125. The model predicts this scalar from the shared node+path context, and `--health-aux-weight` controls the MSE auxiliary loss. This is intended to shape the degradation representation, not to replace the classification task.

Implementation:

- `MSGSERPFNet` now emits `health_pred`.
- `run_public_ms_gse_rpf_experiment.py` exposes `--health-aux-weight` and `--health-rul-cap`.
- Result summaries report `Health aux` and `Health MAE`.

C-MAPSS strict `group_pair_inclusive p50`, seed42 screening:

| Setting | Epochs | Macro-F1 | Balanced accuracy | Health MAE | Interpretation |
|---|---:|---:|---:|---:|---|
| health aux 0.05 | 25 | 0.6980 | 0.6937 | 0.1319 | mild positive over some 25-epoch probes, but not enough |
| health aux 0.10 | 25 | 0.7090 | 0.7036 | 0.1333 | strongest health signal on seed42; comparable to the best lifecycle-evidence seed42 |
| health aux 0.10 + path-node protection | 25 | 0.6741 | 0.6702 | 0.1439 | cleaner sensor paths but large accuracy drop |

Health aux 0.10 three-seed follow-up:

| Seeds | Macro-F1 | Balanced accuracy | Health MAE | Interpretation |
|---:|---:|---:|---:|---|
| 42,43,44 | 0.6869 +/- 0.0187 | 0.6811 +/- 0.0202 | 0.1394 +/- 0.0071 | seed42 improves, but seed43/44 fall below the p50 baseline |

Conclusion:

- Health-index supervision is the first C-MAPSS change that reaches about 0.709 on seed42 without hard lifecycle salience, so the degradation-representation direction is credible.
- It is not stable enough to promote as default. Seed44 drops to 0.6632 and top paths again route through `cycle`.
- Combining health supervision with path-node protection improves path semantics but damages accuracy, so the current model is still using lifecycle coordinates as a shortcut when health supervision is active.
- The next algorithmic step should be regime-aware degradation prototypes or a monotonic health representation that conditions on operating regime before entering RPF, rather than another scalar auxiliary loss.

Artifacts:

- `knowledge_exports/healthp50_h005_e25/summary.md`
- `knowledge_exports/healthp50_h010_e25/summary.md`
- `knowledge_exports/healthp50_h010_e25_seed43/summary.md`
- `knowledge_exports/healthp50_h010_e25_seed44/summary.md`
- `knowledge_exports/health_nodep50_h010_e25/summary.md`

## C-MAPSS Regime-Aware Prototype Residual RPF

The C-MAPSS bottleneck was traced to operating-regime confounding rather than a weak final classifier. A new train-only regime residualization step is now implemented and exposed through:

- `--use-regime-prototype-residuals`
- `--regime-prototype-k`
- `--regime-healthy-stage-max`

For datasets with `op_setting_*` columns, the script clusters operating regimes from the training split only. Within each regime, it estimates a healthy prototype from training samples whose internal stage id is at most `--regime-healthy-stage-max`, subtracts this prototype from sensor channels, and keeps `op_setting_*` plus the order coordinate as context. This gives RPF a degradation-residual space instead of forcing it to separate raw sensor values across mixed operating regimes.

Implementation and validation:

- `apply_regime_prototype_residuals` is implemented in `Scripts/run_public_ms_gse_rpf_experiment.py`.
- CLI wiring is complete, so formal runs can reproduce the setting directly.
- Unit tests now verify that residuals use train-only healthy baselines and leave `op_setting_*` / `cycle` unchanged.
- The related test suite passed: 35 tests OK.
- A small C-MAPSS smoke run confirmed end-to-end diagnostics and JSON output.

C-MAPSS strict `group_pair_inclusive p50`, 25 epochs, seeds 42/43/44:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Path duplicate rate | Interpretation |
|---|---:|---:|---:|---:|---|
| previous p50 baseline | 3 | 0.6958 +/- 0.0032 | 0.6915 +/- 0.0026 | 0.0000 | clean paths but weak degradation representation |
| regime prototype residual RPF | 3 | 0.8105 +/- 0.0021 | 0.8097 +/- 0.0017 | 0.0000 | current strongest C-MAPSS result; stable across seeds |
| regime residual + path-node protection | 3 | 0.8086 +/- 0.0041 | 0.8073 +/- 0.0041 | 0.0000 | removes `cycle` from evidence paths with only a small accuracy cost |

Interpretation:

- This is the first C-MAPSS update that is both large and stable: it improves the strict three-seed Macro-F1 by about 0.115 over the previous p50 result.
- The path-node-protected version is especially useful for the paper story. It keeps lifecycle information available to the temporal encoder, but prevents `cycle` from appearing as source, target, or bridge in evidence paths; top paths then become sensor-sensor or sensor-operating-setting relations.
- The unprotected version has the highest mean score, but some seeds still route paths through `cycle`. The protected version is likely the stronger default for an AAAI method claim because it better separates context from mechanism evidence.
- The remaining weakness is path stability: top-10 path Jaccard is still low. The next optimization should improve cross-seed evidence stability, not replace the backbone classifier.

Artifacts:

- `knowledge_exports/regime_residual_smoke/summary.md`
- `knowledge_exports/regimep50_k6_e25/summary.md`
- `knowledge_exports/regime_nodep50_k6_e25/summary.md`

## TEP Strict 22-Class Screening

TEP was added to the updated MS-GSE + RPF screening under the strict ready protocol:

- official train/test split is respected;
- validation uses tail blocks from each training source file;
- result JSONs record `split_protocol=official_test_blocked_source_validation`;
- the screening uses `max_rows_per_split=8000`, so it is a controlled algorithm screen rather than the final full-test paper run.

Seed42 screening results:

| Setting | Epochs | Macro-F1 | Balanced accuracy | Best validation Macro-F1 | Interpretation |
|---|---:|---:|---:|---:|---|
| `group_pair_inclusive`, hard dedup | 25 | 0.6140 | 0.6250 | 0.6961 | current baseline for high-dimensional TEP paths |
| + train-only class salience path feature | 25 | 0.6124 | 0.6181 | 0.6712 | salience is visible but not helpful |
| + path auxiliary loss 0.05 | 25 | 0.6214 | 0.6291 | 0.7072 | small positive signal; current best Macro-F1 |
| + path auxiliary loss 0.05, current code rerun | 25 | 0.6051 | 0.6208 | n/a | same no-prior setting rerun after auxiliary-head/prior-interface code changes; use as current-code control |
| + path auxiliary 0.05 + coarse class-0/nonzero loss 0.10 | 25 | 0.6049 | 0.6222 | 0.6899 | coarse normal/fault auxiliary hurts |
| default target-group soft redundancy | 25 | 0.6054 | 0.6211 | 0.6680 | repeated high-value evidence alone does not solve TEP |
| path auxiliary 0.05, longer training | 40 | 0.6199 | 0.6322 | 0.7433 | validation improves but test Macro-F1 does not; distribution gap remains |
| + expert prior as path feature only | 25 | 0.6108 | 0.6278 | 0.6868 | prior mass is only 0.0109; weak negative against no-prior path aux |
| + expert prior, fixed 20% prior coverage | 25 | 0.5981 | 0.6116 | 0.6645 | prior mass rises to 0.1877 but accuracy drops; fixed prior coverage causes negative transfer |
| + expert+LLM prior, fixed 20% prior coverage | 25 | 0.5976 | 0.6101 | 0.6612 | LLM candidates do not fix the fixed-coverage issue |
| + expert prior, dynamic-gated 5% prior coverage | 25 | 0.6038 | 0.6190 | 0.6972 | lower prior mass 0.0454 but still below no-prior path aux |
| + class-conditioned evidence router, top-8 features | 25 | 0.6167 | 0.6282 | n/a | current-code positive; sample-level class evidence repairs part of the TEP drop |
| + class router + calibrated expert prior | 25 | 0.6136 | 0.6266 | n/a | expert edges filtered 51 -> 36 by train-only lag support; safer but below class-router only |
| + class router + calibrated expert+LLM prior | 25 | 0.6216 | 0.6282 | n/a | best current-code TEP screen; LLM edges help after train-only edge calibration and sample-conditioned routing |

GPU three-seed follow-up under the same 8000-window screening budget:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Prior mass | Context importance | Inference/s | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| class-conditioned evidence router, no external prior | 42/43/44 | 0.6095 +/- 0.0105 | 0.6185 +/- 0.0108 | 0.0000 | 0.7480 | 7280.4 | current strongest TEP GPU mean among the three evidence-admission settings |
| + calibrated expert prior | 42/43/44 | 0.6088 +/- 0.0120 | 0.6168 +/- 0.0127 | 0.0284 | 0.7668 | 8021.8 | expert prior becomes visible in paths but does not improve the three-seed mean |
| + calibrated expert+LLM prior | 42/43/44 | 0.6040 +/- 0.0119 | 0.6140 +/- 0.0134 | 0.0295 | 0.7698 | 7218.5 | external evidence is not stable enough to claim as a default TEP gain |
| burden-aware validation admission | 42/43/44 | 0.6097 +/- 0.0105 | 0.6195 +/- 0.0108 | mixed | mixed | 7267.6 | selects baseline / expert+LLM / baseline; prevents most negative transfer but gives only tiny mean gain |

Algorithmic path-candidate follow-up:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Interpretation |
|---|---:|---:|---:|---|
| class evidence static-lag, max lag 3, weight 0.50 | 42/43/44 | 0.6071 +/- 0.0085 | 0.6162 +/- 0.0121 | direction-aware lag evidence is implemented but lowers the mean |
| class evidence static-lag, max lag 1, weight 0.25 | 42/43/44 | 0.6051 +/- 0.0111 | 0.6118 +/- 0.0140 | conservative lag mixing still hurts |
| two-hop RPF paths, 25% budget | 42/43/44 | 0.6005 +/- 0.0205 | 0.6049 +/- 0.0255 | seed42 improves but seed44 collapses |
| two-hop RPF paths, 10% budget | 42/43/44 | 0.6003 +/- 0.0153 | 0.6083 +/- 0.0183 | lower two-hop budget remains unstable |
| burden-aware algorithmic admission | 42/43/44 | 0.6098 +/- 0.0105 | 0.6199 +/- 0.0108 | selects baseline / static-lag / baseline; safe but only tiny gain |
| fault-family class path prototypes, k=3, weight 0.25 | 42/43/44 | 0.6058 +/- 0.0151 | 0.6121 +/- 0.0155 | train-only family smoothing helps some seeds but hurts seed44 |
| fault-family prototypes + sample gate, threshold 0.20 | 42/43/44 | 0.6074 +/- 0.0101 | 0.6142 +/- 0.0111 | sample-level gate improves seed43 to 0.6160 but is not validation-selected |
| burden-aware algorithmic admission v2 | 42/43/44 | 0.6098 +/- 0.0105 | 0.6199 +/- 0.0108 | still selects baseline / static-lag / baseline; exposes validation-test mismatch for family/gate |

Global algorithmic edge-prior follow-up:

| Setting | Seeds | Macro-F1 | Balanced accuracy | Prior mass | Interpretation |
|---|---:|---:|---:|---:|---|
| algorithmic edge prior, hybrid k=8, no prior coverage | 42/43/44 | 0.6051 +/- 0.0090 | 0.6132 +/- 0.0089 | 0.1104 | graph bias alone is insufficient; many final paths still have zero prior weight |
| algorithmic edge prior, hybrid k=8, prior coverage 0.25 | 42/43/44 | 0.6115 +/- 0.0119 | 0.6213 +/- 0.0105 | 0.2667 | coupling edge initialization with RPF path coverage gives a small positive mean gain |
| algorithmic edge prior, hybrid k=16, prior coverage 0.25 | 42/43/44 | 0.6155 +/- 0.0055 | 0.6229 +/- 0.0088 | 0.3290 | current best algorithmic edge-prior screen; wider edge bank improves seed stability |
| algorithmic edge prior, hybrid k=16, prior coverage 0.25, strength 0.10 | 42/43/44 | 0.6125 +/- 0.0047 | 0.6239 +/- 0.0046 | 0.3337 | stronger graph bias does not improve Macro-F1; keep the graph prior mild |
| stability-aware edge-prior admission | 42/43/44 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | mixed | selects k8 for seed42 and k16 for seeds43/44 using validation gain, strength burden, and group-path stability |
| unified algorithm/expert/LLM admission | 42/43/44 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | mixed | algorithmic/expert/LLM candidates are evaluated together; expert/LLM are rejected after source burden and selected source-family counts are algorithmic: 3 |
| corroborated expert+LLM + algorithmic edge prior | 42/43/44 | 0.6106 +/- 0.0053 | 0.6226 +/- 0.0055 | 0.3324 | external-only edges are dampened and overlap edges are boosted, but this still underperforms pure algorithmic edge banks |
| unified admission including corroborated expert+LLM | 42/43/44 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | mixed | corroborated expert+LLM is also rejected; selected source-family counts remain algorithmic: 3 |
| expert+LLM anchored algorithmic subgraph | 42/43/44 | 0.6121 +/- 0.0070 | 0.6214 +/- 0.0097 | 0.3116 | external endpoints focus the algorithmic bank; path stability improves versus corroborated fusion but accuracy remains below pure algorithmic admission |
| unified admission including anchored expert+LLM | 42/43/44 | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | mixed | anchored expert+LLM is proposed but rejected; selected source-family counts remain algorithmic: 3 |
| full-row h64/e40 class-conditioned baseline | 42/43/44 | 0.6252 +/- 0.0129 | 0.6438 +/- 0.0118 | 0.0000 | stronger training budget improves TEP substantially even without algorithmic prior |
| full-row h64/e40 algorithmic edge prior, hybrid k=8 | 42/43/44 | 0.6262 +/- 0.0050 | 0.6443 +/- 0.0056 | 0.2484 | stable but only slightly above baseline |
| full-row h64/e40 algorithmic edge prior, hybrid k=16 | 42/43/44 | 0.6283 +/- 0.0125 | 0.6487 +/- 0.0080 | 0.3078 | best fixed full-budget mean but hurts seed43 |
| full-row h64/e40 validation admission over baseline/k8/k16 | 42/43/44 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | mixed | strongest current TEP result; selects k16 for seed42 and baseline for seeds43/44 |
| full-row h64/e40 multiview edge prior, k=16, group cap 4 | 42/43/44 | 0.6156 +/- 0.0079 | 0.6354 +/- 0.0043 | 0.1891 | broad edge sources plus hard group cap are validation-rejected; the global prior becomes too sparse |
| full-row h64/e40 multiview-light edge prior, k=16 | 42/43/44 | 0.6158 +/- 0.0077 | 0.6351 +/- 0.0062 | 0.2819 | hybrid-dominant weighting restores edge density but still underperforms, showing global prior coverage is the bottleneck |
| full-row h64/e40 admission incl. multiview variants | 42/43/44 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | mixed | rejects both multiview candidates and keeps the previous baseline/k16 admission decision |
| full-row h64/e40 class evidence salience coverage 0.25 | 42/43/44 | 0.6155 +/- 0.0033 | 0.6335 +/- 0.0021 | 0.0000 | new sample-level evidence coverage mechanism works technically but current all-class evidence is validation-rejected |
| full-row h64/e40 salience coverage + router top1 + aux 0.05 | 42/43/44 | 0.6146 +/- 0.0030 | 0.6359 +/- 0.0009 | 0.0000 | sharp supervised router still fails, so prototype quality rather than router diffuseness is the bottleneck |

Broad edge-initialization update:

- The old `hybrid` edge prior is not broad enough for TEP. It combines correlation, directed lag support, and class-conditioned evidence, but it still admits many common-driver and duplicated feature-variant edges.
- A new `--algorithmic-edge-prior-mode multiview` has been implemented for the next TEP round. It adds extended window descriptors, ridge partial-correlation residual edges, fault-response/onset ordering edges, bootstrap stability votes, and optional `--algorithmic-edge-prior-group-top-k` group-level capping.
- TEP full-row validation shows that global `multiview` is not yet the right mechanism. The hard group-cap version keeps 206 edges and falls to `0.6156 +/- 0.0079`; the light version keeps 811 edges but still reaches only `0.6158 +/- 0.0077`. Both are rejected by validation admission.
- RPF now supports `--salience-coverage-fraction`, which reserves part of the direct path budget for sample-level train-only salience/class-evidence paths even when no static global prior edge exists. The mechanism is implemented and tested, but the first full-row TEP candidate (`salience-cover@0.25+class-evidence@8`) reaches only `0.6155 +/- 0.0033`, so the class evidence must be sharpened by fault family or low-tail class admission before it can be a main claim.
- Class-evidence routing now supports `--class-evidence-router-top-k` and `--class-evidence-router-temperature`. A supervised sharp-router probe (`router-top1`, temperature `0.50`, router aux `0.05`) reaches only `0.6146 +/- 0.0030`, so the failure is not just softmax dilution. The class/fault evidence prototypes themselves need low-tail, fault-family-specific construction.

Implementation changes:

- `summarize_classification` now records per-class precision/recall/F1/support for future TEP fault-class diagnosis.
- `MSGSERPFNet` now exposes an optional `coarse_logits` head.
- `run_public_ms_gse_rpf_experiment.py` exposes `--coarse-aux-weight`.
- `ReliablePathFusion` now exposes `prior_coverage_fraction` and the CLI exposes `--prior-coverage-fraction`; prior-covered candidates are selected by `prior * dynamic_edge_score`, not by the static prior alone.
- `ReliablePathFusion` now accepts sample-level path evidence matrices. `MSGSERPFNet` adds an optional class-conditioned evidence router (`--use-class-conditioned-evidence`) with auxiliary supervision (`--evidence-router-aux-weight`).
- `run_public_ms_gse_rpf_experiment.py` adds train-only prior edge calibration (`--calibrate-prior-edges`) using lagged temporal support before expert/LLM edges enter RPF.
- `compute_train_class_path_evidence` now supports `--class-evidence-mode static_lag|lag`, `--class-evidence-max-lag`, and `--class-evidence-lag-weight`. This adds directed train-only lag support to class-conditioned path evidence without changing the default static mode.
- `compute_train_class_path_evidence` also supports train-only fault-family path prototypes through `--class-evidence-family-k` and `--class-evidence-family-weight`.
- `MSGSERPFNet` now supports sample-level class evidence admission through `--class-evidence-gate-threshold`, `--class-evidence-gate-temperature`, and `--class-evidence-gate-floor`; summaries report `Class adm.`.
- `compute_train_algorithmic_edge_prior` now builds a train-only global edge bank from correlation, directed lag support, class-conditioned fault evidence, and in `multiview` mode also residual partial-correlation, fault-response ordering, and bootstrap-stability evidence. The CLI exposes `--algorithmic-edge-prior-mode`, `--algorithmic-edge-prior-top-k`, `--algorithmic-edge-prior-group-top-k`, `--algorithmic-edge-prior-max-lag`, component weights, and `--algorithmic-edge-prior-strength`. The strongest completed TEP result is now full-row h64/e40 validation admission over baseline/k8/k16; `multiview` is the next full-budget candidate.
- `ReliablePathFusion` now supports `--salience-coverage-fraction`. Unlike `--salience-selection-strength`, which softly shifts dynamic edge scores, this reserves explicit path slots for sample-level train-only evidence. This is the code hook needed for class/fault-family conditional edge admission.
- `MSGSERPFNet` now supports sharp class-evidence routing through `--class-evidence-router-top-k` and `--class-evidence-router-temperature`, and diagnostics expose the routed `class_evidence_gate`.
- `combine_algorithmic_and_external_priors` adds optional `--prior-algorithmic-combine-mode corroborated_max|anchored_subgraph` paths. `corroborated_max` keeps algorithmic-only edges, boosts expert/LLM edges that overlap train-only algorithmic support, and dampens external-only edges. `anchored_subgraph` treats external endpoints as mechanism anchors: algorithmic edges adjacent to those anchors keep full strength, while non-anchor algorithmic edges are downweighted by `--prior-nonanchor-algorithmic-scale`.
- `summarize_ms_gse_rpf_admission.py` now supports stability-aware admission and source-family adoption statistics. Candidate score is validation Macro-F1 minus candidate burden plus `stability_bonus_weight * top10_group_path_jaccard`, so path stability is part of the auditable selection rule rather than a post-hoc explanation. Reports now count admitted source families (`algorithmic`, `expert`, `llm`, `baseline`).
- The result summarizer now includes a `Setting` column and groups by setting as well as dataset/target/variant/prior, preventing mixed protocol aggregation.
- Related tests passed: 43 tests OK after lag evidence, 40 targeted tests OK after family/gate admission, 35 core MS-GSE/RPF tests OK after global algorithmic edge-prior integration, 40 related tests OK after stability-aware admission, 45 related tests OK after `multiview` edge initialization, 47 related tests OK after sample-level salience coverage, and 49 related tests OK after sharp class-evidence routing.

Interpretation:

- TEP is currently the main remaining algorithm gap. The model learns several faults well, but hard classes such as 21, 9, 13, 15, 3 and the normal class have low per-class F1 in the salience/path-aux screens.
- Path auxiliary supervision gives a small positive signal, so selected paths do need direct task pressure.
- Coarse class-0/nonzero supervision does not solve the problem, which suggests the bottleneck is not simply normal-vs-fault separation. TEP likely needs fault-family mechanism evidence, temporal onset alignment, or class-specific dynamic path prototypes.
- Expert/LLM priors are present in the TEP knowledge graph, but fixed prior coverage is negative: it increases `mean_path_prior_weight` while lowering Macro-F1. The issue is therefore the integration mechanism, not just missing knowledge.
- The new class-conditioned evidence router supports that diagnosis: no-prior current-code TEP improves from 0.6051 to 0.6167 when RPF receives sample-level class-path evidence.
- Expert-only calibrated priors remain slightly negative on seed42, and the unified GPU three-seed follow-up shows that expert+LLM priors are also not a stable TEP gain. The earlier seed42 positive result should be treated as a useful probe, not as final paper evidence.
- Burden-aware validation admission with \(B_\text{expert}=0.01\) and \(B_\text{expert+LLM}=0.015\) selects baseline for seeds 42/44 and expert+LLM for seed43, reaching 0.6097 +/- 0.0105 Macro-F1. It is a useful safety/admission result, but the +0.0002 gain over algorithm-only is not a strong performance claim.
- The new lag-aware and two-hop candidates show the right failure mode: long/lagged paths can help individual seeds but are not stable when admitted globally. This supports a stronger fault-family path-prototype direction rather than unconditional lag correlation or a fixed two-hop path budget.
- Fault-family prototypes and sample-level gating are now implemented. The current family/gate setting is still not a stable TEP gain, but it exposes the next bottleneck: the validation score does not always select the candidate with stronger test behavior. This must be handled by better validation-aligned routing or group-stability admission, not by test-set selection.
- Global algorithmic edge initialization is now implemented and gives the first positive TEP direction beyond local path tweaks when it is coupled to RPF prior coverage. Hybrid k=16 with 25% prior coverage reaches 0.6155 +/- 0.0055 Macro-F1, above the 0.6095 +/- 0.0105 class-conditioned default. Full-row h64/e40 training raises the baseline to 0.6252 +/- 0.0129 and fixed hybrid k=16 to 0.6283 +/- 0.0125, while validation admission over baseline/k8/k16 reaches 0.6335 +/- 0.0090. The `multiview` test was necessary but negative: hard group capping makes the global prior too sparse, and light multiview keeps enough edges but still pushes unrelated high-prior paths across all faults. The new sample-level salience coverage mechanism also fails when driven by broad all-class evidence (`0.6155 +/- 0.0033`), and sharpening/supervising the router does not fix it (`0.6146 +/- 0.0030`). This means the next algorithmic step should not be another global edge-bank variant, raw class-evidence coverage, or merely a sharper router. It should be low-tail class/fault-family conditional evidence construction: multiview, expert, and LLM evidence can propose mechanisms, but RPF coverage should be conditioned on weak fault families and accepted by validation burden plus low-tail fault performance. The unified algorithm/expert/LLM admission route keeps the same score while rejecting external evidence under explicit source burdens (`expert_cal=0.010`, `expert_llm_cal=0.025`), yielding selected source-family counts `algorithmic: 3`. A stricter corroborated expert+LLM fusion also fails to improve TEP because calibrated external edges overlap only about 19-21 of 803 algorithmic prior edges; anchored subgraph improves path stability but is still rejected. This is now the stronger algorithmic-path story: edge banks are not fixed globally; algorithmic, expert, and LLM candidates are admitted by validation gain, source/strength burden, path stability, train-only corroboration, and next by fault-family conditioning.
- The current TEP bottleneck is evidence admission and temporal path quality. External expert/LLM edges should carry a source burden and be accepted only when validation gain is clear; otherwise the algorithm-only class-conditioned router is the safer default.
- The next TEP optimization should make edge-bank admission validation-aligned: compare k=8/k=16/coverage/strength candidates on validation burden and low-tail stability, then admit the edge bank per seed or per fault family rather than forcing generic class salience, a coarse auxiliary head, unconditional expert/LLM admission, or a single fixed prior budget.

2026-06-20 edge-initializer broadening update:

- `compute_train_algorithmic_edge_prior` now includes `edge_sieve` and `edge_overlay`. `edge_sieve` builds a broad train-only candidate canvas from correlation, lag, directed-lag asymmetry, innovation, class evidence, class-lag evidence, residual partial correlation, fault-response ordering, and bootstrap stability, then removes reciprocal directions and keeps only stability/corroboration-supported mechanism edges. `edge_overlay` preserves the current edge-pool prior and adds a limited number of non-replacing `edge_sieve` candidates.
- On TEP seed42, `edge_sieve` reduced reciprocal candidate pairs from 489 to 0 and produced 200 final edges from 671 pre-final candidates. `edge_overlay` kept 206 edge-pool base edges and added 42 direction-stable overlay edges.
- Full TEP h64/e40 results remain below the current fixed baseline `edge_pool + adaptive prior admission + bounded path reliability` (`0.6361 +/- 0.0051`). `edge_sieve` cover0.15 reached `0.6285 +/- 0.0068`, soft cover0.05 reached `0.6260 +/- 0.0055`, `edge_sieve + edge_calibrator` reached `0.6321 +/- 0.0048`, `edge_overlay` reached `0.6303 +/- 0.0019`, and `edge_pool + edge_calibrator` reached `0.6307 +/- 0.0072`.
- The protected admission report `knowledge_exports/ms_gse_rpf_validation_admission/tep_edge_initializer_broadening_lowtail_path_protected_admission/ms_gse_rpf_validation_admission.md` rejects all five candidates. Rejection reasons are mean validation loss, seed-level validation drop, and low-tail class harm. Candidate-vs-baseline path Jaccard ranges from `0.0755` to `0.2667`, so even path-preserving variants still disrupt useful RPF paths.
- The edge audit `knowledge_exports/ms_gse_rpf_edge_audit/tep_edge_initializer_broadening_audit/ms_gse_rpf_edge_audit.md` identifies classes `16`, `9`, `10`, and `15` as repeatedly harmed. Many new top paths have zero prior or low salience, which means the remaining failure is in path proposal/reliability admission, not only in the initialized prior matrix.
- Conclusion: do not keep expanding global initialized edges as the main TEP branch. The next branch should build a low-tail/fault-family path admission layer that protects weak classes before initialized algorithmic/expert/LLM edges can change the RPF path set.

2026-06-20 low-tail path-admission update:

- RPF now has an optional deterministic `path_evidence_consistency` adjustment. Unlike `path_prior_consistency`, it can act on class/path-evidence-supported paths even when the selected path has no initialized prior coverage. It supports `absolute` evidence support and `relative` support, where selected-path evidence is normalized by the per-sample maximum to avoid raw class-evidence scale collapse.
- Smoke diagnostics showed why the relative mode was needed: absolute support on TEP had mean path salience around `0.041`, so a threshold of `0.35` produced almost no positive gate. Relative support raised the mean consistency support to about `0.392` and the mean adjustment to about `0.034`, proving the mechanism is active.
- Full TEP h64/e40 results still do not pass protected admission. Relative evidence consistency with strength `0.10` reached `0.6277 +/- 0.0039`, while the softer `0.03` setting reached `0.6304 +/- 0.0029`, both below the fixed baseline `0.6361 +/- 0.0051`. Protected admission rejects both for mean validation loss, seed-level validation drop, and low-tail class harm.
- Reserving candidate path slots for class evidence (`salience_coverage_fraction=0.10`) reached `0.6309 +/- 0.0010`. It increases salience mass but is also rejected, with low-tail validation harm concentrated on classes `0`, `16`, `9`, and `15`.
- Cross-split stable path evidence remains the closest diagnostic direction but is still not stable. The formal three-seed `stable_path` weak class-off candidate reached `0.6340 +/- 0.0073`; seed42 improved to `0.6428`, but seed44 dropped to `0.6250`. It has higher candidate-vs-baseline path Jaccard (`0.1667`) than salience coverage (`0.0962`), but protected admission still rejects it due to validation loss and low-tail harm.
- A first `class_evidence_quality_certificate` is implemented. It can run stable path reconstruction only as a certificate (`stable_path_evidence_path_mode=off`, `stable_path_evidence_class_mode=off`) and then soft-filter only the low-separation focus classes. This did not solve TEP: floor `0.05` reached `0.6263 +/- 0.0064`, and floor `0.50` reached `0.6266 +/- 0.0032`. Protected admission rejects both for validation loss and low-tail class harm; audit shows repeated harm to classes `9`, `16`, `0`, and `3` with candidate-vs-baseline path Jaccard around `0.095`.
- Current conclusion: the next improvement should not be another global path budget, stronger path-evidence logit boost, or simple cross-split stability filter. It should estimate a path-family quality certificate for class/fault-family evidence before that evidence can change path candidates or path weights. Useful inputs are cross-split edge stability, candidate-vs-baseline path family preservation, per-class low-tail membership, fault-family prototypes, and possibly expert/LLM mechanism corroboration, but the admission decision must remain algorithmic and low-tail protected.

2026-06-20 edge-certificate initializer rewrite:

- A new `edge_cert_pool` initializer is implemented. It treats the initialized graph as a candidate ledger rather than one fused score: structural, dynamic, and task families are collected separately, each edge receives vote/family/certificate diagnostics, reciprocal directions are removed using directed support, and only mechanism-certified dynamic/task/stable edges are retained. This was a deliberate replacement test for the whole initialized edge set.
- The replacement test is negative but diagnostic. On full TEP h64/e40, `edge_cert_pool` reaches `0.6247 +/- 0.0027` Macro-F1 and `0.6376 +/- 0.0036` balanced accuracy. It keeps about 194-200 final edges with mean certificate near `0.97`, but candidate-vs-baseline path Jaccard is only `0.0741`, and protected admission rejects it for mean validation loss, seed-level validation drop, and low-tail class harm (`-0.0760`).
- A new `edge_cert_overlay` initializer is also implemented. The first version preserved an edge-pool-like base but used the broader canvas component set, so it was not a strict anchor. That version reached `0.6329 +/- 0.0075` and was rejected. The corrected anchor version keeps the original edge-pool component set as graph backbone and overlays only 26 certified candidate edges per seed; it reaches `0.6304 +/- 0.0060`, improves candidate-vs-baseline path Jaccard to `0.2128`, but still fails low-tail admission (`-0.0551`).
- The final two-prior version makes the graph prior conservative and exposes the overlay only through `path_candidate_prior`: graph bias stays on the edge-pool base while RPF can see the broader overlay candidate matrix. This matches the desired direction of weakening the standalone initializer and strengthening fusion. It gives a positive seed42 signal (`0.6404`) but seed43/44 regress, with three-seed Macro-F1 `0.6311 +/- 0.0067`; protected admission rejects it with mean validation gain `-0.0081` and low-tail gain `-0.0862`.
- Code status: `compute_train_algorithmic_edge_prior` now supports `edge_cert_pool` and `edge_cert_overlay`; `edge_cert_overlay` emits an internal `_path_candidate_prior_matrix`, and `run_ready_task` passes it to `MSGSERPFNet.set_path_candidate_prior` while keeping the compact graph prior separate. Related model/summary/admission/audit tests pass (`116` tests OK).
- Conclusion: the broad-initialized-edge problem is not solved by replacing, overlaying, or two-prior exposing more global edges. The useful signal is seed-local and class-local. The next hard algorithm step should be class/low-tail-aware edge-family admission: overlay candidates should be admitted only for samples or fault families where validation evidence shows no low-tail harm, instead of entering RPF as one global candidate matrix.

2026-06-20 candidate-prior admission and dual-prior RPF:

- `MSGSERPFNet` now has an explicit `use_candidate_prior_admission` gate. When enabled, `path_candidate_prior` no longer replaces the RPF base prior. The base prior is preserved, candidate edges are scaled by a sigmoid gate over routed class/path evidence, and diagnostics expose `candidate_prior_admission_support`, `candidate_prior_admission_gate`, `candidate_prior_overlay_adjacency`, and the final RPF prior.
- RPF now separates coverage prior and feature prior. `candidate_prior_admission_target=coverage` lets admitted candidates reserve RPF prior-coverage slots; `feature` keeps coverage on the conservative base prior and uses admitted candidates only as selected-path prior features. This was added specifically to test whether the poor results came from candidates replacing the path set rather than from candidate evidence itself.
- The coverage-target TEP run (`edge_cert_overlay + candidate-prior admission`, floor `0.05`, threshold `0.50`, scale `0.50`) reaches `0.6316 +/- 0.0094` Macro-F1 and `0.6433 +/- 0.0116` balanced accuracy. It improves seed42 (`+0.0050` test Macro-F1 over the edge-pool baseline) but hurts seed43/44. Protected admission rejects it with mean validation gain `-0.0047`, worst seed gain `-0.0191`, low-tail validation F1 gain `-0.0819`, and path Jaccard `0.1400`.
- The feature-only target is worse: `0.6284 +/- 0.0064` Macro-F1 and `0.6418 +/- 0.0054` balanced accuracy. Protected admission rejects it with mean validation gain `-0.0121`, low-tail validation F1 gain `-0.1025`, and path Jaccard `0.1200`.
- Conclusion: the failure is not only that candidate edges are stealing path-coverage slots. Even when candidate edges are limited to prior features, the class/path evidence that gates them is not aligned well enough with TEP's weak fault classes. The next broadening step should move from global candidate-edge admission to class/fault-family path certificates: candidates should be admitted by weak-class stability, baseline-path preservation, and validation gain before they can affect either coverage or path features.

2026-06-20 latest edge-initialization and path-proposal gating update:

- Candidate-prior admission now has hard support floors. `candidate_prior_admission_min_support` removes candidate overlay edges whose routed class/path evidence is below a fixed support floor, and `candidate_prior_admission_protected_min_support` raises that floor in proportion to routed mass on low-tail/focus classes. Diagnostics expose `candidate_prior_admission_mask` and `candidate_protected_class_mass`. Related model and summary tests pass.
- The hard floor helped only partially. `edge_dual_lattice + proposal_feature + min_support=0.50` remains the best dual-lattice variant seen so far (`0.6375 +/- 0.0044` Macro-F1), but adding protected floor `0.70` reaches only `0.6364 +/- 0.0029`. It reduces prior mass from about `0.0880` to `0.0437` and is still rejected by admission because low-tail validation classes are harmed.
- A new `edge_guarded_lattice` initializer is implemented. It keeps the graph backbone on the compact `edge_pool` core, but exposes a broader path-candidate prior from `edge_sieve`, so candidates are expanded only through mechanism-stability, direction, and family evidence rather than the unconstrained group lattice. The implementation emits `edge_guarded_lattice` diagnostics and keeps the candidate prior separate from the graph prior.
- The guarded initializer is a negative result on TEP: `0.6279 +/- 0.0037` Macro-F1 and `0.6421 +/- 0.0002` balanced accuracy. Audit shows low-tail validation harm is smaller than the protected-floor variant, but test gain is negative and top new paths are still salience-heavy with weak or zero prior. This means the bottleneck is not just the initialized edge set; path proposal still lets high-salience, low-prior paths dominate.
- A path-proposal consistency probe confirms the coupling issue. Using the previous best `edge_dual_lattice` but gating proposal ranking by prior support (`path_proposal_consistency_support_mode=prior`) gives good single-seed signals at strength `0.50` for seeds 42/43, but seed44 drops sharply. Reducing strength to `0.25` repairs seed44 but hurts seeds 42/43. The full strength-0.50 run reaches `0.6343 +/- 0.0079` and is rejected for seed-level validation drop and low-tail class harm.
- A class-conditioned path-proposal gate is now implemented through `path_proposal_consistency_protected_strength`. The normal proposal-consistency strength can remain `0.0`, while samples routed to low-tail/focus classes interpolate toward the protected strength. Unit tests verify that non-protected samples keep the ungated proposal, while protected samples switch toward prior-supported paths.
- The first protected-proposal TEP run (`base strength=0.0`, `protected strength=0.50`, prior support mode) reaches `0.6337 +/- 0.0019` Macro-F1 and `0.6420 +/- 0.0022` balanced accuracy. It reduces the admission low-tail harm compared with global prior proposal gating (`-0.0457` vs `-0.0679` against the edge-pool certificate baseline), but it is still rejected for seed-level validation drop and low-tail class harm.
- Current conclusion: do not continue with global edge widening, globally guarded edge replacement, or one global path-proposal gate. Class-conditioned proposal gating is the right structural direction, but the next hard algorithmic change should estimate path-family quality per weak/focus class before choosing support mode and strength. This also gives a clean integration point for expert and LLM edges: external evidence should contribute to a class/fault-family certificate, not to a global candidate matrix.

Artifacts:

- `knowledge_exports/tep_gpi_smoke/summary.md`
- `knowledge_exports/tep_gpi_p50_e25/summary.md`
- `knowledge_exports/tep_gpi_salience_p50_e25/summary.md`
- `knowledge_exports/tep_gpi_pathaux005_p50_e25/summary.md`
- `knowledge_exports/tep_gpi_pathaux005_current_noprior_p50_e25/summary.md`
- `knowledge_exports/tep_gpi_pathaux005_coarse010_p50_e25/summary.md`
- `knowledge_exports/tep_soft_p50_e25/summary.md`
- `knowledge_exports/tep_gpi_pathaux005_p50_e40/summary.md`
- `knowledge_exports/tep_gpi_pathaux005_expert_prior0_p50_e25/summary.md`
- `knowledge_exports/tep_gpi_pathaux005_expert_cover020_p50_e25/summary.md`
- `knowledge_exports/tep_gpi_pathaux005_expertllm_cover020_p50_e25/summary.md`
- `knowledge_exports/tep_gpi_pathaux005_expert_dyncover005_p50_e25/summary.md`
- `knowledge_exports/tep_cls_k8/summary.md`
- `knowledge_exports/tep_cls_expcal/summary.md`
- `knowledge_exports/tep_cls_expllmc/summary.md`
- `knowledge_exports/tep_cls_k8_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_expcal_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_expllmc_s424344_gpu/summary.md`
- `knowledge_exports/tep_gpu_evidence_admission_summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_external_evidence_gpu_burden/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_gpu_algorithmic_path_candidate_summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_algorithmic_path_candidates_gpu_burden/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_cls_family3w025_s424344_gpu/summary.md`
- `knowledge_exports/tep_cls_family3w025_gate020_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_algorithmic_path_candidates_v2_gpu_burden/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_gpu_algorithmic_edge_prior_summary.md`
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
- `knowledge_exports/tep_algprior_edgesieve_directed_adaptiveprior_pathrel_f015_thr025_cover015_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_algprior_edgesieve_directed_softcover005_pathrel_f010_thr025_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgesieve_directed_edgecal_f005_b15_reg005_pathrel_cover010_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgeoverlay_directed_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_edgecal_f005_b15_reg005_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edge_initializer_broadening_lowtail_path_protected_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_edge_initializer_broadening_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/tep_edgepool_lowtail_path_evidcons_relative_s010_thr050_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_lowtail_path_evidcons_relative_s003_thr050_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_lowtail_saliencecover010_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_stablepath_s4_v075_w025_k8_edge4_classoff_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_path_evidence_consistency_relative_protected_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_lowtail_path_proposal_and_evidcons_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_stable_path_vs_saliencecover_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_path_evidence_consistency_relative_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_lowtail_path_proposal_and_evidcons_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_stable_path_vs_saliencecover_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/tep_edgepool_classcert_focusstable_f005_thr075_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/tep_edgepool_classcert_focusstable_f050_thr075_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_class_evidence_quality_certificate_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_class_evidence_quality_certificate_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/tep_edgepool_proposalcons_s050_retain050_thr035_f020_adaptiveprior_pathrel_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/tep_edgepool_stableclassoverlay_s025_k8g2_focus6_adaptiveprior_pathrel_cover020_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/tep_edgepool_stableclassoverlay_propagree_s025_thr035_f020_focus6_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_stableclass_overlay_agreement_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/tep_edgecertpool_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/tep_edgecertoverlay_anchor_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/tep_edgecertoverlay_twoprior_adaptiveprior_pathrel_f015_thr025_cover020_full_h64_e40_s424344_gpu/ms_gse_rpf_result_summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgecertpool_adaptiveprior_pathrel_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgecertoverlay_anchor_adaptiveprior_pathrel_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgecertoverlay_twoprior_adaptiveprior_pathrel_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_edgecertpool_adaptiveprior_pathrel_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_edgecertoverlay_anchor_adaptiveprior_pathrel_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_edgecertoverlay_twoprior_adaptiveprior_pathrel_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/ms_gse_rpf_summaries/tep_edgecertoverlay_candadmit_rel_f005_thr050_s050_adaptiveprior_pathrel_f015_thr025_cover020_summary.md`
- `knowledge_exports/ms_gse_rpf_summaries/tep_edgecertoverlay_candadmit_feature_rel_f005_thr050_s050_adaptiveprior_pathrel_f015_thr025_cover020_summary.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgecertoverlay_candadmit_rel_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_validation_admission/tep_edgecertoverlay_candadmit_feature_rel_admission/ms_gse_rpf_validation_admission.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_edgecertoverlay_candadmit_rel_audit/ms_gse_rpf_edge_audit.md`
- `knowledge_exports/ms_gse_rpf_edge_audit/tep_edgecertoverlay_candadmit_feature_rel_audit/ms_gse_rpf_edge_audit.md`
