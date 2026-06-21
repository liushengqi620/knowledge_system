# MS-GSE + RPF Algorithm and Experimental Protocol

## Positioning

The paper should not claim a stronger classifier. The core claim is a unified algorithmic evidence backbone for industrial multivariate time series. Given a causal window \(X_{t-L:t}\), the model predicts the task label and exposes three internal evidence objects:

\[
X_{t-L:t} \rightarrow (\hat y_t, A_t, \mathcal P_t, \rho_t)
\]

- \(\hat y_t\): fault/anomaly/component/degradation label.
- \(A_t\): sample-wise dynamic variable graph.
- \(\mathcal P_t\): selected variable evidence paths.
- \(\rho_t\): reliability score for each selected path.

Expert evidence and LLM-assisted evidence enter as edge/path priors. The pure algorithmic backbone remains complete without them, and priors must be validated by the learned graph and RPF rather than being hard-coded as final decisions.

## Current Implemented Backbone

Implemented files:

- `Scripts/ms_gse_rpf_model.py`
- `Scripts/run_public_ms_gse_rpf_experiment.py`
- `Scripts/test_ms_gse_rpf_model.py`

### 1. Multi-Scale Event Tokenizer

For each variable, depthwise temporal convolutions extract event tokens under multiple receptive fields:

\[
u_{i,t}^{(s)} = \text{DWConv}_{s}(x_{i,t-L:t})
\]

The model learns a scale gate:

\[
u_{i,t} = \sum_s \gamma_{i,t}^{(s)} u_{i,t}^{(s)}
\]

This is the implemented answer to abrupt changes, oscillations, and slow degradation. The `single_scale` ablation removes this contribution.

### 2. Dynamic Variable Graph

A directed graph is learned per sample:

\[
A_{ij,t} = \text{TopKSoftmax}(q_i^\top k_j)
\]

Rows represent target variables attending to source variables. The graph is sparse by construction and is later used both for graph-conditioned memory and path discovery. The `no_graph` ablation removes this contribution.

Knowledge graph priors can be injected as a weak score bias:

\[
A_{ij,t}=\text{TopKSoftmax}(q_i^\top k_j+\lambda B_{ij}),
\]

where \(B_{ij}\) comes from expert, LLM, or other candidate evidence edges. Setting \(\lambda=0\) keeps the prior only as a path feature; setting \(\lambda>0\) lets it bias graph search. This distinction is important because priors should remain falsifiable candidate evidence; old SKAB other-only runs suggested that hard expert bias can hurt, and the corrected full SKAB protocol must now rerun this comparison.

Train-only algorithmic priors now support several auditable initializers. `edge_bank` is the stricter version: instead of collapsing all statistics into one fused matrix first, each evidence source proposes edges independently, including temporal descriptor correlation, directed lag support, class-conditioned evidence, residual partial-correlation edges, fault-response ordering, and bootstrap stability. It records which sources voted for each final edge and can enforce a global edge budget such as \(4N\) edges for \(N\) variables. `edge_pool` is the wider version: it expands each per-source candidate list before final caps, keeps single-source dynamic candidates as weak edges, boosts multi-source agreement, and mixes raw score with rank consistency. This remains the strongest current TEP initializer because it improves recall without over-favoring generic consensus edges.

The new `edge_canvas` mode is a larger candidate-space overhaul rather than a simple top-\(k\) variant. It adds three additional algorithmic edge families: directed-lag asymmetry, innovation/shock propagation, and class-local lag dependency. It then separates structural, dynamic, and task evidence before final admission:

\[
B_{ij}
\leftarrow
\operatorname{Cap}\left(
s_{ij}\cdot a_{\text{vote}}(v_{ij})\cdot a_{\text{family}}(f_{ij})\cdot a_{\text{emergent}}(i,j)
\right),
\]

where \(s_{ij}\) mixes raw component score and component-rank agreement, \(v_{ij}\) is the evidence-source vote count, \(f_{ij}\) is the number of evidence families supporting the edge, and \(a_{\text{emergent}}\) prevents lower-vote dynamic/task edges from being completely suppressed by high-vote structural consensus. The first TEP screen shows this broader canvas is diagnostically useful but not a better default: raw `edge_canvas` reaches `0.6244 +/- 0.0037` Macro-F1, vote-saturated `edge_canvas` reaches `0.6311 +/- 0.0080`, exact duplicate path removal reaches `0.6234 +/- 0.0039`, and reducing prior coverage to 0.10 reaches `0.6225 +/- 0.0091`. Therefore the preferred interface for future expert and LLM evidence is still a wide-but-controlled candidate pool; the next innovation should be sample/class-aware admission over edge families, not another static global initializer.

The next implemented initializer is `edge_universe`. It broadens the edge pool, but changes the admission rule more substantially than `edge_canvas`: structural, dynamic, and task evidence are selected under separate family quotas before being merged into one prior. This prevents high-scoring generic correlation/residual edges from exhausting the global top-\(k\) budget before lag, innovation, fault-response, or class-local edges can enter RPF. It also exports the same three family prior matrices used by the edge-family router, so algorithmic, expert, and LLM evidence can later share one candidate-family interface. The first TEP h64/e40 screen is negative: `edge_universe + adaptive prior admission + bounded path reliability` reaches only `0.6240 +/- 0.0076` Macro-F1, and the validation certificate rejects it because mean validation gain is negative, one seed drops by `0.0293`, and low-tail per-class validation F1 drops by `0.1065`. A later global edge-quality threshold test, `edge_pool` with `pool_min_score=0.10`, is also negative (`0.6291 +/- 0.0035`) and is rejected with low-tail F1 gain `-0.1091`. This rules out a simple "make the initialized edge set larger" or "globally filter weak candidates" fix.

The latest initializer is `edge_lattice`. It first forms a direct edge universe, then expands candidate edges through explicit feature groups and a train-only feature-affinity neighborhood built from correlation, residual, lag, and stability components. This is meant to handle datasets such as TEP where variable names do not provide repeated statistic groups. It also exports a fourth `group_lattice` family for future evidence-family routing. Current TEP results are negative and clarifying: `edge_lattice + router/calibrator` reaches `0.6300 +/- 0.0015`, affinity-expanded `edge_lattice` with cover0.15 reaches `0.6278 +/- 0.0044`, and weak path-only lattice recall reaches `0.6235 +/- 0.0074`. The affinity version generates many raw candidate-only edges, but selected path salience drops from the current baseline's about `0.34` to about `0.05`. Therefore `edge_lattice` should be treated as a recall/audit universe. It should not bias \(A_t\) or consume RPF prior coverage unless a low-tail/class-evidence/path-stability certificate admits a compact core.

The model now supports that split explicitly: `prior_adjacency` can be a compact graph-core prior while `path_candidate_prior` can optionally hold a broader RPF candidate pool. The first `edge_lattice` certified-core TEP screen confirms the direction but rejects the current candidate as a main result. A separate-candidate version compresses roughly 252-256 lattice edges to 115 graph-core edges per seed but still reaches only `0.6238 +/- 0.0061`; a core-only version improves to `0.6304 +/- 0.0116`, but protected admission rejects it with negative validation gain and low-tail class harm. This shifts the next algorithmic target from edge initialization itself to path proposal/fusion: new paths with near-zero prior or salience should not displace baseline paths unless they pass class/low-tail-stable reliability evidence.

The newest edge-initializer rewrite makes that split sharper through `edge_cert_pool` and `edge_cert_overlay`. `edge_cert_pool` treats initialization as a mechanism ledger: structural, dynamic, and task families vote separately; each edge receives a certificate from vote support, family agreement, directed/stability evidence, and dynamic/task corroboration; reciprocal directions are pruned before final endpoint/group caps. This replacement-style prior is intentionally broad but fails TEP (`0.6247 +/- 0.0027`) because it replaces the baseline path set and harms low-tail classes. `edge_cert_overlay` keeps the `edge_pool` graph backbone and adds certified edges only as an overlay. Its final two-prior implementation uses the edge-pool base as `prior_adjacency` and sends the overlay matrix only to `path_candidate_prior`, so broader edges can be proposed by RPF without directly biasing \(A_t\). This is the right architectural shape, but the current global overlay is still rejected: it reaches `0.6311 +/- 0.0067`, with seed42 improving to `0.6404` but seed43/44 dropping and low-tail validation gain `-0.0862`. The conclusion is that broad candidate edges should be admitted by sample/class/fault-family certificates rather than exposed as one global candidate matrix.

The current code also exposes an edge-family router:

\[
w_t=\operatorname{softmax}(r_\theta(h_t)/T),
\qquad
B^{\text{fam}}_{ij,t} = \sum_m w_{t,m}B^{(m)}_{ij},
\]

