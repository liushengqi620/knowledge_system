# AAAI External Baseline Alignment Decision

- Version: external-baseline-alignment-decision-v1
- Checked on: 2026-06-21
- Overall status: official_source_adapted_controls_materialized
- Claim gate: Use these methods as matched-protocol or official-source adapted controls only; do not use them as official external comparison scores.

This decision artifact records why the strongest external baselines remain protocol-alignment obligations rather than completed official comparison scores.

## Decision Matrix

| Method | Venue | Official task | Target datasets | Local adapter | Directness | Admissibility | Next action |
|---|---|---|---|---|---|---|---|
| PatchTST | ICLR 2023 | long-term time-series forecasting and representation learning | TEP, SKAB | local_three_seed_probe_available | task-adapted backbone rather than a direct official anomaly or fault-diagnosis score | not_admissible_as_official_external_score | use the new official-source adapted TEP wrapper as negative-control evidence; exact official budget/protocol reproduction remains required before public comparison wording |
| Anomaly Transformer | ICLR 2022 Spotlight | unsupervised time-series anomaly detection | SKAB, TEP | local_three_seed_probe_available | direct anomaly-detection candidate for SKAB and adapted score baseline for TEP | not_admissible_as_official_external_score | wrap official or faithful Anomaly Transformer scoring for SKAB first, then decide whether TEP remains anomaly-only or multiclass-adapted |
| Graph WaveNet | IJCAI 2019 | spatial-temporal traffic forecasting | TEP | local_three_seed_probe_available | graph-temporal architecture reference, not a direct TEP diagnosis leaderboard score | not_admissible_as_official_external_score | use the official-source adapted TEP wrapper as negative graph-temporal control evidence; exact traffic-forecasting protocol reproduction remains out of scope for public comparison wording |

## Per-Method Contracts

### PatchTST

- Paper: https://openreview.net/forum?id=Jbdc0vTOcol
- Code: https://github.com/yuqinie98/PatchTST
- Manifest status: materialized_official_source_adapted_control
- Official repo snapshot: repo_head_resolved at `knowledge_exports/external_baseline_official_repos/official_external_repo_snapshot.json`; branch `main`; HEAD `204c21efe0b3`; protocol `not_started_from_snapshot`
- Official repo checkout: checkout_verified at `knowledge_exports/external_baseline_official_repos/official_external_repo_checkout_audit.json`; HEAD `204c21efe0b3`; wrapper `official_source_adapted_backbone_wrapper_available_not_official_score`
- Local adapter status: local_three_seed_probe_available
- Safe paper use: cite as a modern temporal backbone and use only as a matched adaptation after runner artifacts exist
- Core mechanism:
  - segment each variable history into overlapping patch tokens
  - share the Transformer encoder across channel-independent univariate series
  - use the patch encoder as a temporal backbone before a task-specific head
- Protocol mismatches:
  - official objective is forecasting/representation, while TEP requires strict 22-class diagnosis and SKAB requires anomaly scoring
  - official benchmark suite is not the current TEP/SKAB split, window, and validation-threshold protocol
  - a classification or anomaly-score head must be introduced and archived before any matched result is admissible
- Runner contract:
  - implement channel-independent patch encoder with declared patch length, stride, lookback window, and head type
  - accept dataset, seed, train/validation/test split, window, and validation-only threshold arguments
  - write validation predictions, test predictions, selected threshold/head config, metric JSON, and config hash
- Local adapter artifacts:
  - tep_official_source_wrapper_smoke (present): `knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_smoke.json`; official PatchTST supervised source backbone with a lightweight TEP classification head; smoke evidence only, not an official paper score
  - tep_official_source_wrapper_smoke_summary (present): `knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_smoke.md`; Markdown summary for the PatchTST official-source adapted TEP wrapper smoke
  - tep_official_source_wrapper_three_seed_probe (present): `knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_probe.json`; three-seed low-budget official-source PatchTST supervised backbone adapted with a lightweight TEP classification head; negative-control evidence only
  - tep_official_source_wrapper_three_seed_summary (present): `knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_probe.md`; Markdown summary for the three-seed PatchTST official-source adapted TEP wrapper probe
  - tep_official_source_wrapper_three_seed_budget_probe (present): `knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_budget_probe.json`; three-seed budget-escalated official-source PatchTST supervised backbone adapted with a lightweight TEP classification head; negative-control evidence only
  - tep_official_source_wrapper_three_seed_budget_summary (present): `knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_budget_probe.md`; Markdown summary for the budget-escalated PatchTST official-source adapted TEP wrapper probe
  - three_seed_matched_probe (present): `knowledge_exports/tep_patchtst_matched_adapter_3seed_probe/patchtst_3seed_probe.json`; three-seed, 3000-row, 3-epoch TEP matched-adapter probe; negative-control evidence only
  - three_seed_alignment_artifact (present): `knowledge_exports/aaai_external_baseline_alignment_decision/patchtst_tep_3seed_alignment_artifact.json`; hash-bearing claim-boundary artifact for the local PatchTST-style three-seed probe
  - pipeline_smoke (present): `knowledge_exports/tep_patchtst_matched_adapter_smoke/patchtst_smoke.json`; single-seed, 600-row, 1-epoch smoke; verifies matched adapter execution only
  - seed42_low_budget_probe (present): `knowledge_exports/tep_patchtst_matched_adapter_seed42_e5/patchtst_seed42_e5.json`; single-seed 5000-row 5-epoch probe; current score is weak and not a competitive result
  - alignment_artifact (present): `knowledge_exports/aaai_external_baseline_alignment_decision/patchtst_tep_smoke_alignment_artifact.json`; hash-bearing claim-boundary artifact for the local PatchTST-style adapter smoke

