# AAAI Completion Matrix

Date: 2026-06-21

This matrix tracks the work required to turn the project into a submission-grade AAAI paper package. It uses the current artifacts as evidence and keeps a strict boundary between matched-protocol method evidence and official leaderboard/SOTA claims.

## 1. Problem and Story

| Item | Current Evidence | Status | Remaining Gate |
|---|---|---|---|
| Core problem | `final_aaai_paper_package.md`, `aaai_latex_draft/main.tex`, and `manuscript_chinese_draft.md` consistently frame the task as safe use of unreliable candidate mechanism evidence under non-interventional industrial logs | closed | Keep this wording in every final manuscript export |
| Causality boundary | Goal audit marks claim boundary satisfied; forbidden overclaim phrases are absent from the audited package | closed | Do not reintroduce true-causal-graph or universal official-SOTA wording |
| Paper story | Anchor/challenger formulation, ERE admission, residual/path intervention, expert evidence, and LLM verifier roles are described in the English LaTeX draft and Chinese draft | closed for draft | Polish prose after external baseline alignment decisions |
| Bilingual deliverables | English AAAI LaTeX package exists under `aaai_latex_draft`; Chinese reading draft exists as `manuscript_chinese_draft.md`; `main.pdf` compiles cleanly | draft-ready | Final bilingual polishing still needed after baseline-alignment decisions |

## 2. Method and Algorithm Backbone

| Item | Current Evidence | Status | Remaining Gate |
|---|---|---|---|
| Reproducible admission algorithm | `aaai_goal_completion_audit.json` marks `reproducible_algorithm` satisfied; `main.tex` includes Algorithm 1, threshold grids, frozen deployment tuple, and validation-only rule | closed | Keep manifest synchronized if thresholds or candidate construction change |
| Difference from attention/gates/pruning | Goal audit marks the distinction satisfied | closed | Preserve this distinction in final rebuttal-ready wording |
| LLM role | Current method describes LLM as weak-class mechanism proposer / expert-graph conditional verifier rather than final independent edge source | closed for current branch | A positive LLM-gain branch remains optional; current evidence supports reliability/safety use |
| Path fusion standard | Final package presents admitted challenger fusion through global certificate plus local ERE routing | closed for draft | If a stronger path-fusion variant is added, rerun coverage and goal audit |
| Candidate edge admission order | `hierarchical_edge_probe_admission.*` freezes expert/LLM candidates, defines source-family/target-group/lag-group/single-edge probes, and enforces validation-gain plus low-tail/FAR/MAR safety before CF guard; `tep_single_edge_validation_probe_smoke.*` verifies the measured order on 6 TEP expert candidates and admits 1 single edge; `tep_hierarchical_edge_validation_probe_smoke.*` measures source-family, target-group, lag-group, and single-edge probes over 50 TEP candidates, with group probes treated as screening diagnostics and final admitted edges still restricted to single-edge passes | closed for algorithm contract plus measured smoke evidence | Run full multi-seed single-edge and group-level validation probes before claiming specific admitted edge gains |

## 3. Experiments and Main Evidence

| Dataset | Current Evidence | Status | Remaining Gate |
|---|---|---|---|
| TEP | Strict 22-class mechanism result `0.9549 +/- 0.0023`; matched TCN/GRU/FT/GDN/MTAD-GAT-style baselines and efficiency rows exist | strongest method evidence | Exact external protocol reproduction before official SOTA wording |
| SKAB | Main reliability route `0.8532 +/- 0.0339`; formal CF/no-CF subset summary complete; external-style USAD/TranAD/GDN/MTAD-GAT baselines exist | method evidence | Official repository scoring, threshold, and event/point alignment before leaderboard wording |
| Hydraulic | Four-target near-ceiling non-degradation evidence exists | supporting evidence | Published-table formatting and one stronger temporal/deep baseline remain useful |
| C-MAPSS | Original terminal RUL protocol restored; AnchorPath-BiGRU RMSE `20.4792`; matched HistGB/ExtraTrees/TCN/GRU baselines exist | transfer evidence | Add only protocol-compatible published RUL baselines before literature-wide SOTA wording |

## 4. Ablation and Reliability Terms

| Ablation / Reliability Term | Current Evidence | Status | Paper Use |
|---|---|---|---|
| Anchor only | Seed-level ledger and main comparison rows exist | covered | Establishes strong default predictor |
| Unfiltered evidence | Seed-level and visualization rows exist | covered | Shows unsafe/all-edge evidence is not the story |
| Expert only | SKAB expert/mechanism rows and TEP expert-removal support exist | covered | Supports expert mechanism contribution |
| LLM only | LLM condition candidate gate is seed-level safety/rejection evidence | covered | Report as reliability admission, not guaranteed positive gain |
| Lag/residual only | TEP sequence and C-MAPSS temporal rows exist | covered | Supports temporal propagation evidence |
| Graph only | Graph-temporal controls exist | covered | Frame as graph-temporal evidence rather than pure graph causality |
| No counterfactual guard | Formal SKAB CF/no-CF three-seed result: CF `0.8798 +/- 0.0317`, no-CF `0.8801 +/- 0.0317`, difference `-0.0003 +/- 0.0003` | closed | CF is reliability/interpretability guard, not main accuracy source |
| No tail safety | Matched SKAB policy replay complete; no admissions changed because admitted candidates already satisfy low-tail safety | closed | Non-differential safety ablation |
| No complexity penalty | Three-seed no-complexity row `0.8234 +/- 0.0153` vs complexity-guarded `0.8261 +/- 0.0138` | closed | Shows source burden can be constrained without accuracy loss |
| Full model | Seed-level evidence exists across the main package | covered | Main reliability-calibrated fusion claim |