where \(m\in\{\text{structural},\text{dynamic},\text{task}\}\). `--edge-family-router-blend` mixes this routed family prior with the original global prior before class-conditioned RPF admission. The training code also exposes `--edge-family-router-balance-weight`, a KL-to-uniform burden regularizer:

\[
\mathcal L_{\text{family-burden}}
=\lambda_f \frac{1}{B}\sum_t
\sum_m w_{t,m}\log \frac{w_{t,m}}{1/M}.
\]

This is the right architectural interface for later expert and LLM families, but current TEP results show it is not yet a safe default. On TEP h64/e40, `edge_canvas + family router` reaches `0.6259 +/- 0.0039`, `edge_pool + family router b0.50` reaches `0.6209 +/- 0.0058`, `edge_pool + family router b0.25` reaches `0.6211 +/- 0.0022`, and adding burden balance 0.05 reaches `0.6199 +/- 0.0042`, all below the `edge_pool + adaptive prior + bounded path reliability` result. The router learns family choices but does not transfer reliably to the official test split, and simple entropy/burden smoothing does not fix this. The next paper-worthy version should constrain family admission with validation-stable path families and low-tail class behavior rather than presenting the unconstrained router as the main algorithm.

The code now also exposes train-only cross-split stable path evidence. For split \(s\), class/lag evidence \(E^{(s)}_{cij}\) is rebuilt from the training subset only. The stability score is:

\[
\pi_{cij}=\frac{1}{S_c}\sum_s \mathbf{1}\left[E^{(s)}_{cij}>0\right],
\qquad
E^{\text{stable}}_{cij}
=\gamma\cdot \operatorname{Cap}_{k_e}\left(
\frac{1}{S_c}\sum_s E^{(s)}_{cij}\cdot \pi_{cij}\cdot
\mathbf{1}[\pi_{cij}\ge \tau_s]
\right),
\]

where \(\tau_s\) is `--stable-path-evidence-min-vote-fraction`, \(k_e\) is `--stable-path-evidence-edge-top-k`, and \(\gamma\) is `--stable-path-evidence-strength`. This is deliberately train-only, so it can be used later as an auditable algorithmic evidence channel alongside expert and LLM evidence. The first TEP probes are negative as a direct initializer: a dense version produced global evidence density `0.973` and seed42 `0.6314` Macro-F1, sparse edge-capped class filtering fixed density to `0.064` but stayed at `0.6319`, and weak class-off evidence reached `0.6384`, close to but still below the original seed42 `0.6398`. Therefore stable evidence should not be claimed as a standalone gain. Its correct role is as an input feature to a learned path/prior admission gate that decides when stability matters for the current sample.

The current implementation also includes `--use-stable-class-edge-overlay`, which overlays cross-split stable class evidence onto the initialized edge prior before path-family and graph-core certification. Its purpose is to test whether low-tail/fault-family stable edges should enter the candidate prior earlier than RPF path evidence. The TEP result is negative but useful: stable-class overlay with scale `0.25`, top-k `8`, group top-k `2`, and low-train-separation focus `6` reaches `0.6344 +/- 0.0032` Macro-F1, raises candidate-vs-baseline path Jaccard to `0.1875`, and is still rejected because validation and low-tail class behavior drop. Adding a path-proposal agreement gate lowers the result to `0.6300 +/- 0.0053`. This means the initialized edge set is not merely too narrow; stable low-tail edges also need sample/class-specific admission before they can occupy RPF path slots.

The first learned path-admission gate has also been implemented as an ablation:

\[
a_{p,t} = \eta \tanh g_\omega
\left(
z_{p,t}, h_t, z_{p,t}\odot h_t,
w^{\text{edge}}_{p,t},
w^{\text{prior}}_{p,t},
w^{\text{stable/task}}_{p,t}
\right),
\qquad
\alpha_{p,t}=\operatorname{softmax}(s_{p,t}+r_{p,t}+a_{p,t}).
\]

The last layer of \(g_\omega\) is zero-initialized, so enabling `--use-learned-path-admission` starts exactly neutral with gate mean `0.5` and zero adjustment. This is architecturally aligned with the desired story because it places admission inside RPF rather than adding an external classifier. However, the current TEP probe is a negative ablation: strength `0.75` with reg `0.002` drops seed42 to `0.6179`, and strength `0.20` with reg `0.02` drops to `0.6117`. The diagnostic mean admission adjustment remains large enough to overfit path logits while validation stays high. Therefore unrestricted end-to-end learned path admission should not be the next default. The paper-worthy direction is a constrained admission certificate or validation-admitted path-family selection, where learned gates are audited by low-tail and validation stability before deployment.

The validation-admission script now supports this certificate explicitly. With `--require-candidate-certificate`, each candidate family must clear mean validation gain, worst-seed validation drop, and low-tail per-class validation F1 harm before any per-seed admission decision can select it. The important point for the paper story is that wider initialization is no longer accepted just because it improves a mean validation score: a candidate edge/path family that damages weak fault classes is rejected before test reporting.

The protocol now also includes an explicit edge/path audit report through `summarize_ms_gse_rpf_edge_audit.py`. This is not another model component and not a classifier; it is the diagnostic layer that justifies which evidence families are allowed to become future model components. Given a baseline and candidate directories, the audit identifies validation-low-tail classes, reports candidate per-class F1 gains on those classes, measures top-path Jaccard, lists newly introduced candidate paths, and summarizes edge-source/family counts from the train-only prior. On current TEP h64/e40, the low-tail validation classes are `9`, `15`, `3`, `10`, `16`, and `0`. Failed candidates have very low path overlap with the strongest fixed baseline: `edge_universe` has path Jaccard `0.0364`, path-prior consistency `0.1154`, `class_blend` `0.0769`, global edge-pool min-score `0.0943`, and static-lag class evidence `0.0755`. This shows that these modules are not merely changing weights inside the same explanation set; they are replacing the path set in a way that hurts weak classes. The next algorithmic admission layer should therefore be low-tail protected: an edge/path family can alter RPF only if it preserves weak-class validation behavior and path stability.

The admission script now implements that path protection directly. For candidate \(m\), let \(J_m\) be the Jaccard overlap between the top-\(K\) group paths of candidate \(m\) and the baseline. The adjusted validation score can include a path-disruption burden:

\[
\operatorname{score}_m
=
\operatorname{ValF1}_m
- \lambda_s \operatorname{source\_burden}_m
+ \lambda_g \operatorname{GroupStability}_m
- \lambda_p(1-J_m).
\]

The certificate can also require \(J_m\ge J_{\min}\). This is not meant to freeze the baseline path set. A candidate with genuinely better validation and low-tail behavior can still pass with a different explanation set. The burden only prevents weak gains from replacing the RPF path set in a way that harms low-tail fault classes. The current TEP low-tail/path-protected report uses \(K=10\), \(\lambda_p=0.01\), and \(J_{\min}=0.05\); all tested edge/path/class-evidence candidates are rejected, with `edge_universe` additionally failing the path-overlap threshold. This turns the next main method into certified evidence admission over algorithmic, expert, and LLM proposals rather than unconditional graph injection.

The newest RPF module is deterministic path-prior consistency. It is not another classifier and it is not the failed free learned path gate. For each selected path \(p\), the prior weight \(b_p\) is admitted only in proportion to dynamic/salience support:

\[
g_p=\sigma\left((s^{dyn}_p-\tau_c)/T_c\right),
\qquad
\Delta_p=\lambda_c b_p(2g_p-1),
\qquad
\alpha_p=\operatorname{softmax}(q_p+r_p+\Delta_p).
\]

Here \(s^{dyn}_p\) is the dynamic graph/salience support for the path, \(b_p\) is the candidate-prior edge weight, and \(\Delta_p\) is bounded and deterministic. The first screen without class-conditioned evidence reached `0.6389 +/- 0.0080` Macro-F1, but that is not a strict comparison to the current class-evidence baseline. Under the strict class-conditioned protocol, `edge_pool + adaptive prior admission + bounded path reliability + path-prior consistency` with strength `0.25`, threshold `0.35`, and temperature `0.05` reaches `0.6368 +/- 0.0034` Macro-F1 and `0.6469 +/- 0.0027` balanced accuracy, roughly matching the previous strongest fixed candidate (`0.6361 +/- 0.0051`) with lower variance. The validation certificate still rejects it because mean validation gain is negative and low-tail per-class validation F1 drops by `0.0643`. A stricter `agreement` support mode, which uses \(\min(s^{dyn}_p,s^{class}_p)\), reaches only `0.6327 +/- 0.0020` and is also rejected. A softer `class_blend` support rule,

\[
s_p=s^{dyn}_p\left(\rho + (1-\rho)s^{class}_p\right),
\]

