"""Build the AAAI LaTeX draft package from current paper artifacts.

When the official AAAI-27 author kit is available under
``knowledge_exports/official_aaai_template/AuthorKit27``, the generated source
uses the official submission style and copies the required style assets into the
package. The source remains a draft until it compiles cleanly and floats are
inspected under that official style.
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def _find_repo_root() -> Path:
    module_root = Path(__file__).absolute().parents[1]
    resolved_root = Path(__file__).resolve().parents[1]
    cwd = Path.cwd()
    candidates: list[Path] = []
    env_root = os.environ.get("AAAI_WORK_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([cwd, cwd.parent, module_root, resolved_root])
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.absolute()).lower()
        if key in seen:
            continue
        seen.add(key)
        if (candidate / "Scripts" / "build_aaai_latex_draft.py").exists() and (candidate / "knowledge_exports").exists():
            return candidate
    return module_root


REPO_ROOT = _find_repo_root()
EXPORT_DIR = REPO_ROOT / "knowledge_exports"
REFERENCES = EXPORT_DIR / "references.bib"
OFFICIAL_TEMPLATE_ROOT = EXPORT_DIR / "official_aaai_template" / "AuthorKit27"
OFFICIAL_TEMPLATE_FILES = [
    OFFICIAL_TEMPLATE_ROOT / "aaai2027.sty",
    OFFICIAL_TEMPLATE_ROOT / "aaai2027.bst",
    OFFICIAL_TEMPLATE_ROOT / "AnonymousSubmission2027.tex",
    OFFICIAL_TEMPLATE_ROOT / "ReproducibilityChecklist.tex",
    OFFICIAL_TEMPLATE_ROOT / "ReproducibilityChecklist.pdf",
]

CORE_FIGURE_DIR = EXPORT_DIR / "paper_core_figures_rendered"
EXPERIMENT_FIGURE_DIR = EXPORT_DIR / "paper_experiment_visualizations"

FIGURES = [
    CORE_FIGURE_DIR / "figure1_reliability_calibrated_mechanism_fusion.pdf",
    CORE_FIGURE_DIR / "figure1_reliability_calibrated_mechanism_fusion.png",
    CORE_FIGURE_DIR / "figure2_evidence_reliability_admission_loop.pdf",
    CORE_FIGURE_DIR / "figure2_evidence_reliability_admission_loop.png",
    CORE_FIGURE_DIR / "figure3_anchor_challenger_deployment_rule.pdf",
    CORE_FIGURE_DIR / "figure3_anchor_challenger_deployment_rule.png",
    EXPERIMENT_FIGURE_DIR / "main_multi_benchmark_results.png",
    EXPERIMENT_FIGURE_DIR / "reliability_ablation_summary.png",
    EXPERIMENT_FIGURE_DIR / "tep_mechanism_ablation.png",
    EXPERIMENT_FIGURE_DIR / "cmapss_rul_matched_results.png",
]

SUPPORTING_ARTIFACTS = [
    (
        EXPORT_DIR / "final_aaai_paper_package.md",
        "final_aaai_paper_package.md",
    ),
    (
        EXPORT_DIR / "final_aaai_paper_package_summary.md",
        "final_aaai_paper_package_summary.md",
    ),
    (
        EXPORT_DIR / "aaai_experiment_execution_manifest" / "aaai_experiment_execution_manifest.md",
        "aaai_experiment_execution_manifest.md",
    ),
    (
        EXPORT_DIR / "aaai_experiment_execution_manifest" / "aaai_experiment_execution_manifest.json",
        "aaai_experiment_execution_manifest.json",
    ),
    (
        EXPORT_DIR / "aaai_experiment_execution_manifest" / "aaai_pending_baseline_gate.md",
        "aaai_pending_baseline_gate.md",
    ),
    (
        EXPORT_DIR / "aaai_experiment_execution_manifest" / "aaai_pending_baseline_gate.json",
        "aaai_pending_baseline_gate.json",
    ),
    (
        REPO_ROOT / "Scripts" / "protocol_aligned_external_baseline_runner.py",
        "protocol_aligned_external_baseline_runner.py",
    ),
    (
        REPO_ROOT / "Scripts" / "run_public_ms_gse_rpf_experiment.py",
        "run_public_ms_gse_rpf_experiment.py",
    ),
    (
        REPO_ROOT / "Scripts" / "run_cmapss_rul_baselines.py",
        "run_cmapss_rul_baselines.py",
    ),
    (
        REPO_ROOT / "Scripts" / "run_cmapss_mdfa_source_matched.py",
        "run_cmapss_mdfa_source_matched.py",
    ),
    (
        REPO_ROOT / "Scripts" / "skab_native_metric_audit.py",
        "skab_native_metric_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "skab_official_baseline_gate.py",
        "skab_official_baseline_gate.py",
    ),
    (
        REPO_ROOT / "Scripts" / "skab_official_repository_baseline_audit.py",
        "skab_official_repository_baseline_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "skab_official_source_rerun_audit.py",
        "skab_official_source_rerun_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "skab_source_rerun_delta_audit.py",
        "skab_source_rerun_delta_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "aaai_sota_gap_ledger.py",
        "aaai_sota_gap_ledger.py",
    ),
    (
        REPO_ROOT / "Scripts" / "skab_external_baselines.py",
        "skab_external_baselines.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_native_preprocessing_manifest.py",
        "cmapss_native_preprocessing_manifest.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_published_baseline_alignment.py",
        "cmapss_published_baseline_alignment.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_published_baseline_contract.py",
        "cmapss_published_baseline_contract.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_lstm_source_protocol_audit.py",
        "cmapss_lstm_source_protocol_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_open_protocol_candidate_audit.py",
        "cmapss_open_protocol_candidate_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_mdfa_source_profile.py",
        "cmapss_mdfa_source_profile.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_mdfa_runner_audit.py",
        "cmapss_mdfa_runner_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_mdfa_strategy_probe_audit.py",
        "cmapss_mdfa_strategy_probe_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_rul_backbone_optimization_audit.py",
        "cmapss_rul_backbone_optimization_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_pseudo_truncation_validation_audit.py",
        "cmapss_pseudo_truncation_validation_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "cmapss_exact_native_gap_audit.py",
        "cmapss_exact_native_gap_audit.py",
    ),
    (
        REPO_ROOT / "Scripts" / "checkout_external_baseline_repos.py",
        "checkout_external_baseline_repos.py",
    ),
    (
        REPO_ROOT / "Scripts" / "prepare_anomaly_transformer_skab_official_adapter.py",
        "prepare_anomaly_transformer_skab_official_adapter.py",
    ),
    (
        REPO_ROOT / "Scripts" / "run_anomaly_transformer_skab_official_wrapper.py",
        "run_anomaly_transformer_skab_official_wrapper.py",
    ),
    (
        REPO_ROOT / "Scripts" / "run_patchtst_tep_official_wrapper.py",
        "run_patchtst_tep_official_wrapper.py",
    ),
    (
        REPO_ROOT / "Scripts" / "run_graph_wavenet_tep_official_wrapper.py",
        "run_graph_wavenet_tep_official_wrapper.py",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "patchtst_seed42_dry_run_plan.json",
        "patchtst_seed42_dry_run_plan.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "skab_anomaly_transformer_seed42_dry_run_plan.json",
        "skab_anomaly_transformer_seed42_dry_run_plan.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "skab_anomaly_transformer_smoke.json",
        "skab_anomaly_transformer_smoke.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "skab_anomaly_transformer_3seed_probe.md",
        "skab_anomaly_transformer_3seed_probe.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "skab_anomaly_transformer_3seed_probe.json",
        "skab_anomaly_transformer_3seed_probe.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "skab_external_baselines_native_records_usad_tranad_w48_e8.json",
        "skab_external_baselines_native_records_usad_tranad_w48_e8.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_adapter" / "anomaly_transformer_official_skab_adapter.md",
        "anomaly_transformer_official_skab_adapter.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_adapter" / "anomaly_transformer_official_skab_adapter.json",
        "anomaly_transformer_official_skab_adapter.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_wrapper_smoke.md",
        "anomaly_transformer_official_skab_wrapper_smoke.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_wrapper_smoke.json",
        "anomaly_transformer_official_skab_wrapper_smoke.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_wrapper_3seed_probe.md",
        "anomaly_transformer_official_skab_wrapper_3seed_probe.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_wrapper_3seed_probe.json",
        "anomaly_transformer_official_skab_wrapper_3seed_probe.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_wrapper_3seed_budget_probe.md",
        "anomaly_transformer_official_skab_wrapper_3seed_budget_probe.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json",
        "anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "patchtst_official_tep_wrapper_smoke.md",
        "patchtst_official_tep_wrapper_smoke.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "patchtst_official_tep_wrapper_smoke.json",
        "patchtst_official_tep_wrapper_smoke.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "patchtst_official_tep_wrapper_3seed_probe.md",
        "patchtst_official_tep_wrapper_3seed_probe.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "patchtst_official_tep_wrapper_3seed_probe.json",
        "patchtst_official_tep_wrapper_3seed_probe.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "patchtst_official_tep_wrapper_3seed_budget_probe.md",
        "patchtst_official_tep_wrapper_3seed_budget_probe.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "patchtst_official_tep_wrapper_3seed_budget_probe.json",
        "patchtst_official_tep_wrapper_3seed_budget_probe.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "graph_wavenet_official_tep_wrapper_smoke.md",
        "graph_wavenet_official_tep_wrapper_smoke.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "graph_wavenet_official_tep_wrapper_smoke.json",
        "graph_wavenet_official_tep_wrapper_smoke.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "graph_wavenet_official_tep_wrapper_3seed_probe.md",
        "graph_wavenet_official_tep_wrapper_3seed_probe.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "graph_wavenet_official_tep_wrapper_3seed_probe.json",
        "graph_wavenet_official_tep_wrapper_3seed_probe.json",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "graph_wavenet_official_tep_wrapper_3seed_budget_probe.md",
        "graph_wavenet_official_tep_wrapper_3seed_budget_probe.md",
    ),
    (
        EXPORT_DIR / "external_baseline_protocol_runs" / "graph_wavenet_official_tep_wrapper_3seed_budget_probe.json",
        "graph_wavenet_official_tep_wrapper_3seed_budget_probe.json",
    ),
    (EXPORT_DIR / "aaai_ablation_coverage_audit.md", "aaai_ablation_coverage_audit.md"),
    (EXPORT_DIR / "aaai_ablation_coverage_audit.json", "aaai_ablation_coverage_audit.json"),
    (EXPORT_DIR / "aaai_missing_ablation_execution_plan.md", "aaai_missing_ablation_execution_plan.md"),
    (EXPORT_DIR / "aaai_missing_ablation_execution_plan.json", "aaai_missing_ablation_execution_plan.json"),
    (EXPORT_DIR / "aaai_efficiency_audit.md", "aaai_efficiency_audit.md"),
    (EXPORT_DIR / "aaai_efficiency_audit.json", "aaai_efficiency_audit.json"),
    (EXPORT_DIR / "paper_protocol_sota_audit.md", "paper_protocol_sota_audit.md"),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_exact_native_protocol_gate.md",
        "aaai_exact_native_protocol_gate.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_exact_native_protocol_gate.json",
        "aaai_exact_native_protocol_gate.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_exact_native_execution_plan.md",
        "aaai_exact_native_execution_plan.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_exact_native_execution_plan.json",
        "aaai_exact_native_execution_plan.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_sota_gap_ledger.md",
        "aaai_sota_gap_ledger.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_sota_gap_ledger.json",
        "aaai_sota_gap_ledger.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_native_metric_audit.md",
        "skab_native_metric_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_native_metric_audit.json",
        "skab_native_metric_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_baseline_gate.md",
        "skab_official_baseline_gate.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_baseline_gate.json",
        "skab_official_baseline_gate.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_repository_baseline_audit.md",
        "skab_official_repository_baseline_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_repository_baseline_audit.json",
        "skab_official_repository_baseline_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_source_rerun_audit.md",
        "skab_official_source_rerun_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_source_rerun_audit.json",
        "skab_official_source_rerun_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_source_rerun_delta_audit.md",
        "skab_source_rerun_delta_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_source_rerun_delta_audit.json",
        "skab_source_rerun_delta_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_native_preprocessing_manifest.md",
        "cmapss_native_preprocessing_manifest.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_native_preprocessing_manifest.json",
        "cmapss_native_preprocessing_manifest.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_published_baseline_alignment.md",
        "cmapss_published_baseline_alignment.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_published_baseline_alignment.json",
        "cmapss_published_baseline_alignment.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_published_baseline_contract.md",
        "cmapss_published_baseline_contract.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_published_baseline_contract.json",
        "cmapss_published_baseline_contract.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_lstm_source_protocol_audit.md",
        "cmapss_lstm_source_protocol_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_lstm_source_protocol_audit.json",
        "cmapss_lstm_source_protocol_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_open_protocol_candidate_audit.md",
        "cmapss_open_protocol_candidate_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_open_protocol_candidate_audit.json",
        "cmapss_open_protocol_candidate_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_source_profile.md",
        "cmapss_mdfa_source_profile.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_source_profile.json",
        "cmapss_mdfa_source_profile.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_runner_audit.md",
        "cmapss_mdfa_runner_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_runner_audit.json",
        "cmapss_mdfa_runner_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_strategy_probe_audit.md",
        "cmapss_mdfa_strategy_probe_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_strategy_probe_audit.json",
        "cmapss_mdfa_strategy_probe_audit.json",
    ),
    (
        EXPORT_DIR / "cmapss_mdfa_source_matched_source2d_smoke" / "cmapss_mdfa_source_matched_summary.md",
        "cmapss_mdfa_source_matched_smoke_summary.md",
    ),
    (
        EXPORT_DIR / "cmapss_mdfa_source_matched_source2d_smoke" / "cmapss_mdfa_source_matched_summary.json",
        "cmapss_mdfa_source_matched_smoke_summary.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_rul_backbone_optimization_audit.md",
        "cmapss_rul_backbone_optimization_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_rul_backbone_optimization_audit.json",
        "cmapss_rul_backbone_optimization_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_pseudo_truncation_validation_audit.md",
        "cmapss_pseudo_truncation_validation_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_pseudo_truncation_validation_audit.json",
        "cmapss_pseudo_truncation_validation_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_exact_native_gap_audit.md",
        "cmapss_exact_native_gap_audit.md",
    ),
    (
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_exact_native_gap_audit.json",
        "cmapss_exact_native_gap_audit.json",
    ),
    (
        EXPORT_DIR / "cmapss_lstm_published_style_w80_cap125" / "cmapss_rul_matched_baselines_summary.md",
        "cmapss_lstm_published_style_w80_cap125_summary.md",
    ),
    (
        EXPORT_DIR / "cmapss_lstm_published_style_w80_cap125" / "cmapss_rul_matched_baselines_summary.json",
        "cmapss_lstm_published_style_w80_cap125_summary.json",
    ),
    (EXPORT_DIR / "reference_verification_report.md", "reference_verification_report.md"),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "aaai_external_baseline_alignment_decision.md",
        "aaai_external_baseline_alignment_decision.md",
    ),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "aaai_external_baseline_alignment_decision.json",
        "aaai_external_baseline_alignment_decision.json",
    ),
    (
        EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_snapshot.md",
        "official_external_repo_snapshot.md",
    ),
    (
        EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_snapshot.json",
        "official_external_repo_snapshot.json",
    ),
    (
        EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_checkout_audit.md",
        "official_external_repo_checkout_audit.md",
    ),
    (
        EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_checkout_audit.json",
        "official_external_repo_checkout_audit.json",
    ),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "anomaly_transformer_tep_smoke_alignment_artifact.json",
        "anomaly_transformer_tep_smoke_alignment_artifact.json",
    ),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "anomaly_transformer_skab_smoke_alignment_artifact.json",
        "anomaly_transformer_skab_smoke_alignment_artifact.json",
    ),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "anomaly_transformer_skab_3seed_alignment_artifact.json",
        "anomaly_transformer_skab_3seed_alignment_artifact.json",
    ),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "graph_wavenet_tep_smoke_alignment_artifact.json",
        "graph_wavenet_tep_smoke_alignment_artifact.json",
    ),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "patchtst_tep_3seed_alignment_artifact.json",
        "patchtst_tep_3seed_alignment_artifact.json",
    ),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "anomaly_transformer_tep_3seed_alignment_artifact.json",
        "anomaly_transformer_tep_3seed_alignment_artifact.json",
    ),
    (
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "graph_wavenet_tep_3seed_alignment_artifact.json",
        "graph_wavenet_tep_3seed_alignment_artifact.json",
    ),
    (
        EXPORT_DIR / "tep_patchtst_matched_adapter_3seed_probe" / "patchtst_3seed_probe.md",
        "patchtst_3seed_probe.md",
    ),
    (
        EXPORT_DIR / "tep_patchtst_matched_adapter_3seed_probe" / "patchtst_3seed_probe.json",
        "patchtst_3seed_probe.json",
    ),
    (
        EXPORT_DIR / "tep_anomaly_transformer_matched_adapter_3seed_probe" / "anomaly_transformer_3seed_probe.md",
        "anomaly_transformer_3seed_probe.md",
    ),
    (
        EXPORT_DIR / "tep_anomaly_transformer_matched_adapter_3seed_probe" / "anomaly_transformer_3seed_probe.json",
        "anomaly_transformer_3seed_probe.json",
    ),
    (
        EXPORT_DIR / "tep_graph_wavenet_matched_adapter_3seed_probe" / "graph_wavenet_3seed_probe.md",
        "graph_wavenet_3seed_probe.md",
    ),
    (
        EXPORT_DIR / "tep_graph_wavenet_matched_adapter_3seed_probe" / "graph_wavenet_3seed_probe.json",
        "graph_wavenet_3seed_probe.json",
    ),
    (
        EXPORT_DIR / "tep_anomaly_transformer_matched_adapter_smoke" / "anomaly_transformer_smoke.md",
        "anomaly_transformer_smoke.md",
    ),
    (
        EXPORT_DIR / "tep_anomaly_transformer_matched_adapter_smoke" / "anomaly_transformer_smoke.json",
        "anomaly_transformer_smoke.json",
    ),
    (
        EXPORT_DIR / "tep_graph_wavenet_matched_adapter_smoke" / "graph_wavenet_smoke.md",
        "graph_wavenet_smoke.md",
    ),
    (
        EXPORT_DIR / "tep_graph_wavenet_matched_adapter_smoke" / "graph_wavenet_smoke.json",
        "graph_wavenet_smoke.json",
    ),
    (
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "hierarchical_edge_probe_admission.md",
        "hierarchical_edge_probe_admission.md",
    ),
    (
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "hierarchical_edge_probe_admission.json",
        "hierarchical_edge_probe_admission.json",
    ),
    (
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "tep_single_edge_validation_probe_smoke.md",
        "tep_single_edge_validation_probe_smoke.md",
    ),
    (
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "tep_single_edge_validation_probe_smoke.json",
        "tep_single_edge_validation_probe_smoke.json",
    ),
    (
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "tep_hierarchical_edge_validation_probe_smoke.md",
        "tep_hierarchical_edge_validation_probe_smoke.md",
    ),
    (
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "tep_hierarchical_edge_validation_probe_smoke.json",
        "tep_hierarchical_edge_validation_probe_smoke.json",
    ),
    (
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "tep_hierarchical_edge_validation_probe_3seed_fullrows.md",
        "tep_hierarchical_edge_validation_probe_3seed_fullrows.md",
    ),
    (
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "tep_hierarchical_edge_validation_probe_3seed_fullrows.json",
        "tep_hierarchical_edge_validation_probe_3seed_fullrows.json",
    ),
    (
        EXPORT_DIR / "edge_admission_protocol_audit" / "aaai_edge_admission_protocol_audit.md",
        "aaai_edge_admission_protocol_audit.md",
    ),
    (
        EXPORT_DIR / "edge_admission_protocol_audit" / "aaai_edge_admission_protocol_audit.json",
        "aaai_edge_admission_protocol_audit.json",
    ),
    (
        REPO_ROOT / "Scripts" / "aaai_edge_admission_protocol_audit.py",
        "aaai_edge_admission_protocol_audit.py",
    ),
    (
        EXPORT_DIR / "ms_gse_rpf_llm_condition_ablation_full" / "llm_condition_verifier_ablation_matrix.md",
        "llm_condition_verifier_ablation_matrix.md",
    ),
    (
        EXPORT_DIR / "ms_gse_rpf_llm_condition_ablation_full" / "llm_condition_verifier_ablation_matrix.json",
        "llm_condition_verifier_ablation_matrix.json",
    ),
    (
        REPO_ROOT / "Scripts" / "llm_condition_verifier_ablation_matrix.py",
        "llm_condition_verifier_ablation_matrix.py",
    ),
]


DEFAULT_REFERENCES = r"""@article{downs1993tep,
  title={A plant-wide industrial process control problem},
  author={Downs, James J. and Vogel, Ernest F.},
  journal={Computers \& Chemical Engineering},
  year={1993},
  note={Verify bibliographic details before submission}
}