### Anomaly Transformer

- Paper: https://openreview.net/forum?id=LzQQ89U1qm_
- Code: https://github.com/thuml/Anomaly-Transformer
- Manifest status: materialized_official_source_adapted_control
- Official repo snapshot: repo_head_resolved at `knowledge_exports/external_baseline_official_repos/official_external_repo_snapshot.json`; branch `main`; HEAD `b0ee470c8012`; protocol `not_started_from_snapshot`
- Official repo checkout: checkout_verified at `knowledge_exports/external_baseline_official_repos/official_external_repo_checkout_audit.json`; HEAD `b0ee470c8012`; wrapper `patched_skab_official_source_wrapper_available_not_official_score`
- Local adapter status: local_three_seed_probe_available
- Safe paper use: high-priority anomaly baseline family; official comparison requires threshold and adjustment alignment
- Core mechanism:
  - learn association discrepancy as an anomaly criterion
  - use anomaly attention to separate prior and series associations
  - amplify normal-abnormal distinction through minimax training
- Protocol mismatches:
  - official evaluation uses unsupervised anomaly scores and adjustment policy that must be matched or explicitly disabled
  - TEP strict multiclass diagnosis is not the native objective and needs a declared score-to-class adaptation
  - thresholding must be validation-only under the current protocol and cannot use test labels or post-hoc adjustment unless declared
- Runner contract:
  - run the official association-discrepancy score path with fixed seed and documented window length
  - emit raw anomaly scores for validation and test before thresholding
  - archive whether point adjustment/event adjustment is used, and compute the same Macro-F1/FAR/MAR protocol as the paper table
- Local adapter artifacts:
  - skab_three_seed_matched_probe (present): `knowledge_exports/external_baseline_protocol_runs/skab_anomaly_transformer_3seed_probe.json`; three-seed SKAB association-discrepancy-style anomaly scorer; local matched negative-control evidence only
  - skab_official_source_adapter (present): `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_adapter/anomaly_transformer_official_skab_adapter.json`; PSM-compatible SKAB adapter for the verified official Anomaly Transformer source; no official score until solver patch and matched threshold protocol are implemented
  - skab_official_source_adapter_summary (present): `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_adapter/anomaly_transformer_official_skab_adapter.md`; Markdown summary of SKAB official-source adapter files and protocol risks
  - skab_official_source_wrapper_smoke (present): `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_smoke.json`; official-source Anomaly Transformer architecture with patched SKAB validation-only threshold protocol; smoke evidence only
  - skab_official_source_wrapper_smoke_summary (present): `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_smoke.md`; Markdown summary for the official-source patched SKAB wrapper smoke
  - skab_official_source_wrapper_three_seed_probe (present): `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_probe.json`; three-seed low-budget official-source Anomaly Transformer architecture with patched SKAB validation-only threshold protocol; not an official paper score
  - skab_official_source_wrapper_three_seed_summary (present): `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_probe.md`; Markdown summary for the three-seed official-source patched SKAB wrapper probe
  - skab_official_source_wrapper_three_seed_budget_probe (present): `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json`; three-seed budget-escalated official-source Anomaly Transformer architecture with patched SKAB validation-only threshold protocol; high-FAR negative-control evidence, not an official paper score
  - skab_official_source_wrapper_three_seed_budget_summary (present): `knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_budget_probe.md`; Markdown summary for the budget-escalated official-source patched SKAB wrapper probe
  - skab_three_seed_summary (present): `knowledge_exports/external_baseline_protocol_runs/skab_anomaly_transformer_3seed_probe.md`; Markdown summary for the local SKAB Anomaly-Transformer-style three-seed probe
  - skab_three_seed_alignment_artifact (present): `knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_skab_3seed_alignment_artifact.json`; hash-bearing claim-boundary artifact for the local SKAB Anomaly-Transformer-style three-seed probe
  - skab_pipeline_smoke (present): `knowledge_exports/external_baseline_protocol_runs/skab_anomaly_transformer_smoke.json`; single-seed, 1-epoch SKAB association-discrepancy-style anomaly scorer; verifies matched SKAB anomaly route only
  - skab_alignment_artifact (present): `knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_skab_smoke_alignment_artifact.json`; hash-bearing claim-boundary artifact for the local SKAB Anomaly-Transformer-style smoke
  - three_seed_matched_probe (present): `knowledge_exports/tep_anomaly_transformer_matched_adapter_3seed_probe/anomaly_transformer_3seed_probe.json`; three-seed, 3000-row, 3-epoch TEP matched-adapter probe; negative-control evidence only
  - three_seed_alignment_artifact (present): `knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_tep_3seed_alignment_artifact.json`; hash-bearing claim-boundary artifact for the local Anomaly-Transformer-style three-seed probe
  - pipeline_smoke (present): `knowledge_exports/tep_anomaly_transformer_matched_adapter_smoke/anomaly_transformer_smoke.json`; single-seed, 600-row, 1-epoch TEP matched-adapter smoke; verifies association-discrepancy-style adapter execution only
  - alignment_artifact (present): `knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_tep_smoke_alignment_artifact.json`; hash-bearing claim-boundary artifact for the local Anomaly-Transformer-style adapter smoke