keeps a dynamic-support floor when class evidence is weak, but the first strict TEP run with \(\rho=0.25\) reaches only `0.6261 +/- 0.0069` and is rejected with mean validation gain `-0.0112`. Therefore the current evidence says path-prior consistency is a useful mechanism and story component, but the AAAI-ready version needs validation-guided low-tail safeguards rather than a fixed global support rule.

The next RPF-side module moves the same principle earlier, before paths are selected. `--use-path-proposal-consistency` gates the proposal scores used by the global, coverage, and prior path selectors:

\[
\hat a_{ij,t}
=a_{ij,t}\left((1-\eta)+\eta\left[\phi+(1-\phi)
\sigma\left(\frac{q_{ij,t}-\tau_q}{T_q}\right)\right]\right),
\]

where \(a_{ij,t}\) is the dynamic proposal score, \(q_{ij,t}\) is selected from prior support, class/salience support, their maximum, or an agreement rule, and \(\eta\) controls how strongly unsupported paths are downweighted. This is not a classifier and not a learned free gate; it is a deterministic candidate-selection constraint. On the current edge-pool/adaptive-prior/path-reliability TEP setting, `support=max(prior,salience)`, strength `0.50`, threshold `0.35`, and floor `0.20` reaches `0.6359 +/- 0.0015` Macro-F1, very close to the strongest fixed result while increasing selected salience mass to `0.4064` and sharply reducing seed variance. It is still rejected by the protected certificate because low-tail validation F1 remains slightly negative and top-path overlap is low. A weaker gate (`0.35`) is less stable, and a prior-only support rule drops to `0.6310 +/- 0.0052`. Retaining half of the ungated dynamic proposal slots improves top-path overlap to `0.0741` but only reaches `0.6344 +/- 0.0055`, and the stable-class overlay experiment confirms that higher overlap alone does not repair low-tail behavior. The algorithmic lesson is that proposal consistency is the right layer, but the final version should include sample/class-specific admission rather than one global support threshold or one global edge overlay.

Lagged class evidence was also re-tested inside the current edge-pool/adaptive-prior/path-reliability backbone. The conservative setting `static_lag`, max lag `3`, lag weight `0.25` reaches `0.6306 +/- 0.0061` Macro-F1 and `0.6453 +/- 0.0064` balanced accuracy. The certificate rejects it with mean validation gain `-0.0086` and low-tail F1 gain `-0.0740`. This means the class-evidence problem is not solved by simply adding temporal support to every class prototype. The class/fault evidence channel needs the same low-tail protected admission rule as algorithmic, expert, and LLM edge families.

Current TEP results show that this interface is useful for diagnosis but not yet a stronger default. Dense edge-bank priors over-admit pseudo-edges, sparse edge-bank priors improve but remain below the validation-admitted hybrid k16/baseline route, and dynamic-only edge-bank variants are still rejected by validation admission. A learned edge calibrator has also been implemented:

\[
\tilde B_{ij,t,c} = g_\theta(h_{i,t}, h_{j,t}, B_{ij}, z_c),
\]

where \(g_\theta\) is a sample/class-conditioned gate over candidate edges and \(z_c\) is optional class or fault-family context. RPF should receive \(\tilde B\), not the raw candidate bank. This keeps edge evidence falsifiable while allowing the model to reject globally plausible but sample-wrong edges.

The corrected identity-regularized TEP run keeps \(g_\theta\) near an identity mapping, reports a mean gate near 0.999, and is still rejected by validation admission. The wider `edge_pool` candidate improves over strict edge-bank but is also rejected unless combined with later path-level calibration, and even then it remains below the validation-admitted k16/baseline route. This means prior-matrix calibration should remain an ablation, not the default paper claim. The next algorithmic change should move calibration after RPF candidate construction: selected paths should receive class/sample-conditioned reliability calibration, so expert/LLM/algorithmic edges are judged as path evidence for the current sample rather than as globally correct adjacency entries. The current implementation exposes this through bounded path-reliability residuals controlled by `--path-reliability-context-scale`.

The first path-side prior admission module is now implemented. When `--use-class-conditioned-prior-admission` is enabled, the graph layer still receives the broad candidate prior, but RPF receives:

\[
B^{\text{RPF}}_{ij,t} = B_{ij} \cdot \left(\alpha + (1-\alpha)E_{ij,t}^{\text{class}}\right),
\]

where \(E_{ij,t}^{\text{class}}\) is the routed class-path evidence for the current sample and \(\alpha\) is `--class-prior-admission-floor`. This makes edge-pool initialization a candidate search space rather than a fixed global path budget. Current TEP results show the module is active: floor 0.15 filters too aggressively, while floor 0.50 is more stable but still below validation admission. The next version should replace fixed \(\alpha\) with learned sample-level reliability so the model can decide when to trust class-routed priors and when to fall back to dynamic paths.

The adaptive version now performs this reliability interpolation explicitly. With `--use-adaptive-prior-admission`, the class-router confidence \(c_t=\max_k p(k \mid X_t)\) defines a trust gate:

\[
\tau_t = \sigma \left((c_t-\delta)/T \right),
\]

and RPF receives:

\[
B^{\text{RPF}}_{ij,t}
= B_{ij}\left[1-\tau_t\left(1-\alpha-(1-\alpha)E_{ij,t}^{\text{class}}\right)\right].
\]

Low-confidence samples therefore remain close to the broad edge pool, while high-confidence samples use stronger class-filtered priors. In the current TEP screen, adaptive admission with \(\alpha=0.15\), \(\delta=0.25\), \(T=0.05\), and bounded path reliability is the strongest fixed candidate (`0.6361 +/- 0.0051` Macro-F1). It is not yet the validation-admitted default, but it is the clearest algorithmic direction for the paper backbone.

The latest candidate-prior revision makes this separation explicit. The model can receive a compact graph/RPF base prior \(B^{base}\) and a broader candidate prior \(B^{cand}\). With `--use-candidate-prior-admission`, candidates are not allowed to replace the base prior directly. Instead:

\[
G^{cand}_{ij,t}
=
\alpha_c + (1-\alpha_c)\sigma\left(
\frac{S_{ij,t}-\tau_c}{T_c}
\right),
\qquad
\bar B^{cand}_{ij,t}
=
\lambda_c B^{cand}_{ij}G^{cand}_{ij,t},
\]

where \(S_{ij,t}\) is routed class/path evidence, optionally normalized by the per-sample maximum. The admitted candidate layer can enter RPF in two places. `candidate_prior_admission_target=coverage` uses \(\max(B^{base},\bar B^{cand})\) for RPF prior coverage. `candidate_prior_admission_target=feature` keeps RPF coverage on \(B^{base}\) and uses \(\max(B^{base},\bar B^{cand})\) only as the selected-path prior feature. This dual-prior interface tests whether candidate edges fail by stealing path slots or because their evidence is itself misaligned.

The TEP result is negative but clarifies the next step. Coverage-target candidate admission improves seed42 but hurts seed43/44, reaching only `0.6316 +/- 0.0094` Macro-F1 and failing the certificate with mean validation gain `-0.0047` and low-tail F1 gain `-0.0819`. Feature-only admission is worse (`0.6284 +/- 0.0064`, low-tail gain `-0.1025`). Therefore the paper should not claim that a wider initialized edge set plus a generic evidence gate solves TEP. The useful architectural claim is narrower: graph priors, RPF coverage priors, and path-feature priors are now separable, and future expert/LLM/algorithmic candidates must pass class/fault-family path certificates before entering either coverage or prior features.

The latest implementation adds the missing middle ground: candidate edges can now enter RPF through an independent exploratory proposal quota instead of sharing the stable prior-coverage budget. `edge_dual_lattice` builds a stable `edge_pool` core and a wider `edge_lattice` exploratory layer. With `candidate_prior_admission_target=proposal_feature`, the base prior still controls normal RPF prior coverage, while admitted candidate edges use `--candidate-coverage-fraction` to reserve a small separate proposal budget and also appear as selected-path prior features. On TEP, using exact path de-duplication and candidate cover `0.08` reaches `0.6365 +/- 0.0018` Macro-F1 and `0.6480 +/- 0.0020` balanced accuracy, slightly above the fixed edge-pool/adaptive/path-reliability baseline (`0.6361 +/- 0.0051`, `0.6477 +/- 0.0044`). The validation certificate still rejects it because weak-class validation behavior is not consistently protected, so the next method step should be low-tail/class-aware candidate proposal admission rather than a broader global initializer.