@misc{skab2020,
  title={Skoltech Anomaly Benchmark (SKAB)},
  author={Katser, Iurii and Kozitsin, Viacheslav},
  year={2020},
  note={Verify benchmark citation before submission}
}

@misc{helwig2018hydraulic,
  title={Condition monitoring of hydraulic systems data set},
  author={Helwig, Nikolai and Pignanelli, Elena and Schuetze, Andreas},
  year={2018},
  note={Verify benchmark citation before submission}
}

@inproceedings{saxena2008cmapss,
  title={Damage propagation modeling for aircraft engine run-to-failure simulation},
  author={Saxena, Abhinav and Goebel, Kai and Simon, Don and Eklund, Neil},
  booktitle={International Conference on Prognostics and Health Management},
  year={2008},
  note={Verify bibliographic details before submission}
}

@inproceedings{gdn2021,
  title={Graph neural network-based anomaly detection in multivariate time series},
  author={Deng, Ailin and Hooi, Bryan},
  booktitle={AAAI Conference on Artificial Intelligence},
  year={2021},
  note={Verify bibliographic details before submission}
}

@inproceedings{mtadgat2020,
  title={Multivariate time-series anomaly detection via graph attention network},
  author={Zhao, Hang and Wang, Yujing and Duan, Jie and Huang, Congrui and Cao, Defu and Tong, Yunhai and Xu, Bixiong and Bai, Jing and Tong, Jie and Zhang, Qi},
  booktitle={IEEE International Conference on Data Mining},
  year={2020},
  note={Verify bibliographic details before submission}
}

