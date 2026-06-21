from __future__ import annotations

import unittest

from summarize_ms_gse_rpf_results import _feature_group_name, aggregate, render_markdown


class SummarizeMSGserpfResultsTest(unittest.TestCase):
    def test_group_path_jaccard_collapses_stat_suffixes_only(self) -> None:
        self.assertEqual(_feature_group_name("PS2_mean"), "PS2")
        self.assertEqual(_feature_group_name("PS2_last_minus_first"), "PS2")
        self.assertEqual(_feature_group_name("sensor_02"), "sensor_02")

        rows = [
            {
                "dataset": "hydraulic",
                "target": "valve",
                "variant": "full",
                "seed": 1,
                "primary_test_metrics": {"macro_f1": 0.8, "balanced_accuracy": 0.81},
                "efficiency": {
                    "test_inference_samples_per_second": 100.0,
                    "parameters": 10,
                    "path_aux_weight": 0.05,
                    "coarse_aux_weight": 0.1,
                    "health_aux_weight": 0.2,
                    "test_health_mae": 0.1,
                },
                "diagnostics": {
                    "config": {"use_context_router": True},
                    "test_diagnostics": {"mean_path_context_importance": 0.2, "mean_class_evidence_admission": 0.8},
                },
                "path_budget": {
                    "path_coverage_mode": "target_group",
                    "coverage_dedup_mode": "soft",
                    "prior_coverage_fraction": 0.2,
                },
                "top_evidence_paths": [
                    {"source": "PS2_mean", "target": "FS2_max", "path": "PS2_mean -> FS2_max"},
                ],
            },
            {
                "dataset": "hydraulic",
                "target": "valve",
                "variant": "full",
                "seed": 2,
                "primary_test_metrics": {"macro_f1": 0.7, "balanced_accuracy": 0.71},
                "efficiency": {
                    "test_inference_samples_per_second": 120.0,
                    "parameters": 10,
                    "path_aux_weight": 0.05,
                    "coarse_aux_weight": 0.1,
                    "health_aux_weight": 0.2,
                    "test_health_mae": 0.3,
                },
                "diagnostics": {
                    "config": {"use_context_router": True},
                    "test_diagnostics": {"mean_path_context_importance": 0.4, "mean_class_evidence_admission": 0.6},
                },
                "path_budget": {
                    "path_coverage_mode": "target_group",
                    "coverage_dedup_mode": "soft",
                    "prior_coverage_fraction": 0.2,
                },
                "top_evidence_paths": [
                    {"source": "PS2_std", "target": "FS2_mean", "path": "PS2_std -> FS2_mean"},
                ],
            },
        ]

        summary = aggregate(rows)
        self.assertEqual(float(summary[0]["top10_path_jaccard"]), 0.0)
        self.assertEqual(float(summary[0]["top10_group_path_jaccard"]), 1.0)
        self.assertAlmostEqual(float(summary[0]["mean_path_context_importance"]), 0.3)
        self.assertAlmostEqual(float(summary[0]["mean_class_evidence_admission"]), 0.7)
        self.assertAlmostEqual(float(summary[0]["path_aux_weight"]), 0.05)
        self.assertAlmostEqual(float(summary[0]["coarse_aux_weight"]), 0.1)
        self.assertAlmostEqual(float(summary[0]["health_aux_weight"]), 0.2)
        self.assertAlmostEqual(float(summary[0]["prior_coverage_fraction"]), 0.2)
        self.assertAlmostEqual(float(summary[0]["test_health_mae"]), 0.2)
        self.assertEqual(summary[0]["setting"], "prior-cover@0.20+path-aux@0.05+coarse@0.10+health@0.20")
        self.assertTrue(summary[0]["use_context_router"])
        report = render_markdown(summary, rows)
        self.assertIn("Setting", report)
        self.assertIn("Group Path Jaccard", report)
        self.assertIn("Context imp.", report)
        self.assertIn("Class adm.", report)
        self.assertIn("Path aux", report)
        self.assertIn("Coarse aux", report)
        self.assertIn("Health aux", report)
        self.assertIn("PS2 -> FS2", report)

    def test_aggregate_keeps_cmapss_rul_metrics(self) -> None:
        rows = [
            {
                "dataset": "cmapss",
                "target": "rul",
                "variant": "full",
                "seed": 1,
                "primary_metric_family": "rul_regression",
                "primary_test_metrics": {
                    "rul_mae": 10.0,
                    "rul_rmse": 12.0,
                    "rul_score": 100.0,
                    "aux_macro_f1": 0.6,
                    "aux_balanced_accuracy": 0.61,
                },
                "test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
                "efficiency": {
                    "test_inference_samples_per_second": 100.0,
                    "parameters": 10,
                    "health_aux_weight": 1.0,
                    "test_health_mae": 0.08,
                    "test_rul_mae": 10.0,
                    "test_rul_rmse": 12.0,
                    "test_rul_score": 100.0,
                },
                "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
                "path_budget": {"cmapss_rul_primary": True, "health_aux_auto_enabled": True},
                "top_evidence_paths": [],
            },
            {
                "dataset": "cmapss",
                "target": "rul",
                "variant": "full",
                "seed": 2,
                "primary_metric_family": "rul_regression",
                "primary_test_metrics": {
                    "rul_mae": 14.0,
                    "rul_rmse": 16.0,
                    "rul_score": 140.0,
                    "aux_macro_f1": 0.7,
                    "aux_balanced_accuracy": 0.71,
                },
                "test_metrics": {"macro_f1": 0.7, "balanced_accuracy": 0.71},
                "efficiency": {
                    "test_inference_samples_per_second": 110.0,
                    "parameters": 10,
                    "health_aux_weight": 1.0,
                    "test_health_mae": 0.10,
                    "test_rul_mae": 14.0,
                    "test_rul_rmse": 16.0,
                    "test_rul_score": 140.0,
                },
                "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
                "path_budget": {"cmapss_rul_primary": True, "health_aux_auto_enabled": True},
                "top_evidence_paths": [],
            },
        ]

        summary = aggregate(rows)
        self.assertAlmostEqual(float(summary[0]["rul_mae_mean"]), 12.0)
        self.assertAlmostEqual(float(summary[0]["rul_rmse_mean"]), 14.0)
        self.assertAlmostEqual(float(summary[0]["rul_score_mean"]), 120.0)
        report = render_markdown(summary, rows)
        self.assertIn("RUL RMSE", report)
        self.assertIn("RUL Score", report)

    def test_setting_label_includes_temporal_mixer(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_temporal_mixer": True,
                "temporal_mixer_depth": 4,
                "focal_loss_gamma": 1.5,
                "label_smoothing": 0.05,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "temporal-mixer-d4+focal1.50+smooth0.05")

    def test_setting_label_includes_nondefault_temporal_encoder(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {"temporal_encoder_mode": "multi_scale_bidirectional"},
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "temporal-multi-scale-bidirectional")

    def test_setting_label_includes_llm_expert_condition_verifier(self) -> None:
        row = {
            "dataset": "skab",
            "target": "anomaly",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_llm_expert_condition_verifier": True,
                "llm_condition_verifier_weight": 0.5,
                "llm_condition_verifier_min_data_support": 0.05,
                "llm_condition_verifier_floor": 0.1,
                "llm_condition_verifier_target": "candidate_gate",
                "effective_use_class_conditioned_evidence": True,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "llm-expert-condition-verifier-candidate_gate-w0.50-ms0.05-f0.10",
        )

    def test_setting_label_includes_prototype_posterior_fusion(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_prototype_posterior_fusion": True,
                "prototype_fusion_max_blend": 0.35,
                "prototype_fusion_min_val_gain": 0.005,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "proto-post-b0.35-mingain0.005")

    def test_setting_label_includes_ordinal_boundary_loss(self) -> None:
        row = {
            "dataset": "cmapss",
            "target": "degradation_stage_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "ordinal_boundary_loss_weight": 0.005,
                "ordinal_boundary_focal_gamma": 1.0,
                "ordinal_boundary_focus": 0.5,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "ord-boundary-w0.005-g1.00-f0.50")

    def test_setting_label_prevents_mixed_protocol_aggregation(self) -> None:
        base_row = {
            "dataset": "cmapss",
            "target": "stage",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.7, "balanced_accuracy": 0.7},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "path_coverage_mode": "group_pair_inclusive",
                "coverage_dedup_mode": "hard",
            },
            "top_evidence_paths": [],
        }
        regime_row = {
            **base_row,
            "seed": 2,
            "primary_test_metrics": {"macro_f1": 0.81, "balanced_accuracy": 0.80},
            "path_budget": {
                "path_coverage_mode": "group_pair_inclusive",
                "coverage_dedup_mode": "hard",
                "use_regime_prototype_residuals": True,
                "regime_prototype_k": 6,
                "protect_order_anchor_path_nodes": True,
            },
        }

        summary = aggregate([base_row, regime_row])
        settings = {item["setting"] for item in summary}

        self.assertEqual(len(summary), 2)
        self.assertIn("group_pair_inclusive+dedup-hard", settings)
        self.assertIn("group_pair_inclusive+dedup-hard+regime6+no-order-path", settings)

    def test_setting_label_includes_class_evidence_mode(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "path_coverage_mode": "group_pair_inclusive",
                "coverage_dedup_mode": "hard",
                "use_class_conditioned_evidence": True,
                "class_evidence_top_k": 8,
                "class_evidence_mode": "static_lag",
                "class_evidence_max_lag": 3,
                "class_evidence_lag_weight": 0.5,
                "class_evidence_family_k": 2,
                "class_evidence_family_weight": 0.4,
                "class_evidence_gate_threshold": 0.7,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "group_pair_inclusive+dedup-hard+class-evidence-static_lag-lag3@0.50-family2@0.40-gate@0.70@8",
        )

    def test_setting_label_includes_algorithmic_edge_prior(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "hybrid",
                "algorithmic_edge_prior_top_k": 8,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "prior_algorithmic_combine_mode": "corroborated_max",
                "prior_external_isolated_scale": 0.25,
                "prior_overlap_boost": 0.2,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "alg-prior-hybrid-k8-lag3@0.05+corrob-e0.25-b0.20")

    def test_setting_label_includes_anchor_subgraph_prior(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "hybrid",
                "algorithmic_edge_prior_top_k": 16,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "prior_algorithmic_combine_mode": "anchored_subgraph",
                "prior_external_isolated_scale": 0.25,
                "prior_overlap_boost": 0.2,
                "prior_nonanchor_algorithmic_scale": 0.35,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "alg-prior-hybrid-k16-lag3@0.05+anchor-e0.25-b0.20-n0.35")

    def test_setting_label_includes_external_candidate_only_edges(self) -> None:
        row = {
            "dataset": "skab",
            "target": "anomaly",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_pool",
                "algorithmic_edge_prior_top_k": 12,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "external_edge_candidate_only": True,
                "external_candidate_families": ["llm"],
                "external_family_calibration_floor": 0.10,
                "external_family_min_data_support": 0.20,
                "external_candidate_expert_scale": 1.0,
                "external_candidate_llm_scale": 0.4,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertIn("ext-cand-e1.00-l0.40-f0.10-famllm-ms0.20", summary[0]["setting"])

    def test_setting_label_includes_multiview_group_cap(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "multiview",
                "algorithmic_edge_prior_top_k": 16,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "alg-prior-multiview-k16-g4-lag3@0.05")

    def test_setting_label_includes_edge_bank_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_bank",
                "algorithmic_edge_prior_top_k": 12,
                "algorithmic_edge_prior_group_top_k": 3,
                "algorithmic_edge_prior_max_lag": 2,
                "algorithmic_edge_prior_strength": 0.04,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.45,
                "algorithmic_edge_prior_bank_vote_boost": 0.10,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 4.0,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "alg-prior-edge_bank-k12-g3-lag2-vote2-sv0.45-vb0.10-gb4.0@0.04")

    def test_setting_label_includes_edge_pool_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_pool",
                "algorithmic_edge_prior_top_k": 20,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.35,
                "algorithmic_edge_prior_bank_vote_boost": 0.12,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 6.0,
                "algorithmic_edge_prior_pool_multiplier": 2.5,
                "algorithmic_edge_prior_pool_min_score": 0.10,
                "algorithmic_edge_prior_pool_rank_weight": 0.40,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "alg-prior-edge_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40-min0.10@0.05",
        )

    def test_setting_label_includes_edge_cert_pool_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_cert_pool",
                "algorithmic_edge_prior_top_k": 20,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.35,
                "algorithmic_edge_prior_bank_vote_boost": 0.12,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 6.0,
                "algorithmic_edge_prior_pool_multiplier": 2.5,
                "algorithmic_edge_prior_pool_min_score": 0.10,
                "algorithmic_edge_prior_pool_rank_weight": 0.40,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "alg-prior-edge_cert_pool-k20-g4-lag3-vote2-sv0.35-vb0.12-gb6.0-pool2.5-rank0.40-min0.10@0.05",
        )

    def test_setting_label_includes_edge_canvas_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_canvas",
                "algorithmic_edge_prior_top_k": 18,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.40,
                "algorithmic_edge_prior_bank_vote_boost": 0.12,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 6.0,
                "algorithmic_edge_prior_pool_multiplier": 2.5,
                "algorithmic_edge_prior_pool_rank_weight": 0.35,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "alg-prior-edge_canvas-k18-g4-lag3-vote2-sv0.40-vb0.12-gb6.0-pool2.5-rank0.35@0.05",
        )

    def test_setting_label_includes_edge_universe_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_universe",
                "algorithmic_edge_prior_top_k": 12,
                "algorithmic_edge_prior_group_top_k": 3,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.50,
                "algorithmic_edge_prior_bank_vote_boost": 0.10,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 5.0,
                "algorithmic_edge_prior_pool_multiplier": 3.0,
                "algorithmic_edge_prior_pool_rank_weight": 0.30,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "alg-prior-edge_universe-k12-g3-lag3-vote2-sv0.50-vb0.10-gb5.0-pool3.0-rank0.30@0.05",
        )

    def test_setting_label_includes_edge_sieve_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_sieve",
                "algorithmic_edge_prior_top_k": 16,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.30,
                "algorithmic_edge_prior_bank_vote_boost": 0.12,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 5.0,
                "algorithmic_edge_prior_pool_multiplier": 3.0,
                "algorithmic_edge_prior_pool_rank_weight": 0.25,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "alg-prior-edge_sieve-k16-g4-lag3-vote2-sv0.30-vb0.12-gb5.0-pool3.0-rank0.25@0.05",
        )

    def test_setting_label_includes_edge_overlay_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_overlay",
                "algorithmic_edge_prior_top_k": 20,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.03,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.25,
                "algorithmic_edge_prior_bank_vote_boost": 0.12,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 5.0,
                "algorithmic_edge_prior_pool_multiplier": 3.0,
                "algorithmic_edge_prior_pool_rank_weight": 0.25,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "alg-prior-edge_overlay-k20-g4-lag3-vote2-sv0.25-vb0.12-gb5.0-pool3.0-rank0.25@0.03",
        )

    def test_setting_label_includes_edge_lattice_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_lattice",
                "algorithmic_edge_prior_top_k": 16,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.04,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.50,
                "algorithmic_edge_prior_bank_vote_boost": 0.12,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 6.0,
                "algorithmic_edge_prior_pool_multiplier": 3.0,
                "algorithmic_edge_prior_pool_rank_weight": 0.30,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "alg-prior-edge_lattice-k16-g4-lag3-vote2-sv0.50-vb0.12-gb6.0-pool3.0-rank0.30@0.04",
        )

    def test_setting_label_includes_edge_dual_lattice_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_dual_lattice",
                "algorithmic_edge_prior_top_k": 18,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.45,
                "algorithmic_edge_prior_bank_vote_boost": 0.12,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 6.0,
                "algorithmic_edge_prior_pool_multiplier": 2.8,
                "algorithmic_edge_prior_pool_rank_weight": 0.35,
                "candidate_coverage_fraction": 0.08,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "candidate-cover@0.08+alg-prior-edge_dual_lattice-k18-g4-lag3-vote2-sv0.45-vb0.12-gb6.0-pool2.8-rank0.35@0.05",
        )

    def test_setting_label_includes_edge_guarded_lattice_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "algorithmic_edge_prior_mode": "edge_guarded_lattice",
                "algorithmic_edge_prior_top_k": 18,
                "algorithmic_edge_prior_group_top_k": 4,
                "algorithmic_edge_prior_max_lag": 3,
                "algorithmic_edge_prior_strength": 0.05,
                "algorithmic_edge_prior_bank_min_votes": 2,
                "algorithmic_edge_prior_bank_single_view_scale": 0.45,
                "algorithmic_edge_prior_bank_vote_boost": 0.12,
                "algorithmic_edge_prior_bank_global_budget_multiplier": 6.0,
                "algorithmic_edge_prior_pool_multiplier": 2.8,
                "algorithmic_edge_prior_pool_rank_weight": 0.35,
                "candidate_coverage_fraction": 0.08,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "candidate-cover@0.08+alg-prior-edge_guarded_lattice-k18-g4-lag3-vote2-sv0.45-vb0.12-gb6.0-pool2.8-rank0.35@0.05",
        )

    def test_setting_label_includes_certified_graph_core_controls(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_certified_graph_prior_core": True,
                "use_separate_path_candidate_prior": True,
                "graph_prior_core_top_k": 8,
                "graph_prior_core_group_top_k": 3,
                "graph_prior_core_floor": 0.05,
                "graph_prior_core_threshold": 0.35,
                "graph_prior_core_temperature": 0.05,
                "graph_prior_core_direct_weight": 1.0,
                "graph_prior_core_group_weight": 0.4,
                "graph_prior_core_stability_weight": 0.5,
                "graph_prior_core_prior_weight": 0.2,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "graph-core-cert-k8-g3-f0.05-thr0.35-t0.05-d1.00-grp0.40-stab0.50-p0.20-sep-path-candidate",
        )

    def test_setting_label_includes_path_proposal_consistency(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_proposal_consistency": True,
                "path_proposal_consistency_strength": 0.75,
                "path_proposal_consistency_threshold": 0.40,
                "path_proposal_consistency_temperature": 0.03,
                "path_proposal_consistency_floor": 0.10,
                "path_proposal_consistency_support_mode": "salience",
                "path_proposal_consistency_protected_strength": 0.50,
                "path_proposal_retention_fraction": 0.25,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "path-proposal-cons-s0.75-thr0.40-t0.03-f0.10-salience-pstr0.50-retain0.25",
        )

    def test_setting_label_includes_evidence_admit_path_proposal_consistency(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_proposal_consistency": True,
                "path_proposal_consistency_strength": 0.30,
                "path_proposal_consistency_threshold": 0.45,
                "path_proposal_consistency_temperature": 0.04,
                "path_proposal_consistency_floor": 0.15,
                "path_proposal_consistency_support_mode": "evidence_admit",
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "path-proposal-cons-s0.30-thr0.45-t0.04-f0.15-evidence_admit",
        )

    def test_setting_label_includes_edge_calibrator(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_edge_calibrator": True,
                "edge_calibrator_floor": 0.10,
                "edge_calibrator_init_bias": 1.5,
                "edge_calibrator_reg_weight": 0.25,
                "algorithmic_edge_prior_mode": "hybrid",
                "algorithmic_edge_prior_top_k": 8,
                "algorithmic_edge_prior_strength": 0.05,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "edge-cal-f0.10-b1.5-reg0.25+alg-prior-hybrid-k8@0.05")

    def test_setting_label_includes_path_prior_consistency(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_prior_consistency": True,
                "path_prior_consistency_strength": 0.35,
                "path_prior_consistency_threshold": 0.20,
                "path_prior_consistency_temperature": 0.04,
                "path_prior_consistency_support_mode": "agreement",
                "algorithmic_edge_prior_mode": "edge_pool",
                "algorithmic_edge_prior_top_k": 8,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "path-prior-cons-s0.35-thr0.20-t0.04-agreement+alg-prior-edge_pool-k8-vote2-sv0.55-vb0.15-pool2.0-rank0.35",
        )

    def test_setting_label_includes_class_blend_floor(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_prior_consistency": True,
                "path_prior_consistency_strength": 0.25,
                "path_prior_consistency_threshold": 0.35,
                "path_prior_consistency_temperature": 0.05,
                "path_prior_consistency_support_mode": "class_blend",
                "path_prior_consistency_class_floor": 0.25,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "path-prior-cons-s0.25-thr0.35-t0.05-class_blend-cf0.25",
        )

    def test_setting_label_includes_path_evidence_consistency(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_evidence_consistency": True,
                "path_evidence_consistency_strength": 0.15,
                "path_evidence_consistency_threshold": 0.35,
                "path_evidence_consistency_temperature": 0.05,
                "path_evidence_consistency_floor": 0.10,
                "path_evidence_consistency_support_mode": "relative",
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "path-evid-cons-s0.15-thr0.35-t0.05-relative-f0.10",
        )

    def test_setting_label_includes_exact_path_dedup(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "deduplicate_exact_paths": True,
                "algorithmic_edge_prior_mode": "edge_canvas",
                "algorithmic_edge_prior_top_k": 8,
                "algorithmic_edge_prior_strength": 0.05,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "dedup-exact+alg-prior-edge_canvas-k8-vote2-sv0.55-vb0.15-pool2.0-rank0.35@0.05")

    def test_setting_label_includes_edge_family_router(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_edge_family_router": True,
                "edge_family_router_temperature": 0.75,
                "edge_family_router_floor": 0.10,
                "edge_family_router_blend": 0.80,
                "edge_family_router_balance_weight": 0.015,
                "algorithmic_edge_prior_mode": "edge_canvas",
                "algorithmic_edge_prior_top_k": 8,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "edge-family-router-t0.75-f0.10-b0.80-bal0.015+alg-prior-edge_canvas-k8-vote2-sv0.55-vb0.15-pool2.0-rank0.35",
        )

    def test_setting_label_includes_stable_path_evidence(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_stable_path_evidence": True,
                "stable_path_evidence_mode": "static_lag",
                "stable_path_evidence_splits": 4,
                "stable_path_evidence_min_vote_fraction": 0.75,
                "stable_path_evidence_strength": 0.50,
                "stable_path_evidence_top_k": 8,
                "stable_path_evidence_edge_top_k": 4,
                "stable_path_evidence_max_lag": 3,
                "stable_path_evidence_lag_weight": 0.50,
                "stable_path_evidence_class_mode": "filter",
                "stable_path_evidence_class_floor": 0.25,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "stable-path-static_lag-s4-v0.75-w0.50-lag3@0.50-k8-edge4-class-filter0.25")

    def test_setting_label_includes_class_evidence_quality_certificate(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {}, "test_diagnostics": {}},
            "path_budget": {
                "use_stable_path_evidence": True,
                "stable_path_evidence_mode": "static_lag",
                "stable_path_evidence_splits": 4,
                "stable_path_evidence_min_vote_fraction": 0.75,
                "stable_path_evidence_strength": 0.25,
                "stable_path_evidence_max_lag": 3,
                "stable_path_evidence_lag_weight": 0.50,
                "stable_path_evidence_path_mode": "off",
                "stable_path_evidence_class_mode": "off",
                "use_class_evidence_quality_certificate": True,
                "class_evidence_quality_mode": "focus_stability",
                "class_evidence_quality_floor": 0.05,
                "class_evidence_quality_threshold": 0.75,
                "class_evidence_quality_temperature": 0.05,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "stable-path-static_lag-s4-v0.75-w0.25-lag3@0.50-path-off+class-evid-cert-focus_stability-f0.05-thr0.75-t0.05",
        )

    def test_setting_label_includes_path_family_quality_certificate(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_family_quality_certificate": True,
                "path_family_quality_mode": "focus_path_family",
                "path_family_quality_floor": 0.10,
                "path_family_quality_threshold": 0.30,
                "path_family_quality_temperature": 0.05,
                "path_family_quality_direct_weight": 0.90,
                "path_family_quality_group_weight": 0.40,
                "path_family_quality_stability_weight": 0.20,
                "use_path_family_protected_proposal_weights": True,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "path-family-cert-focus_path_family-f0.10-thr0.30-t0.05-d0.90-g0.40-stab0.20-pf-protect",
        )

    def test_setting_label_includes_fault_family_quality_certificate(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_family_quality_certificate": True,
                "path_family_quality_mode": "focus_fault_family",
                "path_family_quality_floor": 0.05,
                "path_family_quality_threshold": 0.40,
                "path_family_quality_temperature": 0.04,
                "path_family_quality_direct_weight": 0.80,
                "path_family_quality_group_weight": 0.30,
                "path_family_quality_stability_weight": 0.25,
                "path_family_quality_family_k": 2,
                "path_family_quality_family_weight": 0.60,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "path-family-cert-focus_fault_family-f0.05-thr0.40-t0.04-d0.80-g0.30-stab0.25-fam2@0.60",
        )

    def test_setting_label_includes_stable_class_edge_overlay(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_stable_class_edge_overlay": True,
                "stable_class_edge_overlay_scale": 0.30,
                "stable_class_edge_overlay_top_k": 6,
                "stable_class_edge_overlay_group_top_k": 2,
                "stable_class_edge_overlay_focus_weight": 1.40,
                "stable_class_edge_overlay_nonfocus_weight": 0.20,
                "stable_class_edge_overlay_mode": "add",
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "stable-class-edge-overlay-add-s0.30-k6-g2-fw1.40-nw0.20",
        )

    def test_setting_label_includes_path_reliability_calibrator(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_reliability_calibrator": True,
                "path_reliability_context_reg_weight": 0.005,
                "algorithmic_edge_prior_mode": "hybrid",
                "algorithmic_edge_prior_top_k": 8,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "path-rel-cal-reg0.005+alg-prior-hybrid-k8")

    def test_setting_label_includes_path_reliability_scale(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_path_reliability_calibrator": True,
                "path_reliability_context_scale": 0.50,
                "path_reliability_context_reg_weight": 0.005,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "path-rel-cal-s0.50-reg0.005")

    def test_setting_label_includes_learned_path_admission(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_learned_path_admission": True,
                "path_admission_strength": 0.75,
                "path_admission_reg_weight": 0.002,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "learned-path-admit-s0.75-reg0.002")

    def test_setting_label_includes_class_conditioned_prior_admission(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_class_conditioned_prior_admission": True,
                "class_prior_admission_floor": 0.25,
                "algorithmic_edge_prior_mode": "edge_pool",
                "algorithmic_edge_prior_top_k": 12,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "class-prior-admit-f0.25+alg-prior-edge_pool-k12-vote2-sv0.55-vb0.15-pool2.0-rank0.35")

    def test_setting_label_includes_adaptive_prior_admission(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_class_conditioned_prior_admission": True,
                "class_prior_admission_floor": 0.50,
                "use_adaptive_prior_admission": True,
                "adaptive_prior_admission_threshold": 0.30,
                "adaptive_prior_admission_temperature": 0.07,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "class-prior-admit-f0.50-adaptive@0.30t0.07")

    def test_setting_label_includes_candidate_prior_admission(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_candidate_prior_admission": True,
                "candidate_prior_admission_floor": 0.05,
                "candidate_prior_admission_threshold": 0.50,
                "candidate_prior_admission_temperature": 0.07,
                "candidate_prior_admission_support_mode": "absolute",
                "candidate_prior_admission_scale": 0.35,
                "candidate_prior_admission_min_support": 0.60,
                "candidate_prior_admission_target": "feature",
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(
            summary[0]["setting"],
            "candidate-prior-admit-f0.05-thr0.50-t0.07-absolute-s0.35-feature-minsup0.60",
        )

    def test_setting_label_includes_salience_coverage_fraction(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_task_salience": True,
                "salience_mode": "class",
                "salience_selection_strength": 0.0,
                "salience_coverage_fraction": 0.25,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "salience-class@0.00-cover0.25")

    def test_setting_label_includes_class_router_sharpening(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_class_conditioned_evidence": True,
                "class_evidence_top_k": 8,
                "class_evidence_router_top_k": 1,
                "class_evidence_router_temperature": 0.5,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "class-evidence-router1-temp0.50@8")

    def test_setting_label_includes_class_evidence_focus(self) -> None:
        row = {
            "dataset": "tep",
            "target": "event_quality_class_id",
            "variant": "full",
            "seed": 1,
            "primary_test_metrics": {"macro_f1": 0.6, "balanced_accuracy": 0.61},
            "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
            "diagnostics": {"config": {"use_context_router": True}, "test_diagnostics": {}},
            "path_budget": {
                "use_class_conditioned_evidence": True,
                "class_evidence_top_k": 8,
                "class_evidence_focus_mode": "explicit",
                "class_evidence_focus_classes": [0, 3, 9],
                "class_evidence_focus_nonfocus_weight": 0.1,
            },
            "top_evidence_paths": [],
        }

        summary = aggregate([row])

        self.assertEqual(summary[0]["setting"], "class-evidence-focus-explicit3@0.10@8")


if __name__ == "__main__":
    unittest.main()