The newest edge-initialization sweep makes that negative result sharper. Candidate-prior admission now supports a hard support floor and a protected-class support floor, but `edge_dual_lattice + min_support=0.50 + protected_min_support=0.70` reaches only `0.6364 +/- 0.0029` on TEP and is still rejected for seed-level validation drop and low-tail harm. A new `edge_guarded_lattice` mode was added to test a larger structural rewrite: the graph prior remains the compact `edge_pool` core, while the path-candidate prior is expanded through the mechanism-filtered `edge_sieve` rather than the unconstrained group lattice. This gives a cleaner candidate ledger but performs worse (`0.6279 +/- 0.0037`), showing that simply making the exploratory candidate layer more conservative removes useful signal. A global prior-based path-proposal gate also fails as a default: strength `0.50` improves some seeds but drops seed44, while strength `0.25` repairs seed44 and hurts seeds42/43. The implementation now includes a class-conditioned version, `path_proposal_consistency_protected_strength`, where proposal-consistency strength is interpolated only for samples routed toward low-tail/focus classes. This reduces certificate low-tail harm compared with global prior proposal gating, but the first TEP run still reaches only `0.6337 +/- 0.0019` and is rejected. The protocol conclusion is to keep `edge_dual_lattice + proposal_feature + min_support=0.50` as the best diagnostic branch for now, and to make the next architectural step a path-family certificate that learns which weak-class regimes should use strict prior/evidence agreement rather than applying one protected strength globally.

### 3. Graph-Conditioned Selective Memory

The model uses a selective state update over the window:

\[
h_{i,\ell} = z_{i,\ell} h_{i,\ell-1} + g_{i,\ell} \tilde h_{i,\ell}
\]

Then graph messages are injected:

\[
\bar h_{i,t} = h_{i,t} + \eta_{i,t} \sum_j A_{ij,t} W_m h_{j,t}
\]

This gives a Mamba-style selective memory without turning the contribution into a direct Mamba copy.

### 4. Optional Residual Evidence Injection

The selective memory states predict the current variable values. The absolute prediction residual is encoded as node-level surprise evidence and injected before path construction:

\[
r_{i,t}=|\hat x_{i,t}-x_{i,t}|.
\]

This makes reconstruction residuals part of the evidence state rather than a separate anomaly score. Initial SKAB matched runs did not show consistent macro-F1 gains, so this is kept as an optional variant rather than the default full model. The `with_residual_evidence` variant tests this contribution.

### 5. Reliable Path Fusion

The model selects candidate path tokens with a group-aware coverage router. Half of the path budget is assigned to globally strongest graph edges, and the other half is assigned to representative incoming edges from high-scoring feature groups. The coverage branch uses a soft redundancy penalty by default: paths already selected by the global branch are penalized before group representatives are chosen, but they are not mechanically forbidden. This matters empirically because hard de-duplication removes high-value repeated evidence on Hydraulic valve. Feature groups are inferred by removing only statistic suffixes, e.g., Hydraulic statistics `PS2_mean`, `PS2_std`, and `PS2_max` belong to the same sensor family `PS2`, while raw numbered variables such as `sensor_15`, `xmeas_01`, `xmv_04`, and `op_setting_1` remain distinct groups. This avoids path collapse on high-dimensional datasets where a pure global top-\(K\) selector can over-focus on a few high-variance columns, and it avoids over-collapsing raw sensors into one broad prefix group. A new candidate coverage mode, `group_pair_inclusive`, compresses the coverage branch at the source-group/target-group pair level while still allowing same physical-family statistic relations. It is intended for high-dimensional raw-sensor tasks and is being evaluated as a C-MAPSS/TEP path-compression candidate, not yet as the default. Each run reports `mean_path_duplicate_rate` so this coverage claim is auditable from the result JSON. Each path token contains source state, target state, state contrast, interaction, dynamic edge weight, and optional prior edge weight:

\[
e_k = f([h_s, h_d, h_d-h_s, h_s \odot h_d, A_{ds}, B_{ds}]).
\]

Fusion uses separated importance and reliability scores, but reliability is a calibrated residual term rather than a hard multiplicative penalty:

\[
\rho_k=\sigma(r_k), \quad
g=\text{softplus}(\eta), \quad
w_k = \text{softmax}(\alpha_k + g\tanh(r_k)).
\]

where \(\alpha_k\) is path importance, \(\rho_k\) is reported path reliability, and \(g\) is initialized near zero so reliability must be learned as a useful calibration signal. The `no_reliability` ablation sets this calibration to zero, while `no_path_fusion` removes path tokens entirely.

The current backbone further upgrades the path router from local-only scoring to context-routed evidence fusion. A global sample query is computed from the pooled variable state, and each selected path receives an additional compatibility term:

\[
q_t = f_q(\text{pool}_i h_{i,t}), \quad
c_k = f_c(e_k \odot q_t), \quad
w_k = \text{softmax}(\alpha_k + c_k + g\tanh(r_k)).
\]

This change is intended to fix a weakness observed in C-MAPSS and Hydraulic valve runs: path tokens were auditable, but their weights were not strongly conditioned on the full sample state. Result JSONs report `mean_path_context_importance`, and `--disable-context-router` provides the ablation against the previous local path router.

The model also exposes an auxiliary path-context task head. With `--path-aux-weight > 0`, the fused RPF path context must predict the task label directly:

\[
\mathcal L = \mathcal L_{\text{CE}}(\hat y,y)
  + \lambda_{\text{path}}\mathcal L_{\text{CE}}(\hat y_{\mathcal P},y)
  + \lambda_{\text{forecast}}\mathcal L_{\text{forecast}}
  + \lambda_{\text{graph}}\mathcal L_{\text{graph}}.
\]

This is not a separate classifier contribution. It is a supervision mechanism for the evidence path module: if selected paths cannot support the label, the auxiliary loss exposes that weakness during training. It should be evaluated with `--path-aux-weight` in a small grid such as `{0.05, 0.10, 0.20}` before being promoted to a final default.

Ordered lifecycle tasks such as C-MAPSS expose another failure mode: an observed lifecycle coordinate such as `cycle` can dominate RPF paths. The implementation now provides two explicit ablations:

- `--protect-order-anchor-target`: the order coordinate may be used as a source/context feature, but cannot be selected as an RPF target node.
- `--protect-order-anchor-path-nodes`: the order coordinate is kept in the temporal encoder and node context, but cannot appear as source, target, or bridge in selected evidence paths.

These switches separate lifecycle context from reported mechanism evidence. In current C-MAPSS seed42 screening, path-node protection produces cleaner sensor-to-sensor paths, but does not improve Macro-F1 enough to become a default. It should be reported as an interpretability/protocol diagnostic unless later validation admits it.

The C-MAPSS ready labels also include `rul`, so the backbone now exposes an optional health-index auxiliary head. With `--health-aux-weight > 0`, the script constructs

\[
h = 1 - \min(\mathrm{RUL}, C) / C,
\]

where \(C\) is `--health-rul-cap` and defaults to 125. The model predicts \(h\) from the shared node+path context:

\[
\mathcal L = \mathcal L_{\text{CE}}(\hat y,y)
  + \lambda_{\text{health}}\| \hat h - h \|_2^2
  + \cdots.
\]

This is a degradation-representation constraint rather than a new classifier. Current C-MAPSS screening shows that it can improve seed42 up to 0.7090 Macro-F1, but the three-seed mean is only 0.6869 +/- 0.0187 because seed44 collapses. Therefore health-index supervision is evidence that degradation representation matters, not yet a default main-result configuration.

C-MAPSS then exposed the more important failure mode: operating regimes confound raw sensor values, so RPF can learn paths that separate regimes or lifecycle coordinates instead of degradation residuals. The current backbone therefore includes an optional regime-aware prototype residualization stage:

1. cluster `op_setting_*` columns on the training split only;
2. estimate a healthy sensor prototype within each regime using training samples whose internal stage id is at most `--regime-healthy-stage-max`;
3. subtract that prototype from sensor channels while leaving `op_setting_*` and `cycle` available as context;
4. run the same MS-GSE + RPF backbone on the resulting residual sequence.

This is enabled by `--use-regime-prototype-residuals --regime-prototype-k K`. It is not a target-specific classifier: it is a train-only representation transform that makes the path-fusion module compare degradation residuals under comparable operating conditions. Under strict C-MAPSS official test and unit-disjoint validation, `group_pair_inclusive p50` improves from 0.6958 +/- 0.0032 Macro-F1 to 0.8105 +/- 0.0021. Adding `--protect-order-anchor-path-nodes` keeps `cycle` out of source, target, and bridge roles while retaining it as temporal context; this slightly lowers the mean to 0.8086 +/- 0.0041 but produces cleaner sensor-sensor evidence paths. This protected setting is the preferred paper configuration unless later SOTA comparisons require the unprotected high-score variant.

The Hydraulic valve seed42 fixed-budget check improves from 0.7193 Macro-F1 / 0.7205 balanced accuracy with calibrated global RPF to 0.8103 / 0.8224 after adding feature-group-aware coverage over 17 Hydraulic sensor families at `max_paths=16`. A later automatic 24-path budget check dropped this seed to 0.7339 / 0.7531, so the training script now respects the requested `--max-paths` by default and exposes `--auto-path-budget` only as an explicit ablation. The current fixed-budget three-seed result is 0.7088 +/- 0.0747 Macro-F1 and 0.7259 +/- 0.0700 balanced accuracy, so this component is not yet stable enough to be claimed as a final AAAI-level main result.