@inproceedings{tranad2022,
  title={TranAD: Deep transformer networks for anomaly detection in multivariate time series data},
  author={Tuli, Shreshth and Casale, Giuliano and Jennings, Nicholas R.},
  booktitle={Proceedings of the VLDB Endowment},
  year={2022},
  note={Verify bibliographic details before submission}
}

@inproceedings{patchtst2023,
  title={A Time Series is Worth 64 Words: Long-term Forecasting with Transformers},
  author={Nie, Yuqi and Nguyen, Nam H. and Sinthong, Phanwadee and Kalagnanam, Jayant},
  booktitle={International Conference on Learning Representations},
  year={2023},
  note={Verify bibliographic details before submission}
}

@inproceedings{anomalytransformer2022,
  title={Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy},
  author={Xu, Jiehui and Wu, Haixu and Wang, Jianmin and Long, Mingsheng},
  booktitle={International Conference on Learning Representations},
  year={2022},
  note={Verify bibliographic details before submission}
}

@inproceedings{graphwavenet2019,
  title={Graph WaveNet for Deep Spatial-Temporal Graph Modeling},
  author={Wu, Zonghan and Pan, Shirui and Long, Guodong and Jiang, Jing and Zhang, Chengqi},
  booktitle={International Joint Conference on Artificial Intelligence},
  year={2019},
  note={Verify bibliographic details before submission}
}
"""


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path | str) -> bool:
    return os.path.exists(_fs_path(path))


def latex_source() -> str:
    """Return the current paper draft as portable LaTeX."""

    return r"""\documentclass[letterpaper]{article}