Coverage gate: `aaai_ablation_coverage_audit.json` is `complete` with no missing or incomplete rows.

## 5. Reproducibility and Paper Package

| Item | Current Evidence | Status | Remaining Gate |
|---|---|---|---|
| Official AAAI style | `aaai_latex_draft` contains `aaai2027.sty`, `aaai2027.bst`, official author-kit files, figures, references, manifest, coverage, and protocol audits | closed | Keep synchronized with final source edits |
| Compile gate | `aaai_latex_compile_gate.json` reports `compiled_clean`: PDF exists, LaTeX errors 0, fatal errors 0, undefined references 0, overfull hboxes 0 | closed | Recompile after any manuscript edit |
| PDF float inspection | `aaai_pdf_float_inspection.json` reports `inspected_clean` over 7 rendered pages | closed | Re-render after any figure/table edit |
| Goal audit | `aaai_goal_completion_audit.json` marks figures, algorithm, protocol, ablation, claim boundary, and official template satisfied; `aaai_external_baseline_alignment_decision.*` now records exact decision boundaries for PatchTST, Anomaly Transformer, and Graph WaveNet; `external_baseline_official_repos/official_external_repo_snapshot.*` fixes official repository HEAD provenance; `external_baseline_official_repos/official_external_repo_checkout_audit.*` verifies local checkouts at those HEAD commits; all three have local matched-adapter three-seed probes and official-source adapted low-budget probes | not complete overall | Exact official-score reproduction remains open |
| External baseline command wrapper | `Scripts/protocol_aligned_external_baseline_runner.py` accepts manifest-style `--dataset`, `--model`, `--seed`, `--protocol matched`, and `--validation-only-thresholds`; `Scripts/checkout_external_baseline_repos.py` verifies official source checkouts at fixed commits and audits entrypoints/dependencies/data interfaces; `Scripts/prepare_anomaly_transformer_skab_official_adapter.py` prepares three-seed PSM-compatible SKAB files for the verified Anomaly Transformer source and records required solver patches; `Scripts/run_anomaly_transformer_skab_official_wrapper.py` executes the official-source Anomaly Transformer architecture with patched SKAB validation-only thresholds; `external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json` records budget-escalated Macro-F1 `0.4716 +/- 0.0487` with FAR `38.34` and MAR `63.29`; `Scripts/run_patchtst_tep_official_wrapper.py` executes the official PatchTST supervised source backbone with a lightweight TEP classification head, and `external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_budget_probe.json` records budget-escalated Target-F1 `0.4197 +/- 0.0320`; `Scripts/run_graph_wavenet_tep_official_wrapper.py` executes the official Graph WaveNet source backbone with a lightweight TEP classification head and records budget-escalated Target-F1 `0.2854 +/- 0.0529`; pending gate JSON/Markdown now expose the executable command template and checkout status | closed for local matched-adapter runner contract, official source checkout, SKAB source-adapter preparation, and three official-source adapted budget probes | Still not official external-score reproduction; exact official benchmark preprocessing, metric, and paper-protocol runs remain required for public leaderboard wording |
| Efficiency evidence | `aaai_efficiency_audit.md` records measured SKAB, C-MAPSS, and TEP sequence efficiency rows | covered | Keep efficiency rows tied to measured artifacts only |

## 6. Remaining AAAI-Level Blockers

| Blocker | Why It Matters | Next Action |
|---|---|---|
| PatchTST / Anomaly Transformer / Graph WaveNet exact external alignments | Current manifest still marks these as `pending_external_alignment`; official repository HEAD provenance and local source checkout are now verified (PatchTST `204c21efe0b3`, Anomaly Transformer `b0ee470c8012`, Graph WaveNet `6b162e80c59a`); checkout audit identifies official entrypoints/dependencies/data interfaces; Anomaly Transformer now has a three-seed SKAB PSM-compatible source adapter and a patched validation-only official-source wrapper with budget-escalated Macro-F1 `0.4716 +/- 0.0487`, FAR `38.34`, and MAR `63.29`; PatchTST has an official supervised-source TEP wrapper with a lightweight classification head and budget-escalated Target-F1 `0.4197 +/- 0.0320`; Graph WaveNet has an official-source TEP wrapper with adaptive adjacency, a PyTorch Conv2d compatibility patch, and budget-escalated Target-F1 `0.2854 +/- 0.0529`; local matched three-seed TEP probes and an executable local adapter wrapper also exist: PatchTST `0.0592 +/- 0.0145`, Anomaly Transformer `0.1863 +/- 0.0474`, Graph WaveNet `0.0108 +/- 0.0091` Target-F1 on the same TEP adapter protocol; SKAB Anomaly-Transformer-style three-seed probe gives Macro-F1 `0.4493 +/- 0.0726`, FAR `56.6923 +/- 8.8409`, MAR `44.8715 +/- 2.2162` | Use these as stronger negative temporal/graph-temporal/anomaly controls only; exact official benchmark preprocessing, metric, seed, and paper-protocol reproduction remains required before public leaderboard wording |
| Final prose polishing | Drafts exist, but the English paper still needs compressed AAAI-length writing and final table placement after external-alignment decisions | Polish after deciding whether to add more external baselines |

## Immediate Execution Order

1. Decide whether to leave the three budget-escalated official-source adapted probes as sufficient negative-control evidence or run exact native-paper reproductions in their original benchmark domains.
2. Add protocol-compatible published C-MAPSS RUL baselines only if the paper needs stronger RUL literature positioning.
3. Polish the English AAAI LaTeX manuscript and Chinese draft using the now-complete ablation, reliability, and compile evidence.
4. Recompile and re-render the PDF after every manuscript or figure/table edit.