A group-pair coverage variant was also tested to force coverage over physical source/target group pairs. On Hydraulic valve seed42 it dropped to 0.6884 / 0.6916, so `target_group` remains the default `--path-coverage-mode` and `group_pair` is kept only as a negative ablation candidate. This is useful evidence: naive group-pair de-duplication can remove high-value feature-level paths, so the next optimization should use task-aware reliability admission rather than stronger static coverage constraints.

Optional train-only salience was then tested as a soft path evidence channel. Feature-only salience (`salience_selection_strength=0.0`) reached 0.7956 / 0.7943 on Hydraulic valve seed42. Soft proposal salience (`salience_selection_strength=0.05`) reached 0.8337 / 0.8494 on seed42 and improved the three-seed mean to 0.7360 +/- 0.0880 Macro-F1 and 0.7433 +/- 0.0941 balanced accuracy. It also increased group-level path stability from 0.0196 to 0.0809. However, seed44 still dropped to 0.6204 / 0.6207, so salience-RPF is a promising optimization direction rather than a final AAAI main result.

Hard coverage de-duplication was tested after this patch. It reduced duplicate rate to 0.0000 but dropped Hydraulic valve to 0.6569 +/- 0.0458 Macro-F1 and 0.6701 +/- 0.0471 balanced accuracy, so it is retained only as a negative ablation. The current default is soft redundancy (`--coverage-dedup-mode soft --coverage-redundancy-penalty 0.05`), which reaches 0.7098 +/- 0.0196 Macro-F1 and 0.7102 +/- 0.0179 balanced accuracy on Hydraulic valve with duplicate rate 0.3671. Validation-gated salience admission under the same soft redundancy protocol selects salience for seeds 42 and 43, falls back to baseline for seed44, and reaches 0.7564 +/- 0.0446 Macro-F1 and 0.7601 +/- 0.0499 balanced accuracy with duplicate rate 0.3304. This is the current strongest Hydraulic valve algorithm candidate, but it must still be validated on the other Hydraulic targets and public datasets before being used as a paper main result.

If an evidence prior exists for the path edge, its prior weight is appended to the path token. Thus expert and LLM suggestions are treated as candidate evidence to be accepted, down-weighted, or ignored by RPF.

### 6. Optional Train-Only Task Salience Evidence

A new optional path evidence channel computes group-level task salience from the training split only:

\[
s_i = \max_{j\in g(i)} \text{Norm}(\log(1+F_j)),
\]

where \(F_j\) is the train-only ANOVA class-separation score for feature \(j\), and \(g(i)\) is the physical feature group inferred from feature-name prefixes. For a path \(s\rightarrow d\), RPF receives an additional salience feature:

\[
\psi_{sd}=\max(s_s,s_d).
\]

This salience can be used in two modes:

- `--use-task-salience --salience-selection-strength 0.0`: salience is a path feature only.
- `--use-task-salience --salience-selection-strength 0.05`: salience softly changes path proposal scores before RPF fusion, without changing the dynamic graph itself.
- `--salience-mode class_lifecycle`: for ordered degradation tasks, combine train-only class separation with train-only lifecycle rank correlation as algorithmic path evidence.
- `--algorithmic-evidence-top-k`: keep only the top-k train-only evidence variables in the path evidence matrix. This is an explicit sparsity ablation, not the default.

This keeps the evidence boundary clean: the salience is learned only from training labels, is reported as `Salience mass`, and can be falsified by validation/test performance. It is not expert evidence and not LLM evidence; it is an algorithmic task-evidence channel.

Two additional degradation-task ablations are implemented:

- `--ordinal-loss-weight`: adds cumulative ordinal EMD loss for ordered stage labels.
- `--path-entropy-weight`: penalizes high RPF path-weight entropy to encourage sparse path fusion.

Initial C-MAPSS seed42 checks show that both are useful diagnostics but not current defaults: ordinal EMD with weight 0.20 drops a 25-epoch strict run to 0.6939 Macro-F1, and path entropy regularization with weight 0.005/0.020 drops to 0.6909 Macro-F1. This indicates that naive ordinal smoothing and forced low-entropy path attention can make the model too conservative or collapse paths prematurely. The current paper story should therefore emphasize validation-admitted evidence and learned path compression rather than mandatory hard constraints.

### 7. Validation-Gated Evidence Admission

The current admission rule is deliberately simple and auditable. For each seed/task, train the baseline RPF and each candidate evidence configuration. Select a candidate only when its validation metric improves over the baseline:

\[
k^\star = \arg\max_k [M_{val}(k)-B_k], \quad
\text{admit}(k^\star) \Leftrightarrow M_{val}(k^\star)-B_k \ge M_{val}(\text{baseline})+\epsilon.
\]

Here \(B_k\) is the candidate evidence burden. It is usually zero for train-only algorithmic salience, but positive for external expert/LLM priors because they add source complexity and a higher risk of spurious mechanism injection. The test split is read only after this validation decision. This is the same interface later used for expert and LLM evidence: external evidence is allowed to propose paths, but it must pass burden-aware validation admission before it is reported as adopted evidence.

Expert priors can optionally be expanded from exact feature edges to same-sensor statistic variants through `--prior-group-expansion`. This is deliberately not the default. On Hydraulic valve, group expansion increased mean prior mass to 0.0093 but reduced Macro-F1 to 0.6375 +/- 0.0495, so it is treated as a stress-test candidate with a larger burden rather than a default mechanism.

## Unified Public Benchmark Protocol

The same training script handles all public datasets:

```powershell
$env:PYTHONPATH='Scripts'
$env:KMP_DUPLICATE_LIB_OK='TRUE'
python -B Scripts\run_public_ms_gse_rpf_experiment.py --dataset all --variant full
```

Dataset-specific differences are limited to label column, grouping key, and task head:

| Dataset | Task | Window grouping | Label |
|---|---|---|---|
| TEP | 22-class fault diagnosis | `source_split, source_file` | `event_quality_class_id` |
| SKAB | binary anomaly detection | `run_id` | `anomaly` |
| Hydraulic | component state classification | cycle order | selected component target |
| C-MAPSS | degradation stage classification | `subset, split_role, unit` | `degradation_stage_id` |

For C-MAPSS, `cycle` is retained as an observed lifecycle coordinate. It is not treated as a hidden label proxy; it is part of the available engine trajectory and is also used by the knowledge graph as lifecycle evidence.

Split discipline is now part of the protocol and is written into each result JSON as `split_protocol`. Official public test splits are never used for validation admission. For C-MAPSS, validation is selected by engine group (`subset, unit`), so the same engine unit cannot appear in both train and validation. For TEP, validation is a tail time block from each training source file rather than a random row split, which avoids using interleaved windows from the same process trajectory as both train and validation evidence. SKAB remains run-level split by `run_id`; Hydraulic uses stratified row splits because each row is an independent operating cycle summary.

Hydraulic is implemented as four target runs:

- `cooler`
- `valve`
- `internal_pump_leakage`
- `hydraulic_accumulator`

## Required AAAI Experiments

### Main Results

Run full-budget multi-seed experiments for:

- `full` MS-GSE + RPF
- high-level SOTA baselines: GDN, MTAD-GAT, GCAD, TranAD, Anomaly Transformer, DCdetector, RTdetector, TimesNet/TimeMixer, MAAT or another Mamba/SSM anomaly variant
- existing anchor/residual results only as a legacy or efficiency reference, not as the main contribution

### Core Ablations

Run the unified ablation matrix:

```powershell
--variant full
--variant single_scale
--variant no_graph
--variant no_reliability
--variant no_path_fusion
--variant with_residual_evidence
```

The expected paper argument:

- `single_scale` tests whether abrupt/slow dynamics need multi-scale tokenization.
- `no_graph` tests whether variable propagation matters.
- `no_reliability` tests whether path reliability improves evidence stability beyond raw path attention.
- `no_path_fusion` tests whether node pooling is weaker than evidence paths.
- `with_residual_evidence` tests whether prediction residuals help as node-level surprise evidence.
- `--disable-context-router` tests whether sample-conditioned path routing improves over local path-token routing.
- `--path-aux-weight` tests whether direct path-context supervision makes selected evidence more task-predictive.
- `--protect-order-anchor-target` and `--protect-order-anchor-path-nodes` test whether lifecycle coordinates should be excluded from reported RPF evidence paths while remaining available to the temporal backbone.
- `--health-aux-weight` tests whether capped-RUL health-index supervision improves ordered degradation representation.

### Efficiency