\usepackage[submission]{aaai2027}
% The serif, sans-serif, and monospaced fonts are loaded automatically by aaai2027.sty.
\usepackage[hyphens]{url}
\usepackage{graphicx}
\urlstyle{rm}
\def\UrlFont{\rm}
\usepackage{natbib}
\usepackage{caption}
\frenchspacing
\usepackage{algorithm}
\usepackage{algorithmic}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\pdfinfo{
/TemplateVersion (2027.1)
}
\setcounter{secnumdepth}{0}

\title{Reliability-Calibrated Mechanism Evidence Fusion}
\author{Anonymous Authors}
\affiliations{Anonymous Submission}

\begin{document}
\maketitle

\begin{abstract}
Industrial time-series fault diagnosis benefits from mechanism knowledge, yet industrial logs usually do not contain interventions. Control loops, delayed compensations, operating-condition shifts, and sparse fault labels make it unsafe to interpret every expert relation, statistical lag, or LLM-generated edge as a true causal effect. This paper studies a reliability-calibrated alternative. We treat expert rules, LLM condition-verifier outputs, lagged relations, residual dynamics, and graph paths as candidate mechanism evidence rather than recovered causal truth. A strong anchor discriminator remains the default predictor, and each mechanism source acts as a challenger that can modify the anchor only after validation-benefit, low-tail safety, counterfactual sensitivity, and source/complexity checks. The resulting Evidence Reliability Estimator learns when a candidate source is locally useful enough to correct the anchor. Across TEP, SKAB, Hydraulic, and C-MAPSS, the current evidence shows that reliability-calibrated mechanism admission improves or safely preserves strong models, with the strongest positive result on strict 22-class TEP fault diagnosis.
\end{abstract}

\section{Introduction}

Industrial time-series fault diagnosis is a natural testbed for knowledge-aware machine learning. Process variables are coupled by material flows, feedback control, delayed compensation, and regime-dependent operating states. A valve fault may first perturb a local flow, then propagate to pressure, temperature, or downstream quality variables after several time lags. These dynamics make purely pointwise diagnosis insufficient: a reliable model must reason over temporal evolution and process structure, while still maintaining strong predictive accuracy.

Existing diagnostic models expose a fundamental tension. Data-driven discriminators, including tree ensembles, temporal convolutional networks, recurrent models, Transformers, and graph-temporal networks, can learn powerful decision boundaries from historical logs. However, they mainly exploit observed statistical regularities, which may include spurious correlations induced by controllers, operating regimes, or label imbalance. Mechanism-aware approaches, such as expert graphs, process knowledge bases, and graph neural networks, provide useful structural priors, but industrial knowledge is often incomplete, static, and regime dependent. Large language models further expand this space by proposing fault mechanisms, key variables, lag ranges, signs, and weak-class rules, yet these proposals can be plausible without being predictive on the actual plant data.

The main difficulty is that real industrial logs are usually non-interventional. Operators rarely perturb valves, flows, temperatures, or pressures solely to identify causal effects, and safety constraints often make such interventions impossible. Consequently, it is unsafe to treat correlations, expert relations, statistical lags, or LLM-generated edges as a recovered true causal graph. This paper therefore studies a more practical and falsifiable question: when multiple unreliable sources provide candidate mechanism evidence, how can a model decide which evidence is reliable enough to correct a strong diagnostic predictor without causing negative transfer?

We formulate this as reliability-calibrated mechanism evidence admission for non-interventional industrial time-series diagnosis. A strong anchor discriminator remains the default predictor. Expert relations, LLM suggestions, lagged statistical relations, residual dynamics, and graph paths are treated as candidate challengers rather than authoritative causes. A challenger can influence the anchor only after passing validation-benefit, low-tail safety, counterfactual sensitivity, source trust, and complexity checks. The admitted evidence enters through constrained residual correction or weak-class verification rather than unchecked global logit editing.

The contributions are:
\begin{itemize}
  \item We reframe mechanism fusion in observational industrial logs as falsifiable candidate evidence admission rather than causal graph discovery.
  \item We introduce an Evidence Reliability Estimator that learns when an expert, LLM, statistical-lag, residual, or graph-path challenger is locally useful enough to correct a strong anchor.
  \item We design hierarchical edge admission: expert, LLM-assisted, and data-driven candidates are probed by source family, target group, lag group, and finally single edge before deployment.
  \item We implement residual/path-gated mechanism intervention so graph evidence can enter as an edge mask, attention bias, channel-fusion gate, or path relation only after reliability admission.
  \item We convert the LLM from an independent edge generator into an expert-graph conditional verifier whose outputs are conditional gate features until data support and validation admission approve them.
  \item We validate the framework through main comparisons, reliability ablations, mechanism ablations, and protocol audits across TEP, SKAB, Hydraulic, and C-MAPSS.
\end{itemize}

\section{Related Work}

\paragraph{Industrial time-series fault diagnosis.}
Classical process-monitoring, fault-diagnosis, and prognostics studies use process variables, temporal windows, and class-specific signatures to identify abnormal states or estimate remaining useful life. Benchmarks such as the Tennessee Eastman process \cite{downs1993tep}, SKAB \cite{skab2020}, Hydraulic \cite{helwig2018hydraulic}, and C-MAPSS \cite{saxena2008cmapss} expose multi-class process faults, run-level anomaly detection, component-state diagnosis, and RUL degradation modeling. Recent models use temporal encoders, reconstruction objectives, Transformers, or strong tabular discriminators to improve prediction. These methods can be effective anchors, but they usually optimize predictive accuracy directly and leave process mechanism evidence either implicit or post-hoc.

\paragraph{Graph and temporal dependency modeling.}
Graph-based time-series methods encode sensor relations, learned adjacency, or attention over variable interactions. Representative anomaly-detection families include graph-deviation and graph-attention approaches \cite{gdn2021,mtadgat2020}, Transformer and patch backbones such as TranAD, Anomaly Transformer, and PatchTST \cite{tranad2022,anomalytransformer2022,patchtst2023}, and graph-temporal forecasting models such as Graph WaveNet \cite{graphwavenet2019}. These approaches motivate the use of structure, but learned adjacency, attention weight, or edge gate is not equivalent to a deployment-safe mechanism claim. A relation can reduce training loss while still being unstable across regimes or harmful for low-tail groups.

\paragraph{LLM-assisted mechanism generation.}
Large language models can generate candidate fault mechanisms, important variables, lag ranges, sign constraints, propagation orders, and confusable counterexamples. This ability is useful for weak classes where labeled data are sparse and expert libraries are incomplete. However, LLM outputs are not measurements and should not be used as direct logit edits or authoritative causal edges. In our framework, the LLM acts conservatively as an expert-graph conditional verifier: it judges whether an expert edge or path should be active under a class, regime, residual state, or temporal pattern, and its output remains a gate feature until data support and reliability admission approve it.

\section{Problem Setup}

For a window or sample $i$, let $x_i$ be the multivariate industrial time-series input, $y_i$ the fault or state label, $r_i$ the residual evidence from normal dynamics, $g_i$ the operating or group context, and $m_k$ the $k$-th candidate mechanism item. A candidate may be an expert edge, an LLM condition-verifier feature for an expert edge or path, a lagged statistical relation, a residual-triggered graph path, or a source-pruned multi-edge structure.

The anchor prediction and candidate challenger predictions are:
\begin{equation}
\begin{aligned}
p_0(i) &= f_0(x_i),\\
p_k(i) &= f_k(x_i, r_i, g_i, m_k),\quad k=1,\ldots,K.
\end{aligned}
\end{equation}

