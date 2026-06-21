import tempfile
import unittest
from pathlib import Path

from build_aaai_latex_draft import build_latex_draft


class BuildAaaiLatexDraftTest(unittest.TestCase):
    def test_build_latex_draft_writes_source_bibliography_and_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            written = build_latex_draft(output_dir)

            written_names = {path.relative_to(output_dir).as_posix() for path in written}
            expected = {
                "main.tex",
                "references.bib",
                "aaai2027.sty",
                "aaai2027.bst",
                "official_author_kit/AnonymousSubmission2027.tex",
                "official_author_kit/ReproducibilityChecklist.tex",
                "figures/figure1_reliability_calibrated_mechanism_fusion.pdf",
                "figures/figure1_reliability_calibrated_mechanism_fusion.png",
                "figures/figure2_evidence_reliability_admission_loop.pdf",
                "figures/figure2_evidence_reliability_admission_loop.png",
                "figures/figure3_anchor_challenger_deployment_rule.pdf",
                "figures/figure3_anchor_challenger_deployment_rule.png",
                "figures/main_multi_benchmark_results.png",
                "figures/reliability_ablation_summary.png",
                "figures/tep_mechanism_ablation.png",
                "figures/cmapss_rul_matched_results.png",
                "aaai_experiment_execution_manifest.md",
                "aaai_experiment_execution_manifest.json",
                "aaai_pending_baseline_gate.md",
                "aaai_pending_baseline_gate.json",
                "protocol_aligned_external_baseline_runner.py",
                "run_public_ms_gse_rpf_experiment.py",
                "run_cmapss_rul_baselines.py",
                "run_cmapss_mdfa_source_matched.py",
                "skab_native_metric_audit.py",
                "skab_official_baseline_gate.py",
                "skab_official_repository_baseline_audit.py",
                "skab_official_source_rerun_audit.py",
                "skab_source_rerun_delta_audit.py",
                "aaai_sota_gap_ledger.py",
                "skab_external_baselines.py",
                "cmapss_native_preprocessing_manifest.py",
                "cmapss_published_baseline_alignment.py",
                "cmapss_published_baseline_contract.py",
                "cmapss_lstm_source_protocol_audit.py",
                "cmapss_open_protocol_candidate_audit.py",
                "cmapss_mdfa_source_profile.py",
                "cmapss_mdfa_runner_audit.py",
                "cmapss_mdfa_strategy_probe_audit.py",
                "cmapss_rul_backbone_optimization_audit.py",
                "cmapss_pseudo_truncation_validation_audit.py",
                "cmapss_exact_native_gap_audit.py",
                "checkout_external_baseline_repos.py",
                "prepare_anomaly_transformer_skab_official_adapter.py",
                "run_anomaly_transformer_skab_official_wrapper.py",
                "run_patchtst_tep_official_wrapper.py",
                "run_graph_wavenet_tep_official_wrapper.py",
                "patchtst_seed42_dry_run_plan.json",
                "skab_anomaly_transformer_seed42_dry_run_plan.json",
                "skab_anomaly_transformer_smoke.json",
                "skab_anomaly_transformer_3seed_probe.md",
                "skab_anomaly_transformer_3seed_probe.json",
                "skab_external_baselines_native_records_usad_tranad_w48_e8.json",
                "anomaly_transformer_official_skab_adapter.md",
                "anomaly_transformer_official_skab_adapter.json",
                "anomaly_transformer_official_skab_wrapper_smoke.md",
                "anomaly_transformer_official_skab_wrapper_smoke.json",
                "anomaly_transformer_official_skab_wrapper_3seed_probe.md",
                "anomaly_transformer_official_skab_wrapper_3seed_probe.json",
                "anomaly_transformer_official_skab_wrapper_3seed_budget_probe.md",
                "anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json",
                "patchtst_official_tep_wrapper_smoke.md",
                "patchtst_official_tep_wrapper_smoke.json",
                "patchtst_official_tep_wrapper_3seed_probe.md",
                "patchtst_official_tep_wrapper_3seed_probe.json",
                "patchtst_official_tep_wrapper_3seed_budget_probe.md",
                "patchtst_official_tep_wrapper_3seed_budget_probe.json",
                "graph_wavenet_official_tep_wrapper_smoke.md",
                "graph_wavenet_official_tep_wrapper_smoke.json",
                "graph_wavenet_official_tep_wrapper_3seed_probe.md",
                "graph_wavenet_official_tep_wrapper_3seed_probe.json",
                "graph_wavenet_official_tep_wrapper_3seed_budget_probe.md",
                "graph_wavenet_official_tep_wrapper_3seed_budget_probe.json",
                "aaai_ablation_coverage_audit.md",
                "aaai_ablation_coverage_audit.json",
                "aaai_missing_ablation_execution_plan.md",
                "aaai_missing_ablation_execution_plan.json",
                "paper_protocol_sota_audit.md",
                "aaai_exact_native_protocol_gate.md",
                "aaai_exact_native_protocol_gate.json",
                "aaai_exact_native_execution_plan.md",
                "aaai_exact_native_execution_plan.json",
                "aaai_sota_gap_ledger.md",
                "aaai_sota_gap_ledger.json",
                "skab_official_baseline_gate.md",
                "skab_official_baseline_gate.json",
                "skab_official_repository_baseline_audit.md",
                "skab_official_repository_baseline_audit.json",
                "skab_official_source_rerun_audit.md",
                "skab_official_source_rerun_audit.json",
                "skab_source_rerun_delta_audit.md",
                "skab_source_rerun_delta_audit.json",
                "skab_native_metric_audit.md",
                "skab_native_metric_audit.json",
                "cmapss_native_preprocessing_manifest.md",
                "cmapss_native_preprocessing_manifest.json",
                "cmapss_published_baseline_alignment.md",
                "cmapss_published_baseline_alignment.json",
                "cmapss_published_baseline_contract.md",
                "cmapss_published_baseline_contract.json",
                "cmapss_lstm_source_protocol_audit.md",
                "cmapss_lstm_source_protocol_audit.json",
                "cmapss_open_protocol_candidate_audit.md",
                "cmapss_open_protocol_candidate_audit.json",
                "cmapss_mdfa_source_profile.md",
                "cmapss_mdfa_source_profile.json",
                "cmapss_mdfa_runner_audit.md",
                "cmapss_mdfa_runner_audit.json",
                "cmapss_mdfa_strategy_probe_audit.md",
                "cmapss_mdfa_strategy_probe_audit.json",
                "cmapss_mdfa_source_matched_smoke_summary.md",
                "cmapss_mdfa_source_matched_smoke_summary.json",
                "cmapss_rul_backbone_optimization_audit.md",
                "cmapss_rul_backbone_optimization_audit.json",
                "cmapss_pseudo_truncation_validation_audit.md",
                "cmapss_pseudo_truncation_validation_audit.json",
                "cmapss_exact_native_gap_audit.md",
                "cmapss_exact_native_gap_audit.json",
                "cmapss_lstm_published_style_w80_cap125_summary.md",
                "cmapss_lstm_published_style_w80_cap125_summary.json",
                "reference_verification_report.md",
                "aaai_external_baseline_alignment_decision.md",
                "aaai_external_baseline_alignment_decision.json",
                "official_external_repo_snapshot.md",
                "official_external_repo_snapshot.json",
                "official_external_repo_checkout_audit.md",
                "official_external_repo_checkout_audit.json",
                "anomaly_transformer_tep_smoke_alignment_artifact.json",
                "anomaly_transformer_skab_smoke_alignment_artifact.json",
                "anomaly_transformer_skab_3seed_alignment_artifact.json",
                "graph_wavenet_tep_smoke_alignment_artifact.json",
                "patchtst_tep_3seed_alignment_artifact.json",
                "anomaly_transformer_tep_3seed_alignment_artifact.json",
                "graph_wavenet_tep_3seed_alignment_artifact.json",
                "patchtst_3seed_probe.md",
                "patchtst_3seed_probe.json",
                "anomaly_transformer_3seed_probe.md",
                "anomaly_transformer_3seed_probe.json",
                "graph_wavenet_3seed_probe.md",
                "graph_wavenet_3seed_probe.json",
                "anomaly_transformer_smoke.md",
                "anomaly_transformer_smoke.json",
                "graph_wavenet_smoke.md",
                "graph_wavenet_smoke.json",
                "hierarchical_edge_probe_admission.md",
                "hierarchical_edge_probe_admission.json",
                "tep_single_edge_validation_probe_smoke.md",
                "tep_single_edge_validation_probe_smoke.json",
                "tep_hierarchical_edge_validation_probe_smoke.md",
                "tep_hierarchical_edge_validation_probe_smoke.json",
                "tep_hierarchical_edge_validation_probe_3seed_fullrows.md",
                "tep_hierarchical_edge_validation_probe_3seed_fullrows.json",
                "aaai_edge_admission_protocol_audit.md",
                "aaai_edge_admission_protocol_audit.json",
                "aaai_edge_admission_protocol_audit.py",
                "llm_condition_verifier_ablation_matrix.md",
                "llm_condition_verifier_ablation_matrix.json",
                "llm_condition_verifier_ablation_matrix.py",
                "README.md",
            }

            self.assertTrue(expected.issubset(written_names))
            for relative_name in expected:
                path = output_dir / relative_name
                self.assertTrue(path.exists(), relative_name)
                self.assertGreater(path.stat().st_size, 100, relative_name)

    def test_main_tex_contains_aaai_ready_structure_and_claim_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            build_latex_draft(output_dir)

            tex = (output_dir / "main.tex").read_text(encoding="utf-8")
            self.assertIn(r"\documentclass[letterpaper]{article}", tex)
            self.assertIn(r"\usepackage[submission]{aaai2027}", tex)
            self.assertIn(r"\title{Reliability-Calibrated Mechanism Evidence Fusion}", tex)
            self.assertIn(r"\section{Introduction}", tex)
            self.assertIn(r"\section{Problem Setup}", tex)
            self.assertIn(r"\section{Method}", tex)
            self.assertIn(r"\section{Experiments}", tex)
            self.assertIn(r"\section{Limitations}", tex)
            self.assertIn("non-interventional industrial time-series", tex)
            self.assertIn("candidate mechanism evidence", tex)
            self.assertIn("probed hierarchically", tex)
            self.assertIn("source-family probes", tex)
            self.assertIn("expert-graph conditional verifier", tex)
            self.assertIn("LLM condition-verifier feature", tex)
            self.assertIn("Counterfactual sensitivity verifies", tex)
            self.assertIn("Evidence Reliability Estimator", tex)
            self.assertIn("strong matched-protocol evidence", tex)
            self.assertIn("$0.9549 \\pm 0.0023$", tex)
            self.assertIn("$0.8450 \\pm 0.0189$", tex)
            self.assertIn("LLM diagnostic", tex)
            self.assertIn("GRU w80/cap125 RMSE $20.7559$", tex)
            self.assertIn("GRU w160/cap150 RMSE $18.0617$", tex)
            self.assertIn("path fusion closed", tex)
            self.assertIn("pseudo-terminal validation audit", tex)
            self.assertIn("PHM-score trade-off", tex)
            self.assertNotIn("92--95+ target range", tex)
            self.assertNotIn("SOTA-candidate", tex)
            self.assertIn("original terminal RUL regression", tex)
            self.assertIn("cmapss_rul_matched_results.png", tex)
            self.assertIn("figure1_reliability_calibrated_mechanism_fusion.pdf", tex)
            self.assertIn(r"\subsection{Efficiency Audit}", tex)
            self.assertIn("Test samples/s", tex)
            self.assertIn("TEP MTAD no/resid.", tex)
            self.assertIn(r"\subsection{Matched Backbone Controls}", tex)
            self.assertIn("PatchTST", tex)
            self.assertIn("Anomaly Transformer", tex)
            self.assertIn("Graph WaveNet", tex)
            self.assertIn("Official-source adapted matched controls", tex)
            self.assertIn("$0.4197 \\pm 0.0320$", tex)
            self.assertIn("$0.2854 \\pm 0.0529$", tex)
            self.assertIn("$0.4716 \\pm 0.0487$", tex)
            self.assertIn("FAR $100\\%$", tex)
            self.assertIn("negative controls", tex)
            self.assertNotIn("LLM as a weak-class mechanism proposer", tex)
            self.assertIn(r"\includegraphics", tex)
            self.assertIn(r"\bibliography{references}", tex)
            self.assertNotIn(r"\usepackage[margin=1in]{geometry}", tex)
            self.assertNotIn(r"\usepackage[colorlinks", tex)
            self.assertNotIn(r"\bibliographystyle{plainnat}", tex)
            self.assertNotIn("we recover the true causal graph", tex.lower())


if __name__ == "__main__":
    unittest.main()