Report:

- train seconds
- train samples/second
- inference seconds
- inference samples/second
- parameter count

The runner already writes these fields under `efficiency`.

For binary anomaly-detection tasks, the runner also tunes a positive-class threshold on the validation split and stores:

- `positive_threshold`
- `thresholded_val_metrics`
- `thresholded_test_metrics`
- `primary_test_metrics`

For multiclass tasks, `primary_test_metrics` is the standard argmax result.

### Path Evidence Evaluation

The runner writes `top_evidence_paths` by mapping internal `path_source` and `path_target` indices back to feature names. This supports:

- path sparsity
- path stability across seeds
- path overlap with expert mechanism edges
- path acceptance/rejection when LLM proposes candidates later

### LLM-Assisted Candidate Evidence

LLM evidence is implemented as a weak candidate edge generator, not as a classifier and not as a causal oracle. The API key must be provided through an environment variable such as `LLM_API_KEY` or `STEEL_LLM_API_KEY`; it is never written to source files or result JSON. The base URL and model can be provided through `LLM_BASE_URL` and `LLM_MODEL`.

Dry-run prompt generation:

```powershell
$env:PYTHONPATH='Scripts'
python -B Scripts\llm_public_benchmark_evidence.py `
  --dataset skab --target anomaly `
  --dry-run --max-edges 8 `
  --output-dir knowledge_exports\llm_evidence
```

Live candidate generation and graph merge:

```powershell
$env:PYTHONPATH='Scripts'
$env:LLM_API_KEY='<set outside the repository>'
$env:LLM_BASE_URL='https://api.n1n.ai/v1'
$env:LLM_MODEL='gpt-5.5'
python -B Scripts\llm_public_benchmark_evidence.py `
  --dataset skab --target anomaly `
  --max-edges 8 --merge-into-ready-graph
```

After merging, training can expose those edges to RPF as path features:

```powershell
python -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset skab --variant full --seeds 42 `
  --evidence-prior-mode llm --prior-strength 0.0
```

Use `--prior-strength 0.0` for the first reliability check. This keeps LLM edges as candidate path features only. Positive prior strength should be reported as a separate ablation because previous SKAB checks showed that hard graph bias can reduce performance.

## Current Smoke Evidence

The following run validates only pipeline completeness, not paper performance:

```powershell
python -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset all --variant full --seeds 42 `
  --window-size 8 --hidden-dim 8 --epochs 1 `
  --batch-size 64 --max-rows-per-split 64 `
  --graph-top-k 2 --max-paths 4 `
  --forecast-weight 0.0 --graph-weight 0.0
```

Observed smoke output:

| Dataset/target | Macro-F1 | Balanced accuracy |
|---|---:|---:|
| TEP | 0.0060 | 0.0318 |
| SKAB | 0.4149 | 0.4219 |
| Hydraulic/cooler | 0.2685 | 0.3167 |
| Hydraulic/valve | 0.1111 | 0.2188 |
| Hydraulic/internal pump leakage | 0.3789 | 0.4185 |
| Hydraulic/hydraulic accumulator | 0.1312 | 0.2344 |
| C-MAPSS | 0.3107 | 0.3889 |

These smoke numbers were generated before the stricter validation protocol. They remain pipeline checks only and must not be used as performance evidence.

These numbers are intentionally low-budget smoke values. They should not be used in the paper.

## SKAB Protocol Correction and Current Evidence

The SKAB loader has been corrected to use the full public dataset under `data/{anomaly-free,other,valve1,valve2}`. The previous ready file only covered the `other` group because normal Windows path traversal dropped deep subdirectories under the recovered workspace and the loader also filtered out `anomaly-free.csv` by filename. The corrected ready dataset contains 46,806 rows and 35 experiment runs:

| Group | Rows | Runs | Anomaly rows |
|---|---:|---:|---:|
| anomaly-free | 9,405 | 1 | 0 |
| other | 14,929 | 14 | 5,241 |
| valve1 | 18,160 | 16 | 6,309 |
| valve2 | 4,312 | 4 | 1,517 |

The following three-seed run is a historical corrected-protocol checkpoint from before the soft-redundancy RPF update. It is useful for diagnosis and comparison, but it is not the current main-paper result because the path-fusion standard has since changed:

```powershell
python -B Scripts\run_public_ms_gse_rpf_experiment.py `
  --dataset skab --seeds 42,43,44 --window-size 48 --hidden-dim 64 `
  --epochs 40 --batch-size 256 --max-rows-per-split 8000 `
  --graph-top-k 4 --max-paths 16 `
  --forecast-weight 0.01 --graph-weight 0.002 `
  --evidence-prior-mode none --prior-strength 0.0