$p_0$ is the default deployed prediction. $p_k$ is a mechanism-conditioned challenger. The problem is to learn when, if ever, $p_k$ should be allowed to modify the anchor. This setup makes the connection between the main classifier and later mechanism layers explicit: mechanism evidence is neither a disconnected explanation nor an unchecked post-processing module.

The anchor is the strong default predictor. A candidate mechanism evidence item is an expert rule, LLM proposal, lagged relation, residual signal, or graph path that may explain or improve a diagnostic decision. A challenger is the prediction route $p_k$ induced by one candidate evidence source. Reliability admission is the global certificate deciding whether a candidate may be deployed at all, and the Evidence Reliability Estimator is the local router estimating whether an admitted challenger should correct the anchor for sample $i$.

\begin{figure*}[t]
  \centering
  \includegraphics[width=0.95\textwidth]{figures/figure1_reliability_calibrated_mechanism_fusion.pdf}
  \caption{Reliability-calibrated mechanism evidence fusion. A strong anchor model remains the default predictor. Expert knowledge, LLM conditional verification, lagged statistics, residual dynamics, and graph paths generate candidate mechanism evidence. Evidence can modify the final prediction only if it passes the reliability certificate and local routing.}
  \label{fig:overview}
\end{figure*}

\section{Method}

\subsection{Anchor-Challenger Formulation}

The anchor model $f_0$ can be a TCN, GRU, Transformer, FT-Transformer, LightGBM, or another strong discriminator selected by the data protocol. The mechanism module does not replace this anchor by default. Instead, each mechanism evidence source creates a challenger. This formulation makes the fusion problem explicit: the question is not whether an auxiliary mechanism is plausible, but whether it is locally useful enough to improve the anchor under validation constraints.

For each candidate $m_k$, we define a local usefulness label:
\begin{equation}
z_{i,k} =
\mathbb{1}\left[
\ell(y_i,p_k(i)) + \delta < \ell(y_i,p_0(i))
\right],
\end{equation}
where $\ell$ is the task loss and $\delta$ is a margin preventing negligible changes from being labeled useful. The Evidence Reliability Estimator predicts:
\begin{equation}
q_{\psi}(i,k) =
\Pr(z_{i,k}=1 \mid x_i, r_i, g_i, \phi(m_k), p_0(i), p_k(i)).
\end{equation}

\subsection{Candidate Mechanism Evidence}

Candidate evidence comes from four sources. Expert evidence contributes process-flow relations, known equipment links, and sign constraints. Statistical evidence contributes lagged variable relations and residual changes under the declared split. LLM evidence no longer contributes independent final edges; it verifies whether expert edges or paths are conditionally active for a class, regime, residual state, or temporal pattern. Graph evidence composes these sources into paths, but the paths are treated as challengers rather than final explanations.

We do not inject a mixed edge pool as a whole. The candidate pool is frozen with source-family tags and then probed hierarchically: expert-only, LLM-only, and data-only source families are tested first; target-group and lag-group probes identify coarse harmful regions; single-edge probes then decide which relations can enter the deployment graph. This prevents a useful edge from being rejected merely because unrelated weak edges were tested in the same pool. Once an edge is admitted, its relation can enter as an edge mask, attention bias, channel-fusion gate, patch/frequency relation mask, or residual channel. The shifted target-minus-source channel used in some graph-temporal probes is therefore only one interface, not the definition of the method.

\subsection{Reliability Certificate}

Each candidate source receives a reliability certificate:
\begin{equation}
R_k =
\sigma(
\alpha_1 G_k -
\alpha_2 H_k +
\alpha_3 C_k +
\alpha_4 S_k -
\alpha_5 B_k),
\end{equation}
where $G_k$ is validation gain over the anchor, $H_k$ is low-tail harm, $C_k$ is counterfactual sensitivity, $S_k$ is source trust, and $B_k$ is complexity burden. The guards are ordered: $G_k$ and low-tail/FAR/MAR safety must pass before $C_k$ is evaluated. Counterfactual sensitivity verifies whether a model route depends on an admitted edge; it does not prove that the edge is useful. The admitted set is:
\begin{equation}
\mathcal{A}_R = \{k \mid R_k \ge \tau_R,\; G_k \ge 0,\; H_k \le \epsilon_H \}.
\end{equation}

This certificate is not an attention weight, edge gate, or static pruning score. It is a deployment admission criterion tied to observable validation benefit, harm control, and perturbation evidence.

\subsection{Reproducible Admission Algorithm}

Algorithm 1 gives the complete validation-only admission rule used by the paper package. First train the anchor $f_0$ and every challenger $f_k$ on the training split. Then freeze the candidate set and evaluate hierarchical probes on the validation split: source-family probes, target-group probes, lag-group probes, and finally single-edge probes. For each candidate, compute $G_k,H_k,C_k,S_k,B_k$, but in a fixed order: validation gain and low-tail/FAR/MAR safety are computed first, and counterfactual sensitivity is computed only after those guards pass. The remaining certificate terms $S_k$ and $B_k$ control source trust and complexity burden. All certificate terms use the same min--max normalization operator within the validation candidate pool, and no test labels are used to select candidates or thresholds. We grid-search only on validation:
\begin{equation}
\begin{aligned}
\mathcal{T}_R &= \{0.55,0.60,0.65,0.70\},\\
\tau_q &\in \{0.50,0.60,0.70\}.
\end{aligned}
\end{equation}
The selected result is a frozen deployment tuple $(f_0,\mathcal{A}_R,q_{\psi},\tau_R,\tau_q,\lambda_{\max})$. At test time this tuple is loaded without re-estimating thresholds, pruning edges, or changing source weights.

\subsection{Difference from Attention, Gates, and Pruning}

The proposed reliability step is not an ordinary gate inserted inside a neural network. An ordinary gate learns a differentiable importance multiplier during training, while our validation-only gate is an external admission decision that can reject a whole evidence source even if the source looks useful inside the training objective. It is also not an attention gate: attention redistributes representation mass among tokens, variables, or neighbors, whereas complete reliability admission decides whether a candidate mechanism can affect deployment at all. It differs from selective prediction because the system still returns a diagnostic or RUL output rather than abstaining. It differs from calibration because calibration changes confidence after a model is trained, whereas deployment risk control decides whether a mechanism challenger is allowed to override the anchor. Finally, it differs from pruning because the certificate combines validation gain, low-tail safety, counterfactual dependence, source trust, and complexity rather than keeping edges only by magnitude or sparsity.

\subsection{Deployment Rule}

At inference time, only admitted candidates can compete with the anchor:
\begin{equation}
k^*(i) =
\arg\max_{k \in \mathcal{A}_R} q_{\psi}(i,k).
\end{equation}
The final prediction is:
\begin{equation}
p^*(i) =
\begin{cases}
(1-\lambda_i)p_0(i)+\lambda_i p_{k^*}(i), & \text{if } q_{\psi}(i,k^*)\ge \tau_q,\\
p_0(i), & \text{otherwise},
\end{cases}
\end{equation}
where $\lambda_i$ is bounded by the reliability score. The anchor therefore remains the fallback whenever evidence is not admitted or locally unconvincing.

\begin{figure}[t]
  \centering
  \includegraphics[width=0.98\linewidth]{figures/figure2_evidence_reliability_admission_loop.pdf}
  \caption{Evidence reliability admission loop. Mechanism evidence is proposed, converted into challengers, tested for validation gain, low-tail harm, counterfactual sensitivity, source trust, and complexity, then admitted or rejected.}
  \label{fig:ere-loop}
\end{figure}

\begin{figure}[t]
  \centering
  \includegraphics[width=0.98\linewidth]{figures/figure3_anchor_challenger_deployment_rule.pdf}
  \caption{Anchor-challenger deployment rule. The strong anchor is retained by default. A mechanism challenger can modify the decision only when the global certificate and local ERE score both pass thresholds.}
  \label{fig:deployment}
\end{figure}

\section{Theory and Claim Boundary}

