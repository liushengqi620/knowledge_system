from __future__ import annotations

import argparse
import os
import textwrap
from pathlib import Path


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def render_package() -> str:
    return textwrap.dedent(
        """\
        # Final AAAI Paper Package

        Date: 2026-06-21

        ## Working Title

        Reliability-Calibrated Mechanism Evidence Fusion for Industrial Time-Series Fault Diagnosis

        ## Paper-Level Problem

        Industrial fault diagnosis needs mechanism knowledge, but real industrial logs usually lack interventional data. Control loops, delayed compensation, latent operating states, and sparse faults make it unsafe to treat correlations, expert relations, or LLM-generated edges as true causal effects.

        The paper therefore studies safe use of unreliable mechanism evidence under non-interventional industrial time series. The core object is candidate mechanism evidence, not a recovered true causal graph.

        ## Core Thesis

        A strong anchor model should remain the primary discriminator. Algorithmic lag/residual evidence, expert mechanism relations, and LLM-assisted mechanism verification act as challengers. A challenger may modify the anchor only after validation-benefit, low-tail, FAR/MAR safety, counterfactual, and source/complexity checks.

        ## Paper Contributions

        1. Problem reframing: mechanism fusion in observational industrial logs is formulated as falsifiable evidence admission rather than causal graph discovery.
        2. Evidence Reliability Estimator: the method learns when a candidate mechanism source is locally useful enough to correct the anchor prediction.
        3. Hierarchical edge admission: expert, LLM-assisted, and data-driven candidates are not injected as one mixed pool. They are probed by source family, target group, lag group, and finally single edge; only validation-admitted single edges can enter the deployed graph.
        4. Residual/path-gated mechanism intervention: graph evidence enters as a constrained residual verifier, attention bias, edge mask, channel-fusion gate, or path relation, not as unchecked all-edge smoothing.
        5. LLM as expert-graph conditional verifier: the LLM does not directly add final graph edges. It verifies expert edges or paths under class, regime, residual, and temporal-pattern conditions; its output is only a conditional gate feature until data support and reliability admission approve it.
        6. Multi-benchmark evidence: TEP validates mechanism diagnosis, SKAB validates native metric auditing and conservative LLM/expert-graph verification, Hydraulic validates near-ceiling non-degradation, and C-MAPSS validates original-task RUL transfer with cap/window repair while closing unsafe path fusion.

        ## Mathematical Core

        The manuscript should present the anchor/challenger formulation from `reliability_theory_model.md`: `p_0=f_0(x)` is the anchor; each candidate `k` produces `p_k=f_k(x,r,g,m)`; admitted evidence is `A={k: Delta M_k >= eta, Q_alpha(B_{g,k}) >= -epsilon, CF_k >= zeta, C_k <= c_max}`; the deployed predictor falls back to `p_0` unless an admitted challenger has sufficient local reliability `q_psi(i,k)`.

        The current edge-admission contract is stricter than the original mixed-pool design. Candidate evidence is frozen, screened by source family, target group, and lag group, and only then measured as single-edge challengers. Final `validation_admitted_edges` are materialized only from single-edge passes. Counterfactual sensitivity is evaluated after validation gain and low-tail/FAR/MAR safety, because CF can show dependence on a harmful edge but cannot prove task utility.

        `aaai_edge_admission_protocol_audit` now binds this story to executable artifacts. It reports `protocol_and_evidence_complete`: the reusable contract, relation interfaces, SKAB mechanism-gate matrix, a three-seed/full-row TEP hierarchical edge probe, and the full SKAB LLM-condition matrix are present. The measured TEP probe admits no single edge under the ordered validation-gain, FAR/MAR, and CF guards. The SKAB LLM matrix rejects independent LLM edges, LLM+expert correction, condition-verifier candidate gating, and weak-class condition verification under the same validation/low-tail guards. This supports reliability fallback rather than mixed-pool injection or unchecked LLM graph edits.

        ## Main Result Table

        | Dataset | Role | Main | Reliable/Proposed | Delta | Claim Level |
        |---|---|---:|---:|---:|---|
        | TEP | Primary 22-class mechanism-diagnosis benchmark | 0.9122 +/- 0.0134 | 0.9549 +/- 0.0023 | +0.0428 | strongest method evidence; SOTA candidate only under matched protocol |
| SKAB | Native anomaly/changepoint audit benchmark | 0.8193 +/- 0.0283 | 0.8450 +/- 0.0189 | +0.0257 | native-audited algorithmic anchor; LLM verifier remains diagnostic |
        | Hydraulic | Near-ceiling state-diagnosis safety benchmark | 0.9773 +/- 0.0321 | 0.9784 +/- 0.0301 | +0.0011 | non-degradation / supporting evidence |
        | C-MAPSS | Original terminal RUL transfer benchmark | GRU w80 cap125 RMSE 20.7559 | GRU w160 cap150 RMSE 18.0617; pseudo-terminal validation rerun RMSE 18.2840 | RMSE -2.6942 archived / -2.3982 validation-safe rerun | cap/window-corrected prognostics transfer evidence; path fusion closed |

        ## Final Reliability Ablation Table

        | Reliability Question | Dataset | Result | Paper Use |
        |---|---|---:|---|
| Native metric audit | SKAB | algorithmic anchor 0.8450 +/- 0.0189 vs strong anchor 0.8193 +/- 0.0283; LLM verifier 0.8209 +/- 0.0220 is not deployed as the accuracy branch | upgrades the safe SKAB result while keeping LLM evidence conditional/diagnostic |
        | Full LLM-condition matrix | SKAB | algorithmic-only 0.8450 +/- 0.0189; independent LLM 0.8208 +/- 0.0123; LLM condition gate 0.7981 +/- 0.0391; weak-class verifier 0.8265 +/- 0.0349 | full matrix rejects current LLM branches, so LLM evidence is diagnostic/conditional and not deployed |
        | Historical dense graph injection | SKAB | all-edge 0.8528 +/- 0.0322, delta +0.0185 +/- 0.0146 | retained only as historical matched evidence until rerun under the native-audit protocol |
        | Source/complexity penalty | SKAB | no-complexity 0.8234 +/- 0.0153 vs complexity-guarded 0.8261 +/- 0.0138 | shows source-family burden can be constrained without sacrificing accuracy |
        | Counterfactual edge structure | SKAB | CF 0.8798 +/- 0.0317 vs no-CF 0.8801 +/- 0.0317; CF-noCF -0.0003 +/- 0.0003 | supports CF as a reliability/interpretability guard, not a primary accuracy source |
        | Original-task correction | C-MAPSS | GRU w80 cap125 RMSE 20.7559 -> GRU w160 cap150 RMSE 18.0617; train-unit pseudo-terminal validation also selects w160/cap150 by RMSE with conservative rerun RMSE 18.2840; AnchorPath cap150 w80 RMSE 18.6666 is not admitted | keeps derived degradation labels auxiliary and reports the original RUL task while disclosing the PHM-score trade-off |
        | Edge gate replacement | TEP sequence family | edge-gate 0.5501 +/- 0.0089 vs reliability-pruned 0.5514 +/- 0.0109 | shows reliability is not just an internal gate |
        | Mechanism non-decoration | TEP strict 22-class | full 0.9549 +/- 0.0023 vs no expert/no sequence graph 0.7432 +/- 0.0102 | shows mechanism evidence changes decisions |

        ## Matched Backbone Negative Controls

        These rows are local matched-adapter controls, not official external paper scores. They are useful for the paper story because they show that simply importing a modern temporal or graph-temporal backbone is not enough under the current adapter protocols.

        | Backbone control | Protocol | Result | Claim Boundary |
        |---|---|---:|---|
        | PatchTST official-source adapted wrapper | TEP, seeds 42/43/44, 20k rows, 10 epochs | Target-F1 0.4197 +/- 0.0320 | official-source adapted matched control only |
        | Graph WaveNet official-source adapted wrapper | TEP, seeds 42/43/44, 20k rows, 10 epochs | Target-F1 0.2854 +/- 0.0529 | official-source adapted matched control only |
        | Anomaly Transformer official-source adapted wrapper | SKAB, seeds 42/43/44, validation threshold, no point adjustment | Macro-F1 0.4716 +/- 0.0487; FAR 38.34; MAR 63.29 | official-source adapted matched control only |

        The official comparison boundary is unchanged: PatchTST, Anomaly Transformer, and Graph WaveNet still require exact external repository/protocol/budget alignment before any public leaderboard wording. The manifest keeps these controls as `official_external_score=false`.

        ## Exact-Native Protocol Gate

        The new exact-native gate is stricter than the matched-protocol paper audit. It currently reports `official_sota_not_admissible`: TEP, SKAB, Hydraulic, and C-MAPSS can support the current matched-protocol method claims, but none should be described as official leaderboard SOTA until its native split, preprocessing, metric, threshold or delay policy, budget, baseline protocol, and seed-level artifacts are reproduced exactly.

        The paired exact-native execution plan now makes the next work concrete. SKAB is the first anomaly-detection target: separate outlier and changepoint scoring, freeze validation-only thresholds, keep point adjustment disabled unless reproducing that exact native rule, and rerun official/fair baselines under one event-window policy. C-MAPSS is the first prognostics target: preserve the NASA FD001-FD004 terminal RUL task, declare the RUL cap and train-only preprocessing, and align published RUL baselines before literature-wide claims.

        The P0 audit set is now materialized. `aaai_sota_gap_ledger` is the current numeric gap ledger: it records the matched improvements, keeps all official-native SOTA gates closed, and prioritizes SKAB and C-MAPSS as the next gate-closing datasets. `skab_official_baseline_gate` separates fair frozen-record USAD/TranAD-style controls from official-source adapted controls, official repository precomputed rows, and partial official source reruns. `skab_official_repository_baseline_audit` now aligns all 10 official SKAB result pickles to the raw data, recomputes the README outlier leaderboard rows such as Conv-AE (`F1 0.7838`, `FAR 13.55`, `MAR 28.02`), and materializes frozen JSONL prediction records; the official-source Anomaly Transformer wrapper also exports frozen prediction records. `skab_official_source_rerun_audit` reruns or preserves from the pinned official environment the implemented T2, T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE notebook/core logic, recomputing README rows (`T2 F1 0.6598`, `T2+Q F1 0.7581`, `Isolation Forest F1 0.2868`, `MSET F1 0.7800`, `Vanilla-AE F1 0.3938`, `Conv-AE F1 0.7842`) with frozen records. LSTM-AE (`F1 0.7515`), MSCRED (`F1 0.3382`), and Vanilla-LSTM (`F1 0.5111`) are also rerun with frozen records, but they do not match the official leaderboard within tolerance and therefore remain diagnostic rather than gate-closing evidence. `skab_source_rerun_delta_audit` now shows those unmatched source-rerun rows share identical keyed sample sets and labels with the official repository pickles, so the mismatch is attributed to prediction-level rerun variance rather than row alignment or label errors. The SKAB official-baseline gate still remains closed because ArimaFD is not fully rerun or formally scoped out and split/preprocessing/budget matching is not yet exact. `skab_native_metric_audit` is complete for the current proposed SKAB branches: frozen per-window prediction records, point Macro-F1/FAR/MAR, validation-only thresholds, and right-window changepoint event recall are all recomputable from the same seed artifacts. It now selects the `a0_algorithmic_only` branch as the current native-audited SKAB accuracy anchor (`Macro-F1 0.8450 +/- 0.0189`, CP recall about 0.9060), while the conservative LLM condition verifier remains a diagnostic branch (`0.8209 +/- 0.0220`) rather than the deployed accuracy branch. The audit also includes record-level USAD/TranAD-style three-seed negative controls under the same SKAB window policy; these are useful fair controls, but still not official repository reproductions. `cmapss_native_preprocessing_manifest` verifies the current FD001-FD004 terminal RUL records, RUL cap/window settings, subset RMSE/score rows, train-only preprocessing declaration, and seed-level prediction archives, so the C-MAPSS native preprocessing gate is now a pass. `cmapss_published_baseline_alignment` materializes the published-reference alignment table, local GRU/TCN/AnchorPath matched controls, and a three-seed LSTM published-style candidate (`RMSE 21.6521`, `score 9679.97`) for the LSTM RUL baseline family. `cmapss_published_baseline_contract` now turns the remaining published-baseline problem into a field-level exact reproduction checklist for LSTM, temporal CNN, attention-LSTM, MDFA 2025, and FD001-only CNN-LSTM references; it deliberately keeps published reproduction, published-baseline preprocessing equivalence, matched budget, and literature-wide SOTA gates closed until source-matched fields and archived predictions exist. `cmapss_lstm_source_protocol_audit` extracts the local LSTM candidate config (`window=80`, `cap=125`, `epochs=25`, `batch=256`, `hidden=64`, `layers=2`) and records that the IEEE full-text protocol is not available in the current environment, so source fields such as sensor selection, normalization, sequence policy, architecture, and budget remain unverified. `cmapss_open_protocol_candidate_audit` adds the next exact-source route: prioritize MDFA 2025 as an open full-text FD001-FD004 C-MAPSS candidate, with ACB 2021 as fallback if MDFA cannot be source-matched. `cmapss_mdfa_source_profile` now extracts MDFA window/batch/epoch/optimizer/dropout/source_2d dilation fields and reconciles FD001-FD004 raw-file counts with the MDFA published table, including FD004 train=249/test=248. `run_cmapss_mdfa_source_matched` now materializes a source_2d all-subset smoke archive with 707 terminal per-engine predictions (`RMSE 41.8246`, reduced one-epoch budget) and completed three-seed branch archives. The selected route keeps `window80/all24_pca/dropout0.1` for stable FD001, uses `window80/all24_pca/dropout0.0 + level_diff` for the FD003 two-fault subset, and uses `sensor21_pca + kmeans6_settings + condition_onehot` for FD002/FD004. Three-seed capped-test means are FD001 `RMSE 12.5498`, FD002 `RMSE 15.8410`, FD003 `RMSE 12.9260`, and FD004 `RMSE 15.9596`. New PCA-threshold sensitivity evidence shows that an all24 PCA threshold of `0.90` remains unsafe for multi-condition subsets (`FD002 RMSE 40.2631`, `FD004 RMSE 38.6818`), and raw-test auditing shows the current source-style cap policy is not yet exact-native for public C-MAPSS RUL scoring. This proves the runner/archive path, reduces the previous FD003 weakness by a small but stable three-seed level+first-difference temporal-channel gain, and gives a stronger route for multi-condition C-MAPSS, but it is still not a published reproduction or SOTA proof: the gate remains closed until PCA/key-sensor preprocessing, exact-source RUL-label policy, budget equivalence, and published baseline alignment are verified. `cmapss_rul_backbone_optimization_audit` records the cap=150 and window=160 improvement and keeps C-MAPSS path fusion closed until it beats the same-window temporal anchor. `cmapss_mdfa_strategy_probe_audit` now also includes validation-only affine output-calibration, checkpoint snapshot-ensemble, and level+first-difference temporal-channel probes: output calibration and checkpoint averaging remain blocked by the validation RMSE gain guard, FD001 regresses under the velocity channel, and FD003 receives only a small admitted local improvement rather than a SOTA-closing result. `cmapss_pseudo_truncation_validation_audit` uses train-split pseudo-terminal units to select the w160/cap150 temporal anchor by RMSE without test selection; it reports status `pseudo_truncation_validation_complete_with_score_tradeoff` because PHM score favors the w80/cap150 candidate on the official-test audit. `cmapss_exact_native_gap_audit` now separates score evidence from protocol evidence: native task/split/preprocessing/metric and seed archives pass, the MDFA local FD001-FD004 three-seed archive exists, and the MDFA external source-resolution rows confirm that hyperparameters, architecture, and key sensors are machine-readable while the PCA threshold and source code/package remain unavailable from the article page. Exact published reproduction, exact MDFA preprocessing/label policy, and matched budget remain blocked.

        | Dataset | Current safe claim | Official SOTA status |
        |---|---|---|
        | TEP | strict 22-class matched-protocol mechanism evidence | blocked by exact external split/preprocessing/metric/budget gates |
        | SKAB | native-audited anomaly/changepoint evidence | blocked by official split/preprocessing, repository-level baselines, and matched budget |
        | Hydraulic | near-ceiling non-degradation evidence | blocked by published four-target table and temporal baseline alignment |
        | C-MAPSS | original terminal RUL transfer evidence with long-window temporal anchor; native preprocessing gate passed; path fusion not admitted | blocked by exact published-baseline reproduction, published-baseline preprocessing equivalence, and matched budget |

        ## Efficiency Evidence

        | Dataset | Branch | Status | Params | Train seconds | Test samples/s | Paper Use |
        |---|---|---|---:|---:|---:|---|
        | SKAB | strong_anchor | measured, 3 seeds | 88716 | 340.54 | 2988.7 | formal anomaly anchor efficiency |
        | SKAB | llm_condition_candidate_gate | measured, 3 seeds | 88716 | 345.44 | 2939.9 | LLM verifier overhead check |
        | C-MAPSS | original_rul_anchor | measured, 3 seeds | 119183 | 62.84 | 9667.1 | terminal RUL anchor efficiency |
        | C-MAPSS | anchorpath_bigru_cls020 | measured, 3 seeds | 382162 | 147.46 | 8341.6 | path-fusion challenger efficiency; not admitted as current C-MAPSS main branch |
        | TEP | GDN20k no/residual | measured, 3 seeds | 17942 / 35885 | 0.47 / 0.63 | 586309.7 / 330096.4 | timed efficiency rerun; performance table uses best recovered row |
        | TEP | MTADGAT20k no/residual | measured, 3 seeds | 92055 / 184111 | 0.66 / 1.07 | 476639.1 / 254825.4 | timed efficiency rerun; performance table uses best recovered row |

        The current efficiency evidence is measured for SKAB, C-MAPSS, and the TEP GDN/MTAD sequence baselines. TEP timed reruns are used for efficiency, while the performance table preserves the best recovered target-F1 rows.

        ## SOTA Claim Boundary

        Safe claim:

        The method provides reliability-certified mechanism evidence fusion and strong matched-protocol method evidence across industrial benchmarks, with TEP as the primary positive mechanism-diagnosis result.

        Unsafe claim:

        The method is universal official SOTA on every benchmark. This should not be stated until exact external leaderboard reproduction is completed for each cited protocol.

        Dataset-specific wording:

        - TEP: strong strict 22-class matched-protocol evidence; official SOTA wording requires exact external protocol reproduction.
        - SKAB: native-audited conservative LLM/expert-graph verification evidence; official leaderboard wording requires repository/protocol/budget alignment.
        - Hydraulic: supporting non-degradation evidence near ceiling, not the main novelty benchmark.
        - C-MAPSS: original terminal RUL regression evidence with cap/window correction; train-unit pseudo-terminal validation supports the RMSE choice but discloses a PHM-score trade-off. Path fusion remains a closed challenger and literature-wide SOTA requires compatible published RUL baselines.

        ## Manuscript Section Plan

        1. Introduction: non-interventional industrial logs make causal-looking evidence unreliable.
        2. Problem formulation: candidate mechanism evidence, anchor/challenger prediction, and safe admission.
        3. Method: anchor model, mechanism candidates, Evidence Reliability Estimator, hierarchical edge admission, residual/path intervention, and LLM verifier.
        4. Theory/proposition: validation benefit, low-tail/FAR/MAR non-degradation, counterfactual relevance, and source complexity.
        5. Experiments: TEP main benchmark, SKAB reliability editing, Hydraulic safety, C-MAPSS original RUL transfer.
        6. Ablations: final reliability table, hierarchical edge admission, matched backbone negative controls, TEP mechanism table, sequence-family gate replacement, and source-pruning study.
        7. Limitations: no true causal discovery claim, protocol boundaries, and reliance on validation audits.

        ## Manuscript Assembly Checklist

        | Artifact | Use in paper |
        |---|---|
        | `knowledge_exports/aaai_latex_draft/main.pdf` | English AAAI-style compiled paper |
        | `knowledge_exports/aaai_latex_draft/main.tex` | English AAAI LaTeX source |
        | `knowledge_exports/manuscript_chinese_draft.md` | Chinese reading/writing draft aligned with the English AAAI LaTeX package |
        | `final_reliability_ablation_table.md` | Main reliability ablation table |
        | `reliability_theory_model.md` | Method equations and proposition wording |
        | `hierarchical_edge_probe_admission.md` | Candidate source-family, target-group, lag-group, and single-edge admission contract |
        | `tep_hierarchical_edge_validation_probe_smoke.md` | Measured hierarchical TEP edge-probe smoke evidence |
        | `tep_hierarchical_edge_validation_probe_3seed_fullrows.md` | Three-seed/full-row TEP hierarchical edge probe; ordered guards admit no single edge |
        | `aaai_edge_admission_protocol_audit.md` | Unified audit connecting hierarchical edge admission, TEP measured probes, LLM condition verification, and mechanism-gate controls |
        | `llm_condition_verifier_ablation_matrix.md` | Full SKAB LLM condition-verifier matrix showing current LLM branches are rejected by validation/low-tail admission |
        | `aaai_efficiency_audit.md` | Measured efficiency table and timing provenance |
        | `aaai_seed_level_ablation_evidence.md` | Copied seed-level metric/artifact ledger for completed ablation rows |
        | `aaai_ablation_coverage_audit.md` | Final-table ablation coverage gate |
        | `aaai_external_baseline_alignment_decision.md` | Claim-boundary gate for external baseline alignment |
        | `aaai_pending_baseline_gate.md` | No-pending-baseline gate with materialized official-source adapted controls |
        | `aaai_exact_native_protocol_gate.md` | Exact-native gate that keeps official leaderboard/SOTA wording disabled |
        | `aaai_exact_native_execution_plan.md` | Executable SKAB/C-MAPSS-first plan for closing exact-native SOTA gates |
        | `aaai_sota_gap_ledger.md` | Numeric gap ledger tying matched gains, MDFA source-style gaps, missing exact-native gates, and next gate-closing experiments together |
        | `skab_official_baseline_gate.md` | SKAB official/fair baseline gate; separates frozen fair controls from official-source controls and keeps official SOTA wording blocked |
        | `skab_official_repository_baseline_audit.md` | Official SKAB repository precomputed baseline audit; recomputes official README outlier rows from result pickles and materializes frozen prediction records without claiming source rerun |
        | `skab_official_source_rerun_audit.md` | Official SKAB notebook/core source rerun audit; matches T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE, records diagnostic LSTM-AE/MSCRED/Vanilla-LSTM reruns, and links their delta attribution while keeping ArimaFD explicit |
        | `skab_native_metric_audit.md` | Native SKAB metric readiness audit; complete for current proposed branches, with official/fair baseline alignment still outside this audit |
        | `cmapss_native_preprocessing_manifest.md` | Native C-MAPSS FD001-FD004 preprocessing/RUL evidence manifest |
        | `cmapss_published_baseline_alignment.md` | C-MAPSS published-reference alignment audit; local matched controls are materialized, while exact published reproduction and matched budget remain closed |
        | `cmapss_published_baseline_contract.md` | Field-level C-MAPSS published-baseline exact reproduction contract; prevents published-style rows from being treated as official SOTA evidence |
        | `cmapss_lstm_source_protocol_audit.md` | LSTM source-protocol audit; extracts local LSTM config and blocks exact reproduction until primary full-text fields are verified |
        | `cmapss_open_protocol_candidate_audit.md` | Open full-text C-MAPSS candidate audit; selects MDFA 2025 as the next exact-source target and ACB 2021 as fallback while keeping SOTA gates closed |
        | `cmapss_mdfa_source_profile.md` | MDFA 2025 source profile; reconciles FD001-FD004 raw-file counts and records the remaining runner/preprocessing/prediction blockers |
        | `cmapss_mdfa_runner_audit.md` | MDFA source-matched runner audit; smoke archive is materialized but full published reproduction remains blocked |
        | `cmapss_mdfa_strategy_probe_audit.md` | FD001-FD004 MDFA strategy-selection audit; long-window single-condition and condition-aware multi-condition archives are materialized while SOTA gates remain closed |
        | `cmapss_mdfa_source_matched_smoke_summary.md` | One-seed, one-epoch MDFA all-subset smoke summary; readiness evidence only, not a SOTA row |
        | `cmapss_lstm_published_style_w80_cap125_summary.md` | Three-seed LSTM published-style local candidate summary; not an exact published-baseline reproduction |
        | `cmapss_rul_backbone_optimization_audit.md` | C-MAPSS cap/window audit showing the current long-window temporal anchor and closing path fusion |
        | `cmapss_pseudo_truncation_validation_audit.md` | Train-unit pseudo-terminal validation audit for C-MAPSS cap/window selection and PHM-score trade-off disclosure |
        | `cmapss_exact_native_gap_audit.md` | Field-level C-MAPSS exact-native gap audit separating native-field passes, MDFA local archive evidence, MDFA external source-resolution evidence, and remaining published-protocol/budget blockers |
        | `run_public_ms_gse_rpf_experiment.py` | Main MS-GSE/RPF public benchmark runner; now exports classification prediction records for native SKAB metric recomputation |
        | `run_cmapss_rul_baselines.py` | C-MAPSS tabular, GRU, LSTM, and TCN terminal RUL baseline runner |
        | `run_cmapss_mdfa_source_matched.py` | Raw-file C-MAPSS MDFA source-matched candidate runner |
        | `skab_external_baselines.py` | USAD/TranAD/Anomaly-Transformer-style SKAB baseline runner; now exports frozen prediction records for native metric recomputation |
        | `skab_official_baseline_gate.py` | Recomputable SKAB official/fair baseline gate checker |
        | `skab_official_repository_baseline_audit.py` | Recomputable official SKAB result-pickle audit and frozen-record materializer |
        | `skab_official_source_rerun_audit.py` | Recomputable official SKAB source rerun and dependency readiness checker for matched T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, Conv-AE, diagnostic LSTM/MSCRED rows, and remaining ArimaFD/source protocol blockers |
        | `skab_source_rerun_delta_audit.py` | Frozen-record delta attribution audit showing unmatched LSTM-AE/MSCRED/Vanilla-LSTM source-rerun mismatches are prediction-level rather than row/label alignment errors |
        | `skab_native_metric_audit.py` | Recomputable SKAB native metric readiness checker |
        | `cmapss_native_preprocessing_manifest.py` | Recomputable C-MAPSS native preprocessing/RUL manifest checker |
        | `cmapss_published_baseline_alignment.py` | Recomputable C-MAPSS published-baseline alignment checker |
        | `cmapss_published_baseline_contract.py` | Recomputable C-MAPSS published-baseline contract checker |
        | `cmapss_lstm_source_protocol_audit.py` | Recomputable LSTM source-protocol audit for C-MAPSS exact reproduction |
        | `cmapss_open_protocol_candidate_audit.py` | Recomputable open-protocol candidate audit for selecting the next C-MAPSS exact-source reproduction target |
        | `cmapss_mdfa_source_profile.py` | Recomputable MDFA source profile and raw-count reconciliation checker |
        | `cmapss_mdfa_runner_audit.py` | Recomputable audit separating MDFA smoke readiness from full-budget published reproduction |
        | `cmapss_mdfa_strategy_probe_audit.py` | Recomputable FD001-FD004 MDFA strategy-selection audit for source_2d, feature policy, scheduler, validation split, long-window, and operating-condition probes |
        | `cmapss_rul_backbone_optimization_audit.py` | Recomputable C-MAPSS cap/window/path-fusion admission audit |
        | `cmapss_pseudo_truncation_validation_audit.py` | Recomputable C-MAPSS pseudo-terminal validation runner for RMSE-safe cap/window choice |
        | `cmapss_exact_native_gap_audit.py` | Recomputable C-MAPSS field-level exact-native blocker and MDFA source-resolution audit |
        | `aaai_edge_admission_protocol_audit.py` | Recomputable audit for the ordered edge/path-admission protocol |
        | `llm_condition_verifier_ablation_matrix.py` | Recomputable SKAB LLM condition-verifier ablation runner |
        | `run_patchtst_tep_official_wrapper.py` | Official PatchTST-source TEP adapter |
        | `run_graph_wavenet_tep_official_wrapper.py` | Official Graph WaveNet-source TEP adapter |
        | `run_anomaly_transformer_skab_official_wrapper.py` | Patched official-source Anomaly Transformer SKAB runner |
        | `paper_protocol_sota_audit.md` | External protocol/SOTA claim boundary |
        | `reference_verification_report.md` | BibTeX verification status and official-comparison claim limits |
        | `references.bib` | Draft bibliography consumed by the AAAI LaTeX package |

        ## Current Readiness Judgment

        The method and protocol core is paper-draft ready under a matched-protocol claim boundary. The English draft compiles cleanly under the official AAAI style, rendered PDF pages have been inspected, the Chinese reading draft is now regenerated as valid UTF-8 text, and the strongest external-source controls are materialized as non-official matched controls. The remaining blocker for the original long-term goal is exact native external protocol reproduction for public leaderboard/SOTA wording.
        """
    ).strip() + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render the final AAAI paper package summary.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = render_package()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(_fs_path(output), "w", encoding="utf-8") as handle:
        handle.write(report)
    print(report)


if __name__ == "__main__":
    main()