```

Pre-soft-redundancy corrected SKAB full-protocol checkpoint:

| Dataset/target | Rows | Runs | Seeds | Prior | Macro-F1 | Balanced accuracy | Path Jaccard | Inference/s |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| SKAB anomaly | 46,806 | 35 | 3 | none | 0.8368 +/- 0.0238 | 0.8350 +/- 0.0254 | 0.4652 | 2,958.6 |

Top evidence paths from the corrected full run include:

- `Temperature -> Volume Flow RateRMS`
- `Accelerometer1RMS -> Volume Flow RateRMS`
- `Current -> Volume Flow RateRMS`
- `Accelerometer2RMS -> Accelerometer1RMS`
- `Accelerometer1RMS -> Accelerometer2RMS`

The current soft-redundancy SKAB result is reported in the cross-dataset summary below.

Corrected SKAB ablation evidence under the 46,806-row protocol:

| Variant | Seeds | Macro-F1 | Balanced accuracy | Path Jaccard | Interpretation |
|---|---:|---:|---:|---:|---|
| full | 3 | 0.8368 +/- 0.0238 | 0.8350 +/- 0.0254 | 0.4652 | calibrated reliability keeps accuracy while improving path stability |
| no_reliability | 3 | 0.8389 +/- 0.0266 | 0.8382 +/- 0.0283 | 0.2850 | similar accuracy, weaker path stability and no reliability score |
| no_path_fusion | 1 | 0.5493 | 0.5650 | n/a | path fusion is a major contributor |
| no_graph | 1 | 0.7155 | 0.7279 | n/a | dynamic variable graph is useful |
| single_scale | 1 | 0.7709 | 0.7679 | n/a | multi-scale event tokens are useful |
| with_residual_evidence | 1 | 0.8336 | 0.8381 | n/a | residual injection is not yet a default contribution |

Modern protocol cross-dataset summary after adding the prior interface:

| Dataset/target | Prior | Macro-F1 | Balanced accuracy | Notes |
|---|---|---:|---:|---|
| SKAB anomaly | soft redundancy | 0.8150 +/- 0.0257 | 0.8164 +/- 0.0246 | updated default; duplicate rate 0.4616 |
| SKAB anomaly | soft redundancy + validation-admitted salience | 0.8307 +/- 0.0141 | 0.8281 +/- 0.0164 | selects baseline for seed42 and salience for seeds 43/44; duplicate rate 0.4630 |
| SKAB anomaly | soft redundancy expert prior, \(\lambda=0\) | 0.8117 +/- 0.0297 | 0.8140 +/- 0.0260 | 3 seeds; prior mass 0.0208; useful but not admitted without source-burden gain |
| SKAB anomaly | soft redundancy + burden-aware salience/expert admission | 0.8307 +/- 0.0141 | 0.8281 +/- 0.0164 | expert burden \(B_k=0.01\); rejects tiny external-prior validation gains |
| SKAB anomaly | expert, \(\lambda=0\) | 0.8670 | 0.8657 | seed42; external edges as path features, prior mass 0.0153 |
| SKAB anomaly | expert+LLM, \(\lambda=0\) | 0.8670 | 0.8657 | seed42; same adopted prior path as expert-only |
| SKAB anomaly | expert+LLM, \(\lambda=0.1\) | 0.8376 | 0.8405 | seed42; weak graph bias hurts versus \(\lambda=0\) |
| TEP 22-class | group-pair RPF | 0.6140 | 0.6250 | seed42 strict screen; official test and blocked source validation, 8000 test rows |
| TEP 22-class | group-pair RPF + path auxiliary | 0.6214 | 0.6291 | seed42 current best TEP screen; path evidence needs task pressure |
| TEP 22-class | group-pair RPF + path auxiliary, current code rerun | 0.6051 | 0.6208 | no-prior control after auxiliary-head/prior-interface code changes; use to isolate current prior experiments |
| TEP 22-class | path auxiliary + coarse normal/fault auxiliary | 0.6049 | 0.6222 | coarse class-0/nonzero loss hurts; not a default |
| TEP 22-class | path auxiliary + expert prior feature | 0.6108 | 0.6278 | prior mass 0.0109; weak negative against no-prior path auxiliary |
| TEP 22-class | path auxiliary + fixed 20% expert/LLM prior coverage | 0.5976-0.5981 | 0.6101-0.6116 | prior mass rises to about 0.188 but fixed prior coverage causes negative transfer |
| TEP 22-class | path auxiliary + dynamic-gated 5% expert prior coverage | 0.6038 | 0.6190 | lower prior mass 0.0454, still below no-prior path auxiliary |
| TEP 22-class | class-conditioned evidence router | 0.6167 | 0.6282 | current-code positive; sample-level path evidence improves over current no-prior control |
| TEP 22-class | class router + calibrated expert prior | 0.6136 | 0.6266 | expert edges filtered 51 -> 36 by train-only lag support; safer than fixed coverage but not best |
| TEP 22-class | class router + calibrated expert+LLM prior | 0.6216 | 0.6282 | seed42 probe only; useful as a hypothesis but not stable enough for a main claim |
| TEP 22-class | GPU class-conditioned RPF, no external prior | 0.6095 +/- 0.0105 | 0.6185 +/- 0.0108 | three seeds; current safest TEP default under unified GPU screening |
| TEP 22-class | GPU calibrated expert prior | 0.6088 +/- 0.0120 | 0.6168 +/- 0.0127 | three seeds; prior mass 0.0284 but no mean gain |
| TEP 22-class | GPU calibrated expert+LLM prior | 0.6040 +/- 0.0119 | 0.6140 +/- 0.0134 | three seeds; external evidence is visible but hurts the mean |
| TEP 22-class | GPU burden-aware expert/LLM admission | 0.6097 +/- 0.0105 | 0.6195 +/- 0.0108 | selects baseline / expert+LLM / baseline; safety result, not a strong gain |
| TEP 22-class | GPU static-lag class evidence | 0.6071 +/- 0.0085 | 0.6162 +/- 0.0121 | directed lag evidence is implemented but does not improve the mean |
| TEP 22-class | GPU two-hop RPF paths | 0.6005 +/- 0.0205 | 0.6049 +/- 0.0255 | seed42 improves but seed44 collapses; needs admission, not a fixed budget |
| TEP 22-class | GPU burden-aware algorithmic path admission | 0.6098 +/- 0.0105 | 0.6199 +/- 0.0108 | selects baseline / static-lag / baseline; safe but tiny gain |
| TEP 22-class | GPU fault-family path prototypes | 0.6058 +/- 0.0151 | 0.6121 +/- 0.0155 | train-only family smoothing; helpful for some seeds but hurts seed44 |
| TEP 22-class | GPU fault-family prototypes + sample gate | 0.6074 +/- 0.0101 | 0.6142 +/- 0.0111 | sample-level admission improves seed43 but is not validation-selected |
| TEP 22-class | GPU global algorithmic edge prior, hybrid k=8 | 0.6051 +/- 0.0090 | 0.6132 +/- 0.0089 | graph bias alone is insufficient without path coverage |
| TEP 22-class | GPU global algorithmic edge prior, hybrid k=8 + 25% prior coverage | 0.6115 +/- 0.0119 | 0.6213 +/- 0.0105 | coupling initialized edges with RPF path candidates gives a small gain |
| TEP 22-class | GPU global algorithmic edge prior, hybrid k=16 + 25% prior coverage | 0.6155 +/- 0.0055 | 0.6229 +/- 0.0088 | current best algorithmic edge-prior screen; wider edge bank improves stability |
| TEP 22-class | GPU global algorithmic edge prior, hybrid k=16 + 25% prior coverage, strength 0.10 | 0.6125 +/- 0.0047 | 0.6239 +/- 0.0046 | stronger graph bias is not better; keep prior strength mild |
| TEP 22-class | GPU stability-aware edge-prior admission | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | selects edge-bank candidates by validation gain, strength burden, and group-path stability |
| TEP 22-class | GPU unified algorithm/expert/LLM admission | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | evaluates algorithmic, expert, and LLM candidates together; source burden rejects external candidates in this screen |
| TEP 22-class | GPU corroborated expert+LLM + algorithmic prior | 0.6106 +/- 0.0053 | 0.6226 +/- 0.0055 | dampens external-only edges and boosts train-corroborated overlap; still below pure algorithmic edge-bank admission |
| TEP 22-class | GPU unified admission including corroborated expert+LLM | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | corroborated expert+LLM is proposed but rejected; selected source-family counts remain algorithmic: 3 |
| TEP 22-class | GPU expert+LLM anchored algorithmic subgraph | 0.6121 +/- 0.0070 | 0.6214 +/- 0.0097 | external endpoints focus the algorithmic bank and improve path stability, but accuracy remains below pure algorithmic admission |
| TEP 22-class | GPU unified admission including anchored expert+LLM | 0.6191 +/- 0.0072 | 0.6269 +/- 0.0100 | anchored expert+LLM is proposed but rejected; selected source-family counts remain algorithmic: 3 |
| TEP 22-class | GPU full-row h64/e40 class-conditioned baseline | 0.6252 +/- 0.0129 | 0.6438 +/- 0.0118 | stronger budget improves TEP substantially without algorithmic prior |
| TEP 22-class | GPU full-row h64/e40 hybrid edge prior k=8 | 0.6262 +/- 0.0050 | 0.6443 +/- 0.0056 | stable but only slightly above the full-row baseline |
| TEP 22-class | GPU full-row h64/e40 hybrid edge prior k=16 | 0.6283 +/- 0.0125 | 0.6487 +/- 0.0080 | best fixed full-row edge bank but still seed-sensitive |
| TEP 22-class | GPU full-row h64/e40 admission over baseline/k8/k16 | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | strongest current TEP result; validates candidate admission over fixed edge injection |
| TEP 22-class | GPU full-row h64/e40 multiview edge prior k=16, group cap 4 | 0.6156 +/- 0.0079 | 0.6354 +/- 0.0043 | broad edge sources with hard group cap are rejected by validation |
| TEP 22-class | GPU full-row h64/e40 multiview-light edge prior k=16 | 0.6158 +/- 0.0077 | 0.6351 +/- 0.0062 | hybrid-dominant multiview restores edge density but still underperforms; global prior coverage is the bottleneck |
| TEP 22-class | GPU full-row h64/e40 admission incl. multiview variants | 0.6335 +/- 0.0090 | 0.6502 +/- 0.0080 | rejects both multiview candidates and preserves the previous baseline/k16 admission decision |
| TEP 22-class | GPU full-row h64/e40 class-evidence salience coverage 0.25 | 0.6155 +/- 0.0033 | 0.6335 +/- 0.0021 | sample-level evidence coverage works technically but broad class evidence is still too noisy |
| TEP 22-class | GPU full-row h64/e40 salience coverage + router top1 + aux 0.05 | 0.6146 +/- 0.0030 | 0.6359 +/- 0.0009 | sharp supervised router still fails, so prototype quality is the bottleneck |
| Hydraulic cooler | soft redundancy | 0.9994 +/- 0.0009 | 0.9994 +/- 0.0009 | updated default; duplicate rate 0.3257 |
| Hydraulic valve | soft redundancy | 0.7098 +/- 0.0196 | 0.7102 +/- 0.0179 | updated default; duplicate rate 0.3671 |
| Hydraulic valve | soft redundancy + validation-admitted salience | 0.7564 +/- 0.0446 | 0.7601 +/- 0.0499 | selects salience for seeds 42/43 and baseline for seed44; duplicate rate 0.3304 |
| Hydraulic valve | burden-aware salience/expert admission | 0.7641 +/- 0.0350 | 0.7738 +/- 0.0335 | selects salience for seeds 42/43 and exact expert for seed44 |
| Hydraulic valve | expert group-expanded prior | 0.6375 +/- 0.0495 | 0.6550 +/- 0.0358 | stress test; prior mass 0.0093 but lower accuracy |
| Hydraulic internal pump leakage | soft redundancy | 0.9790 +/- 0.0118 | 0.9792 +/- 0.0116 | updated default; duplicate rate 0.3771 |
| Hydraulic accumulator | soft redundancy / validation-admitted baseline | 0.9327 +/- 0.0078 | 0.9339 +/- 0.0052 | salience is rejected for all seeds; duplicate rate 0.3832 |
| C-MAPSS stage | strict unit-val soft redundancy | 0.6860 +/- 0.0236 | 0.6811 +/- 0.0242 | official test + unit-disjoint validation; still below target |
| C-MAPSS stage | regime residual + group-pair RPF | 0.8105 +/- 0.0021 | 0.8097 +/- 0.0017 | train-only operating-regime healthy prototypes; strongest current score |
| C-MAPSS stage | regime residual + protected evidence paths | 0.8086 +/- 0.0041 | 0.8073 +/- 0.0041 | keeps `cycle` as context but removes it from RPF source/target/bridge roles |

This result supports the paper story: expert/LLM evidence should be treated as falsifiable candidate priors, not as forced graph structure. In the older corrected SKAB run, \(\lambda=0\) preserved performance and exposed one adopted expert path, while \(\lambda=0.1\) degraded the seed42 result. These expert/LLM rows still need to be rerun under the updated soft-redundancy RPF before entering the final main table. The framework exposes whether external evidence is adopted through `mean_path_prior_weight`. The Hydraulic update is now complete for all four component targets under the same soft-redundancy protocol: cooler and internal pump leakage are strong, accumulator is strong after rejecting salience, and valve remains the hardest target where burden-aware evidence admission is needed. The Hydraulic accumulator update gives the same lesson for algorithmic salience: train-only salience reaches only 0.8978 +/- 0.0103 Macro-F1, while the baseline reaches 0.9327 +/- 0.0078, so validation admission correctly rejects salience for all three seeds.

C-MAPSS is now the clearest evidence that the method must be presented as a full algorithmic pipeline rather than a classifier replacement. After switching to official-test and unit-disjoint validation, the broad-prefix sensor grouping baseline reaches 0.6860 +/- 0.0236 Macro-F1. The feature grouping bug was fixed so raw numbered variables (`sensor_15`, `xmeas_01`) remain distinct groups, but seed42 probes show that a 24-path budget is too small for 25 C-MAPSS groups (0.6899 Macro-F1, duplicate rate 0.4297) and 50 target-group paths only partly recovers performance (0.6975 Macro-F1). The `group_pair_inclusive` compression mode with hard coverage de-duplication reaches 0.6958 +/- 0.0032 Macro-F1 over three seeds. Context-routed RPF, path-auxiliary supervision, ordinal loss, path entropy, and health-index supervision all identify useful diagnostics but do not solve the task. The decisive change is regime-aware prototype residualization before RPF: it reaches 0.8105 +/- 0.0021 Macro-F1, and the path-node-protected version still reaches 0.8086 +/- 0.0041 while producing cleaner sensor-level evidence. The remaining C-MAPSS problem is no longer raw accuracy under this protocol; it is cross-seed path stability and comparison against modern deep time-series SOTA.

TEP remains the main unresolved dataset under the updated backbone. The strict 22-class seed42 screen reaches 0.6140 Macro-F1 with `group_pair_inclusive` hard de-duplicated paths and 0.6214 with a path auxiliary loss of 0.05 in the earlier artifact. A current-code no-prior rerun reaches 0.6051, so later prior-coverage experiments should be compared against that current-code control as well as the historical best screen. Train-only class salience, a coarse class-0/nonzero auxiliary loss, and fixed expert/LLM prior coverage are all negative. The prior-coverage experiments are especially diagnostic: forcing prior paths raises `mean_path_prior_weight` from about 0.01 to about 0.19 but lowers Macro-F1, so the problem is not simply that expert/LLM edges are absent from the graph. The updated GPU three-seed follow-up changes the TEP conclusion: algorithm-only class-conditioned RPF reaches 0.6095 +/- 0.0105 Macro-F1, calibrated expert prior reaches 0.6088 +/- 0.0120, and calibrated expert+LLM prior reaches 0.6040 +/- 0.0119. Burden-aware validation admission rejects most harmful external evidence and reaches 0.6097 +/- 0.0105, but this is only a safety result. A new train-only directed lag-evidence mode and existing two-hop RPF path compression were then tested. Both expose useful seed-level signals, but neither is stable when globally enabled: static-lag evidence reaches 0.6071 +/- 0.0085, and two-hop paths reach 0.6005 +/- 0.0205. Burden-aware algorithmic admission recovers to 0.6098 +/- 0.0105 by selecting baseline/static-lag/baseline across seeds, again showing safety rather than a decisive gain. The latest completed positive update implements train-only fault-family path prototypes, sample-level class-evidence admission, and a global hybrid algorithmic edge prior built from correlation, directed lag support, and class-conditioned fault evidence. The edge prior is useful only when it also changes RPF path candidates: hybrid k=16 with 25% prior coverage reaches 0.6155 +/- 0.0055 Macro-F1, while graph bias alone reaches only 0.6051 +/- 0.0090. The new stability-aware admission route selects edge-bank candidates by validation gain, strength burden, and group-path stability, reaching 0.6191 +/- 0.0072 Macro-F1 in the 8000-window screen. Full-row h64/e40 training raises the baseline to 0.6252 +/- 0.0129, and validation admission over baseline/k8/k16 reaches 0.6335 +/- 0.0090, which is the strongest current TEP result. The unified algorithm/expert/LLM route keeps expert and LLM evidence in the candidate set but rejects them after source burden in this screen, with selected source-family counts `algorithmic: 3`. A stricter corroborated expert+LLM fusion dampens external-only edges and boosts train-corroborated overlap edges, but still reaches only 0.6106 +/- 0.0053 Macro-F1 because calibrated external edges overlap only about 19-21 of the 803 algorithmic prior edges. The anchored-subgraph variant treats expert/LLM endpoints as mechanism anchors and downweights non-anchor algorithmic edges; it improves external-candidate path stability but still reaches only 0.6121 +/- 0.0070 Macro-F1 and is rejected by unified admission. Per-class diagnostics show that several faults are nearly solved, while classes 21, 9, 13, 15, 3 and the normal class remain weak. This indicates that TEP needs validation-aligned edge-bank/fault-family routing and group-stability admission rather than a generic auxiliary classifier, unconditional expert/LLM admission, unconditional lag/two-hop injection, or test-set-based candidate choice. The full-row multiview test strengthens this conclusion: adding residual partial-correlation, fault-response ordering, bootstrap-stability voting, and group-level edge caps does not help when those edges are still admitted as one global prior. Hard group capping is too sparse (`0.6156 +/- 0.0079`), and hybrid-dominant light multiview restores edge density but remains weak (`0.6158 +/- 0.0077`). RPF now has a sample-level salience coverage mechanism that can reserve path slots for class evidence without a static global prior, but broad all-class evidence remains weak (`0.6155 +/- 0.0033`). Sharp, supervised class-evidence routing also remains weak (`0.6146 +/- 0.0030`), ruling out simple softmax dilution as the main cause. The latest edge-initializer widening adds `edge_sieve` and `edge_overlay`: the former builds a wide stability/direction-filtered candidate canvas and the latter preserves edge-pool while adding non-replacing sieve candidates. Both are useful diagnostics but not defaults. Full-row h64/e40 TEP reaches only `0.6285 +/- 0.0068` for `edge_sieve`, `0.6321 +/- 0.0048` for `edge_sieve + edge_calibrator`, `0.6303 +/- 0.0019` for `edge_overlay`, and `0.6307 +/- 0.0072` for `edge_pool + edge_calibrator`, all below the current fixed baseline `0.6361 +/- 0.0051`. Protected admission rejects them due to validation loss, seed drops, and low-tail class harm. The follow-up low-tail path experiments confirm the same bottleneck. A new deterministic path-evidence consistency adjustment can operate independently of prior coverage and supports relative selected-path evidence normalization, but relative settings reach only `0.6277 +/- 0.0039` at strength `0.10` and `0.6304 +/- 0.0029` at strength `0.03`. Reserving 10% of path proposals for class evidence reaches `0.6309 +/- 0.0010`; weak cross-split stable path evidence reaches `0.6340 +/- 0.0073` with seed42 improvement but seed44 regression. Protected admission rejects all three because validation and low-tail classes still drop. A first class-evidence quality certificate then uses cross-split stability only as a filter and does not inject stable paths (`path_mode=off`, `class_mode=off`), but floor `0.05` reaches only `0.6263 +/- 0.0064` and floor `0.50` reaches `0.6266 +/- 0.0032`; both are rejected with low-tail harm and candidate-vs-baseline path Jaccard near `0.095`. The latest retention and stable-overlay checks reinforce the same conclusion: proposal retention raises path Jaccard but remains below the baseline, stable-class edge overlay raises path Jaccard to `0.1875` but still hurts low-tail classes, and overlay plus agreement gating is worse. Therefore the next algorithmic step should construct a train-only low-tail/fault-family path-family certificate before evidence can alter path proposals or path weights, so multiview, expert, and LLM evidence propose mechanisms for specific weak fault regimes rather than occupying RPF coverage globally.

## Next Optimization Targets

1. Add path stability metrics across seeds and bootstrap windows.
2. Add a stronger training schedule: larger hidden dimension, longer epochs, warmup, early stopping, and per-dataset window sizes.
3. Add official SOTA baseline runners or adapters.
4. Add expert and LLM candidate edge injection as priors into \(A_t\) and reliability features, without changing the algorithmic backbone.
5. Build the AAAI paper tables from result JSON only after full-budget runs finish.