This framework deliberately avoids claiming that observational logs identify the true causal graph. Instead, it makes a weaker and testable claim: under a fixed protocol, admitted candidate mechanism evidence should improve or preserve the anchor more often than unfiltered evidence. The optimization objective combines anchor learning, challenger learning, ERE calibration, and safety regularization:
\begin{equation}
\mathcal{L} =
\mathcal{L}_{0}
+ \beta_c \mathcal{L}_{c}
+ \beta_r \mathcal{L}_{ERE}
+ \beta_s \mathcal{L}_{safe}.
\end{equation}
The ERE term is supervised by local improvement labels, while the safety term penalizes low-tail harm and over-complex evidence admission. Counterfactual perturbation does not prove true causality; it verifies whether the model's decision uses the proposed mechanism route in the expected direction. This is a reliability test for model dependence, not a claim of physical intervention.

Disallowed claim before additional evidence: the method should not be described as recovering the plant's true causal graph or as proving universal benchmark superiority until matched external protocols, raw seed-level artifacts, and intervention-level evidence are available.

\section{Experiments}

\subsection{Experimental Questions}

The experiments are organized around four questions. RQ1 asks whether the full framework improves strong anchors under matched protocols. RQ2 asks whether reliability admission prevents harmful knowledge injection. RQ3 asks which mechanism sources contribute to performance. RQ4 asks whether the method preserves near-ceiling performance or transfer safety on auxiliary datasets.

\subsection{Datasets and Protocols}

TEP is the primary 22-class mechanism-diagnosis benchmark. SKAB evaluates binary anomaly detection and dynamic graph evidence in valve-related industrial time series. Hydraulic evaluates four component-state targets with near-ceiling baselines. C-MAPSS evaluates original terminal RUL regression and transfer across operating settings. We report strong matched-protocol evidence under stated protocols, not universal official SOTA claims, unless the split, preprocessing, metrics, thresholding, scoring rule, and training budget are exactly aligned with an external benchmark.

Split and leakage control are fixed before model selection: training data fit anchors and challengers, validation data select reliability thresholds and admitted candidates, and test data are used once for reporting. Window / label construction follows the dataset task rather than a single artificial target: TEP and SKAB use time-series windows for diagnosis or anomaly labels, Hydraulic uses component-state labels, and C-MAPSS uses terminal test-unit RUL. Metric and thresholding are likewise task-specific but validation-only: macro/target F1 for diagnosis or anomaly detection and RMSE/MAE/score for RUL. Seeds / budget are recorded for each formal run so that model families are compared under matched training limits. No test-set threshold or route tuning is allowed after the frozen deployment tuple is selected. Same reliability equation across datasets means that evidence admission remains comparable even when the anchor architecture changes. For C-MAPSS, a train-unit pseudo-terminal validation audit independently selects the same w160/cap150 temporal anchor by RMSE; it also discloses that PHM score has a secondary trade-off, so C-MAPSS is used as transfer evidence rather than a path-fusion or leaderboard claim.

\begin{table*}[t]
\centering
\caption{Main matched-protocol results summarized from current experiment artifacts. Public leaderboard wording requires exact external protocol alignment.}
\label{tab:main-results}
\small
\begin{tabular}{p{0.11\textwidth}p{0.19\textwidth}p{0.20\textwidth}p{0.14\textwidth}p{0.24\textwidth}}
\toprule
Dataset & Task & Strong Anchor & Proposed & Main Evidence \\
\midrule
TEP & 22-class fault diagnosis & $0.9122 \pm 0.0134$ & $0.9549 \pm 0.0023$ & strict mechanism diagnosis \\
SKAB & anomaly detection & $0.8193 \pm 0.0283$ & $0.8450 \pm 0.0189$ & native-audited algorithmic anchor; LLM diagnostic \\
Hydraulic & four state targets & $0.9773 \pm 0.0321$ & $0.9784 \pm 0.0301$ & low-tail non-degradation \\
C-MAPSS & terminal RUL & GRU w80/cap125 RMSE $20.7559$ & GRU w160/cap150 RMSE $18.0617$ & cap/window repair; path fusion closed \\
\bottomrule
\end{tabular}
\end{table*}

\begin{figure*}[t]
  \centering
  \includegraphics[width=0.98\textwidth]{figures/main_multi_benchmark_results.png}
  \caption{Main matched-protocol experiment results. C-MAPSS is normalized from RMSE because lower is better, while the dedicated RUL figure reports the original units.}
  \label{fig:main-experiment}
\end{figure*}

\subsection{Matched Backbone Controls}

To separate mechanism-evidence fusion from simply choosing a fashionable temporal backbone, we also ran local matched adapters for three strong external families: PatchTST, Anomaly Transformer, and Graph WaveNet. These are not official external scores because their native tasks are forecasting, anomaly scoring, or traffic forecasting rather than strict 22-class TEP diagnosis. Under the same TEP adapter protocol, the three-seed probes are much weaker than the reliability-calibrated mechanism route (Table~\ref{tab:backbone-controls}). We therefore use them as negative controls: they support the paper's claim that the main contribution is reliable admission of mechanism evidence, not direct transplantation of a generic backbone. We additionally archive official-source adapted budget probes for PatchTST, Anomaly Transformer, and Graph WaveNet. These runs fix source provenance but still add task-specific heads or protocol patches; PatchTST reaches only $0.4197 \pm 0.0320$ TEP Target-F1, Graph WaveNet reaches $0.2854 \pm 0.0529$, and Anomaly Transformer reaches $0.4716 \pm 0.0487$ SKAB Macro-F1 with 100\% FAR. They remain supporting negative controls rather than official external benchmark scores.

\begin{table}[t]
\centering
\caption{Official-source adapted matched controls. These rows fix source provenance but remain negative controls, not official external benchmark scores.}
\label{tab:backbone-controls}
\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{p{0.25\linewidth}p{0.23\linewidth}p{0.34\linewidth}}
\toprule
Backbone & Native family & Matched result \\
\midrule
PatchTST & patch Transformer forecasting & TEP Target-F1 $0.4197 \pm 0.0320$ \\
Graph WaveNet & adaptive graph-temporal forecasting & TEP Target-F1 $0.2854 \pm 0.0529$ \\
Anomaly Transformer & assoc.-discrepancy anomaly scoring & SKAB Macro-F1 $0.4716 \pm 0.0487$, FAR $100\%$ \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Efficiency Audit}

We report efficiency only when the seed-level JSON artifact records parameter count, training time, and inference throughput. SKAB, C-MAPSS, and the TEP GDN/MTAD sequence baselines currently satisfy this requirement. For TEP, efficiency is measured from timed reruns, while the performance comparison preserves the best recovered target-F1 rows.

\begin{table*}[t]
\centering
\caption{Measured efficiency evidence. TEP sequence efficiency uses full-budget timed reruns; TEP performance comparisons keep the best recovered target-F1 rows.}
\label{tab:efficiency}
\small
\begin{tabular}{lrrr}
\toprule
Branch & Params & Train sec. & Test samples/s \\
\midrule
SKAB anchor & 88,716 & 340.54 & 2,988.7 \\
SKAB LLM verifier & 88,716 & 345.44 & 2,939.9 \\
C-MAPSS RUL anchor & 119,183 & 62.84 & 9,667.1 \\
C-MAPSS AnchorPath-BiGRU challenger & 382,162 & 147.46 & 8,341.6 \\
TEP GDN no/resid. & 17,942 / 35,885 & 0.47 / 0.63 & 586,309.7 / 330,096.4 \\
TEP MTAD no/resid. & 92,055 / 184,111 & 0.66 / 1.07 & 476,639.1 / 254,825.4 \\
\bottomrule
\end{tabular}
\end{table*}

\subsection{Ablations}

The ablation design separates three effects: the strength of the anchor, the benefit of mechanism challengers, and the reliability of admission. Removing reliability admission tests whether unfiltered expert or LLM-conditioned edges cause negative transfer. Removing LLM condition-verifier features tests whether semantic expert-edge activation helps difficult classes after validation. Removing lagged graph and residual channels tests whether temporal propagation evidence is necessary beyond static window features.