### Graph WaveNet

- Paper: https://www.ijcai.org/proceedings/2019/264
- Code: https://github.com/nnzhan/Graph-WaveNet
- Manifest status: materialized_official_source_adapted_control
- Official repo snapshot: repo_head_resolved at `knowledge_exports/external_baseline_official_repos/official_external_repo_snapshot.json`; branch `master`; HEAD `6b162e80c59a`; protocol `not_started_from_snapshot`
- Official repo checkout: checkout_verified at `knowledge_exports/external_baseline_official_repos/official_external_repo_checkout_audit.json`; HEAD `6b162e80c59a`; wrapper `official_source_adapted_graph_temporal_wrapper_available_not_official_score`
- Local adapter status: local_three_seed_probe_available
- Safe paper use: cite as graph-temporal design motivation; compare only as a matched adaptation after graph contract is archived
- Core mechanism:
  - learn adaptive node dependencies through trainable node embeddings
  - combine graph convolution with stacked dilated temporal convolution
  - model long temporal receptive fields and hidden spatial dependencies jointly
- Protocol mismatches:
  - official task is traffic forecasting on METR-LA/PEMS-BAY rather than industrial fault diagnosis
  - the native input contract assumes a node graph and forecasting horizon, while TEP uses process variables and class labels
  - a fair comparison requires a declared process-variable graph, horizon/window adapter, classification head, and no test-tuned thresholds
- Runner contract:
  - define the process-variable graph contract: static, adaptive, or reliability-admitted adjacency
  - accept identical TEP windows, seeds, split, normalization, and class labels as the main protocol
  - write adjacency provenance, validation/test logits, metric JSON, config hash, and executable command
- Local adapter artifacts:
  - tep_official_source_wrapper_smoke (present): `knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_smoke.json`; official Graph WaveNet source backbone with a lightweight TEP classification head and PyTorch Conv2d compatibility patch; smoke evidence only, not an official paper score
  - tep_official_source_wrapper_smoke_summary (present): `knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_smoke.md`; Markdown summary for the Graph WaveNet official-source adapted TEP wrapper smoke
  - tep_official_source_wrapper_three_seed_probe (present): `knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_probe.json`; three-seed low-budget official-source Graph WaveNet backbone adapted with a lightweight TEP classification head; negative-control evidence only
  - tep_official_source_wrapper_three_seed_summary (present): `knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_probe.md`; Markdown summary for the three-seed Graph WaveNet official-source adapted TEP wrapper probe
  - tep_official_source_wrapper_three_seed_budget_probe (present): `knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_budget_probe.json`; three-seed budget-escalated official-source Graph WaveNet backbone adapted with a lightweight TEP classification head; negative-control evidence only
  - tep_official_source_wrapper_three_seed_budget_summary (present): `knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_budget_probe.md`; Markdown summary for the budget-escalated Graph WaveNet official-source adapted TEP wrapper probe
  - three_seed_matched_probe (present): `knowledge_exports/tep_graph_wavenet_matched_adapter_3seed_probe/graph_wavenet_3seed_probe.json`; three-seed, 3000-row, 3-epoch TEP matched-adapter probe; negative-control evidence only
  - three_seed_alignment_artifact (present): `knowledge_exports/aaai_external_baseline_alignment_decision/graph_wavenet_tep_3seed_alignment_artifact.json`; hash-bearing claim-boundary artifact for the local Graph-WaveNet-style three-seed probe
  - pipeline_smoke (present): `knowledge_exports/tep_graph_wavenet_matched_adapter_smoke/graph_wavenet_smoke.json`; single-seed, 600-row, 1-epoch TEP matched-adapter smoke; verifies adaptive graph-temporal adapter execution only
  - alignment_artifact (present): `knowledge_exports/aaai_external_baseline_alignment_decision/graph_wavenet_tep_smoke_alignment_artifact.json`; hash-bearing claim-boundary artifact for the local Graph-WaveNet-style adapter smoke