\begin{table}[t]
\centering
\caption{Ablation logic for internal mechanism validation.}
\label{tab:ablation}
\small
\begin{tabular}{p{0.30\linewidth}p{0.60\linewidth}}
\toprule
Variant & Purpose \\
\midrule
Anchor only & Tests base temporal discrimination \\
All evidence, no ERE & Tests unsafe knowledge injection \\
Expert only & Tests hand-written mechanism value \\
LLM only & Tests conditional expert-edge verification features \\
Lag/residual only & Tests temporal propagation evidence \\
Full model & Tests reliability-calibrated fusion \\
\bottomrule
\end{tabular}
\end{table}

\begin{figure*}[t]
  \centering
  \includegraphics[width=0.98\textwidth]{figures/tep_mechanism_ablation.png}
  \caption{TEP mechanism ablation. The results show that improvement is not merely from adding more features, but from reliability-controlled mechanism admission.}
  \label{fig:ablation}
\end{figure*}

\subsection{Safety and Transfer}

Safety experiments evaluate whether the framework avoids damaging high-performing anchors and low-tail groups. Counterfactual edge perturbations test model dependence on admitted paths, while source and complexity penalties prevent dense LLM-generated graphs from overwhelming observed evidence. The expected outcome is not that every dataset reaches a universal leaderboard state-of-the-art score, but that admitted evidence improves the anchor when useful and falls back safely when unreliable.

\begin{figure*}[t]
  \centering
  \includegraphics[width=0.98\textwidth]{figures/reliability_ablation_summary.png}
  \caption{Reliability ablation summary. The framework is evaluated by validation admission, unsafe prior-only/all-edge contrasts, source pruning, and original-task RUL transfer.}
  \label{fig:safety}
\end{figure*}

\begin{figure}[t]
  \centering
  \includegraphics[width=0.98\linewidth]{figures/cmapss_rul_matched_results.png}
  \caption{C-MAPSS original terminal RUL regression. Lower RMSE is better; the current reliable branch is the cap-corrected long-window temporal anchor, and a train-unit pseudo-terminal audit selects the same configuration by RMSE while reporting a PHM-score trade-off. AnchorPath-BiGRU remains a non-admitted path-fusion challenger.}
  \label{fig:cmapss-rul}
\end{figure}

\section{Limitations}

The current framework provides reliability-calibrated evidence admission, not physical causal discovery. Counterfactual perturbation verifies model dependence on a proposed route; it does not replace plant-level intervention. The present evidence should be described as strong matched-protocol evidence until official benchmark protocols are exactly reproduced. The strongest current claim is mechanism-aware improvement and safe preservation across diverse industrial datasets, with TEP serving as the primary multi-class diagnosis setting.

\section{Conclusion}

We presented a reliability-calibrated framework for using imperfect mechanism evidence in industrial time-series fault diagnosis. The central idea is to keep a strong anchor predictor as the default and allow expert, LLM, lagged, residual, and graph evidence to correct it only when that evidence is validated, safe, and locally useful. This turns mechanism fusion from unchecked knowledge injection into a testable anchor-challenger admission problem, making the approach more suitable for non-interventional industrial settings where real causal verification is rarely available.

\bibliography{references}

\end{document}
"""


def copy_required_file(source: Path, destination: Path) -> Path:
    if not _exists(source):
        raise FileNotFoundError(f"Required artifact not found: {source}")
    os.makedirs(_fs_path(destination.parent), exist_ok=True)
    shutil.copy2(_fs_path(source), _fs_path(destination))
    return destination


def _ensure_core_figures() -> None:
    core_expected = [
        CORE_FIGURE_DIR / "figure1_reliability_calibrated_mechanism_fusion.pdf",
        CORE_FIGURE_DIR / "figure1_reliability_calibrated_mechanism_fusion.png",
        CORE_FIGURE_DIR / "figure2_evidence_reliability_admission_loop.pdf",
        CORE_FIGURE_DIR / "figure2_evidence_reliability_admission_loop.png",
        CORE_FIGURE_DIR / "figure3_anchor_challenger_deployment_rule.pdf",
        CORE_FIGURE_DIR / "figure3_anchor_challenger_deployment_rule.png",
    ]
    missing = [path for path in core_expected if not _exists(path)]
    if not missing:
        return
    from render_core_paper_figures import render_all_core_figures

    render_all_core_figures(CORE_FIGURE_DIR)


def _ensure_external_baseline_alignment_decision() -> None:
    expected = [
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "aaai_external_baseline_alignment_decision.md",
        EXPORT_DIR / "aaai_external_baseline_alignment_decision" / "aaai_external_baseline_alignment_decision.json",
    ]
    missing = [path for path in expected if not _exists(path)]
    if not missing:
        from aaai_sota_gap_ledger import write_sota_gap_ledger

        write_sota_gap_ledger(EXPORT_DIR / "aaai_exact_native_protocol_gate")
        return
    from aaai_external_baseline_alignment_decision import build_external_baseline_alignment_decision

    build_external_baseline_alignment_decision(EXPORT_DIR / "aaai_external_baseline_alignment_decision")


def _ensure_external_baseline_official_repo_snapshot() -> None:
    expected = [
        EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_snapshot.md",
        EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_snapshot.json",
    ]
    missing = [path for path in expected if not _exists(path)]
    if not missing:
        return
    from snapshot_external_baseline_repos import build_official_repo_snapshot

    build_official_repo_snapshot(
        EXPORT_DIR / "external_baseline_official_repos",
        allow_network=False,
    )


def _ensure_external_baseline_checkout_audit() -> None:
    expected = [
        EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_checkout_audit.md",
        EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_checkout_audit.json",
    ]
    missing = [path for path in expected if not _exists(path)]
    if not missing:
        return
    from checkout_external_baseline_repos import build_checkout_audit

    build_checkout_audit(
        EXPORT_DIR / "external_baseline_official_repos",
        skip_clone=True,
    )


def _ensure_anomaly_transformer_official_skab_adapter() -> None:
    expected = [
        EXPORT_DIR
        / "external_baseline_protocol_runs"
        / "anomaly_transformer_official_skab_adapter"
        / "anomaly_transformer_official_skab_adapter.md",
        EXPORT_DIR
        / "external_baseline_protocol_runs"
        / "anomaly_transformer_official_skab_adapter"
        / "anomaly_transformer_official_skab_adapter.json",
    ]
    missing = [path for path in expected if not _exists(path)]
    if not missing:
        return
    from prepare_anomaly_transformer_skab_official_adapter import (
        DEFAULT_PUBLIC_DATASET_ROOT,
        build_adapter_payload,
        write_adapter_artifacts,
    )

    output_root = EXPORT_DIR / "external_baseline_protocol_runs" / "anomaly_transformer_official_skab_adapter"
    payload = build_adapter_payload(
        DEFAULT_PUBLIC_DATASET_ROOT,
        output_root,
        seeds=[42, 43, 44],
        win_size=48,
        batch_size=256,
        epochs=10,
    )
    write_adapter_artifacts(payload, output_root)


def _ensure_hierarchical_edge_probe_admission() -> None:
    expected = [
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "hierarchical_edge_probe_admission.md",
        EXPORT_DIR / "hierarchical_edge_probe_admission" / "hierarchical_edge_probe_admission.json",
    ]
    missing = [path for path in expected if not _exists(path)]
    if not missing:
        return
    from hierarchical_edge_probe_admission import build_default_hierarchical_artifact

    build_default_hierarchical_artifact(EXPORT_DIR / "hierarchical_edge_probe_admission")


def _ensure_edge_admission_protocol_audit() -> None:
    expected = [
        EXPORT_DIR / "edge_admission_protocol_audit" / "aaai_edge_admission_protocol_audit.md",
        EXPORT_DIR / "edge_admission_protocol_audit" / "aaai_edge_admission_protocol_audit.json",
    ]
    missing = [path for path in expected if not _exists(path)]
    if not missing:
        return
    from aaai_edge_admission_protocol_audit import write_protocol_audit

    write_protocol_audit(EXPORT_DIR / "edge_admission_protocol_audit")


def _ensure_exact_native_protocol_gate() -> None:
    expected = [
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_exact_native_protocol_gate.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_exact_native_protocol_gate.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_exact_native_execution_plan.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_exact_native_execution_plan.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_sota_gap_ledger.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "aaai_sota_gap_ledger.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_baseline_gate.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_baseline_gate.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_repository_baseline_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_repository_baseline_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_source_rerun_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_official_source_rerun_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_source_rerun_delta_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_source_rerun_delta_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_native_metric_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "skab_native_metric_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_native_preprocessing_manifest.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_native_preprocessing_manifest.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_published_baseline_alignment.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_published_baseline_alignment.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_published_baseline_contract.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_published_baseline_contract.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_lstm_source_protocol_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_lstm_source_protocol_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_open_protocol_candidate_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_open_protocol_candidate_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_source_profile.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_source_profile.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_runner_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_runner_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_strategy_probe_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_strategy_probe_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_rul_backbone_optimization_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_rul_backbone_optimization_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_pseudo_truncation_validation_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_pseudo_truncation_validation_audit.json",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_exact_native_gap_audit.md",
        EXPORT_DIR / "aaai_exact_native_protocol_gate" / "cmapss_exact_native_gap_audit.json",
    ]
    missing = [path for path in expected if not _exists(path)]
    if not missing:
        from aaai_sota_gap_ledger import write_sota_gap_ledger
        from skab_official_baseline_gate import write_skab_official_baseline_gate
        from skab_official_repository_baseline_audit import write_skab_official_repository_baseline_audit
        from skab_official_source_rerun_audit import write_skab_official_source_rerun_audit
        from skab_source_rerun_delta_audit import write_skab_source_rerun_delta_audit
        from cmapss_exact_native_gap_audit import write_cmapss_exact_native_gap_audit

        write_skab_official_repository_baseline_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
        write_skab_official_source_rerun_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
        write_skab_source_rerun_delta_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
        write_skab_official_source_rerun_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
        write_skab_official_baseline_gate(EXPORT_DIR / "aaai_exact_native_protocol_gate")
        write_sota_gap_ledger(EXPORT_DIR / "aaai_exact_native_protocol_gate")
        write_cmapss_exact_native_gap_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
        return
    from aaai_exact_native_protocol_gate import write_exact_native_protocol_gate
    from aaai_exact_native_execution_plan import write_exact_native_execution_plan
    from aaai_sota_gap_ledger import write_sota_gap_ledger
    from skab_official_baseline_gate import write_skab_official_baseline_gate
    from skab_official_repository_baseline_audit import write_skab_official_repository_baseline_audit
    from skab_official_source_rerun_audit import write_skab_official_source_rerun_audit
    from skab_source_rerun_delta_audit import write_skab_source_rerun_delta_audit
    from skab_native_metric_audit import write_skab_native_metric_audit
    from cmapss_native_preprocessing_manifest import write_cmapss_native_preprocessing_manifest
    from cmapss_published_baseline_alignment import write_cmapss_published_baseline_alignment
    from cmapss_published_baseline_contract import write_cmapss_published_baseline_contract
    from cmapss_lstm_source_protocol_audit import write_cmapss_lstm_source_protocol_audit
    from cmapss_open_protocol_candidate_audit import write_cmapss_open_protocol_candidate_audit
    from cmapss_mdfa_source_profile import write_cmapss_mdfa_source_profile
    from cmapss_mdfa_runner_audit import write_cmapss_mdfa_runner_audit
    from cmapss_mdfa_strategy_probe_audit import write_mdfa_strategy_probe_audit
    from cmapss_rul_backbone_optimization_audit import write_cmapss_rul_backbone_optimization_audit
    from cmapss_exact_native_gap_audit import write_cmapss_exact_native_gap_audit

    write_exact_native_protocol_gate(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_exact_native_execution_plan(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_skab_official_repository_baseline_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_skab_official_source_rerun_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_skab_source_rerun_delta_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_skab_official_source_rerun_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_skab_native_metric_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_skab_official_baseline_gate(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_rul_backbone_optimization_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_native_preprocessing_manifest(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_published_baseline_alignment(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_published_baseline_contract(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_lstm_source_protocol_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_open_protocol_candidate_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_mdfa_source_profile(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_mdfa_runner_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_mdfa_strategy_probe_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_sota_gap_ledger(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_exact_native_gap_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_native_preprocessing_manifest(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_published_baseline_alignment(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_published_baseline_contract(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_lstm_source_protocol_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_open_protocol_candidate_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_mdfa_source_profile(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_mdfa_runner_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_mdfa_strategy_probe_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_sota_gap_ledger(EXPORT_DIR / "aaai_exact_native_protocol_gate")
    write_cmapss_exact_native_gap_audit(EXPORT_DIR / "aaai_exact_native_protocol_gate")


def _write_references(destination: Path) -> Path:
    os.makedirs(_fs_path(destination.parent), exist_ok=True)
    if _exists(REFERENCES):
        shutil.copy2(_fs_path(REFERENCES), _fs_path(destination))
    else:
        with open(_fs_path(destination), "w", encoding="utf-8") as handle:
            handle.write(DEFAULT_REFERENCES)
    return destination


def _copy_official_template_assets(output_path: Path) -> list[Path]:
    written: list[Path] = []
    for source in OFFICIAL_TEMPLATE_FILES:
        if not _exists(source):
            continue
        if source.suffix in {".sty", ".bst"}:
            destination = output_path / source.name
        else:
            destination = output_path / "official_author_kit" / source.name
        written.append(copy_required_file(source, destination))
    return written


def build_latex_draft(output_dir: Path | str) -> list[Path]:
    """Create the LaTeX draft package and return written paths."""

    output_path = Path(output_dir)
    os.makedirs(_fs_path(output_path), exist_ok=True)
    _ensure_core_figures()
    _ensure_external_baseline_official_repo_snapshot()
    _ensure_external_baseline_checkout_audit()
    _ensure_anomaly_transformer_official_skab_adapter()
    _ensure_external_baseline_alignment_decision()
    _ensure_hierarchical_edge_probe_admission()
    _ensure_edge_admission_protocol_audit()
    _ensure_exact_native_protocol_gate()

    written: list[Path] = []

    main_tex = output_path / "main.tex"
    with open(_fs_path(main_tex), "w", encoding="utf-8") as handle:
        handle.write(latex_source())
    written.append(main_tex)

    references_out = output_path / "references.bib"
    written.append(_write_references(references_out))
    written.extend(_copy_official_template_assets(output_path))

    figures_dir = output_path / "figures"
    for source in FIGURES:
        written.append(copy_required_file(source, figures_dir / source.name))

    for source, relative_destination in SUPPORTING_ARTIFACTS:
        if _exists(source):
            written.append(copy_required_file(source, output_path / relative_destination))

    readme = output_path / "README.md"
    with open(_fs_path(readme), "w", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "# AAAI LaTeX Draft Package",
                    "",
                    "This directory is generated by `Scripts/build_aaai_latex_draft.py`.",
                    "It uses the official AAAI-27 submission style when `aaai2027.sty` is available in `knowledge_exports/official_aaai_template/AuthorKit27`.",
                    "It remains a draft until LaTeX compilation and float inspection pass under the official style.",
                    "",
                    "Recommended next steps:",
                    "1. Compile `main.tex` with the copied `aaai2027.sty` and `aaai2027.bst`.",
                    "2. Re-run protocol audits before converting matched-protocol wording into stronger claims.",
                    "3. Verify fallback BibTeX metadata against official sources before submission.",
                    "4. Compile `main.tex` and inspect figure sizing before final submission polishing.",
                    "",
                ]
            )
        )
    written.append(readme)

    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=EXPORT_DIR / "aaai_latex_draft",
        help="Directory where the LaTeX package will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written = build_latex_draft(args.output_dir)
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
