from __future__ import annotations

import os
import json
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd
import torch

from ms_gse_rpf_model import MSGSERPFConfig, MSGSERPFNet, MultiScaleEventTokenizer, ReliablePathFusion
from run_public_ms_gse_rpf_experiment import (
    ReadyTask,
    _aggregate_external_candidate_prior,
    _calibrate_external_edge_family_priors,
    apply_llm_expert_condition_verifier_to_candidate_prior,
    apply_class_evidence_quality_certificate,
    apply_graph_prior_core_certificate,
    apply_one_class_posterior_fusion,
    apply_ordinal_threshold_posterior_calibration,
    apply_path_family_quality_certificate,
    apply_prototype_posterior_fusion,
    apply_stable_class_edge_overlay,
    apply_regime_prototype_residuals,
    build_capped_rul_targets,
    build_health_index_targets,
    build_split,
    build_causal_windows,
    build_rul_prediction_records,
    calibrate_prior_adjacency_from_windows,
    build_rul_targets,
    combine_algorithmic_and_external_priors,
    compute_train_algorithmic_edge_prior,
    compute_train_class_path_evidence,
    compute_train_group_salience,
    compute_train_stable_path_evidence,
    feature_group_name,
    infer_feature_group_ids,
    load_ready_task,
    load_knowledge_graph_prior,
    ordinal_boundary_bce_loss,
    ordinal_emd_loss,
    predict_rul_from_normalized,
    resolve_path_budget,
    rul_regression_metrics,
    run_ready_task,
    select_cmapss_terminal_rul_indices,
    summarize_rul_by_subset,
    supervised_classification_loss,
    validation_gain_admission_decision,
)


class MSGSERPFModelTest(unittest.TestCase):
    def test_temporal_encoder_modes_preserve_token_contract(self) -> None:
        x = torch.randn(2, 9, 4)
        expected_scale_counts = {
            "single_scale_causal": 1,
            "multi_scale_causal": 3,
            "single_scale_bidirectional": 1,
            "multi_scale_bidirectional": 3,
        }
        for mode, scale_count in expected_scale_counts.items():
            with self.subTest(mode=mode):
                tokenizer = MultiScaleEventTokenizer(
                    n_features=4,
                    hidden_dim=6,
                    scales=(3, 5, 9),
                    dropout=0.0,
                    temporal_encoder_mode=mode,
                )
                tokens, weights = tokenizer(x)
                self.assertEqual(tuple(tokens.shape), (2, 4, 6))
                self.assertEqual(tuple(weights.shape), (2, scale_count, 4))
                np.testing.assert_allclose(
                    weights.sum(dim=1).detach().numpy(),
                    np.ones((2, 4), dtype=np.float32),
                    atol=1.0e-5,
                )

    def test_forward_returns_logits_reconstruction_and_path_diagnostics(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=5,
                n_classes=3,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=6,
            )
        )

        out = model(torch.randn(4, 7, 5), return_diagnostics=True)

        self.assertEqual(tuple(out["logits"].shape), (4, 3))
        self.assertEqual(tuple(out["path_aux_logits"].shape), (4, 3))
        self.assertEqual(tuple(out["coarse_logits"].shape), (4, 2))
        self.assertEqual(tuple(out["health_pred"].shape), (4,))
        self.assertEqual(tuple(out["rul_norm_pred"].shape), (4,))
        self.assertEqual(tuple(out["reconstruction"].shape), (4, 5))
        self.assertEqual(tuple(out["diagnostics"]["path_weights"].shape), (4, 6))
        self.assertEqual(tuple(out["diagnostics"]["path_context_importance"].shape), (4, 6))
        self.assertEqual(tuple(out["diagnostics"]["path_reliability_gain"].shape), (4,))
        self.assertGreater(float(out["diagnostics"]["path_reliability_gain"].mean()), 0.0)
        self.assertEqual(getattr(model, "model_family"), "ms_gse_rpf")

    def test_forward_with_temporal_mixer_preserves_output_contract(self) -> None:
        for mixer_type in ("conv", "gru", "bigru"):
            with self.subTest(mixer_type=mixer_type):
                model = MSGSERPFNet(
                    MSGSERPFConfig(
                        n_features=5,
                        n_classes=3,
                        hidden_dim=8,
                        graph_top_k=2,
                        max_paths=6,
                        use_temporal_mixer=True,
                        temporal_mixer_type=mixer_type,
                        temporal_mixer_depth=2,
                    )
                )

                out = model(torch.randn(4, 7, 5), return_diagnostics=True)

                self.assertEqual(tuple(out["logits"].shape), (4, 3))
                self.assertEqual(tuple(out["path_aux_logits"].shape), (4, 3))
                self.assertEqual(tuple(out["temporal_rul_norm_pred"].shape), (4,))
                self.assertNotIn("anchor_rul_norm_pred", out)
                self.assertEqual(tuple(out["diagnostics"]["path_weights"].shape), (4, 6))

    def test_rul_temporal_anchor_fusion_adds_conservative_path_residual_head(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=5,
                n_classes=3,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=6,
                use_temporal_mixer=True,
                temporal_mixer_type="gru",
                temporal_mixer_depth=2,
                use_rul_temporal_anchor_fusion=True,
                rul_anchor_gate_bias=-2.0,
            )
        )

        out = model(torch.randn(4, 7, 5), return_diagnostics=True)

        self.assertEqual(tuple(out["temporal_rul_norm_pred"].shape), (4,))
        self.assertEqual(tuple(out["anchor_rul_norm_pred"].shape), (4,))
        self.assertEqual(tuple(out["diagnostics"]["rul_anchor_gate"].shape), (4,))
        self.assertEqual(tuple(out["diagnostics"]["rul_anchor_delta"].shape), (4,))
        self.assertLess(float(out["diagnostics"]["rul_anchor_gate"].mean()), 0.50)

    def test_unknown_temporal_mixer_type_fails_fast(self) -> None:
        with self.assertRaises(ValueError):
            MSGSERPFNet(
                MSGSERPFConfig(
                    n_features=5,
                    n_classes=3,
                    hidden_dim=8,
                    graph_top_k=2,
                    max_paths=6,
                    use_temporal_mixer=True,
                    temporal_mixer_type="missing",
                )
            )

    def test_reliable_path_fusion_uses_separate_candidate_proposal_quota(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=6,
            use_reliability=False,
            use_path_fusion=True,
            prior_coverage_fraction=0.0,
            candidate_coverage_fraction=0.25,
        )
        node_states = torch.randn(2, 4, 4)
        adjacency = torch.tensor(
            [
                [0.0, 0.9, 0.8, 0.1],
                [0.7, 0.0, 0.6, 0.1],
                [0.5, 0.4, 0.0, 0.2],
                [0.4, 0.3, 0.2, 0.0],
            ],
            dtype=torch.float32,
        ).unsqueeze(0).expand(2, -1, -1)
        candidate = torch.zeros(4, 4)
        candidate[2, 3] = 1.0
        candidate[3, 2] = 1.0

        _context, diag = fusion(
            node_states,
            adjacency,
            candidate_proposal_adjacency=candidate,
        )

        selected_pairs = set(zip(diag["path_target"][0].tolist(), diag["path_source"][0].tolist()))
        self.assertIn((2, 3), selected_pairs)
        self.assertEqual(int(diag["path_candidate_quota"][0].item()), 2)

    def test_feature_group_ids_drive_group_aware_path_coverage(self) -> None:
        groups = infer_feature_group_ids(
            ["FS1_mean", "FS1_std", "PS1_mean", "PS1_std", "Voltage", "sensor_02", "xmeas_01", "op_setting_1"]
        )
        self.assertEqual(groups.tolist(), [0, 0, 1, 1, 2, 3, 4, 5])
        self.assertEqual(feature_group_name("FS1_last_minus_first"), "FS1")
        self.assertEqual(feature_group_name("sensor_02"), "sensor_02")
        self.assertEqual(feature_group_name("xmeas_01"), "xmeas_01")
        self.assertEqual(feature_group_name("op_setting_1"), "op_setting_1")
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=8,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=6,
            )
        )
        model.set_feature_groups(groups)

        out = model(torch.randn(3, 6, 8), return_diagnostics=True)

        self.assertEqual(tuple(out["diagnostics"]["path_weights"].shape), (3, 6))
        self.assertEqual(tuple(model.feature_group_ids.shape), (8,))

    def test_task_salience_is_optional_path_evidence(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=5,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=6,
                use_task_salience=True,
                salience_selection_strength=0.05,
            )
        )
        model.set_task_salience([1.0, 0.8, 0.2, 0.0, 0.5])

        out = model(torch.randn(3, 6, 5), return_diagnostics=True)

        self.assertEqual(tuple(out["diagnostics"]["path_salience_weight"].shape), (3, 6))
        self.assertGreaterEqual(float(out["diagnostics"]["path_salience_weight"].mean()), 0.0)

    def test_path_candidate_prior_is_separate_from_graph_prior(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=1,
                max_paths=4,
                prior_strength=1.0,
                prior_coverage_fraction=1.0,
            )
        )
        graph_prior = np.zeros((4, 4), dtype=np.float32)
        graph_prior[1, 0] = 1.0
        candidate_prior = np.zeros((4, 4), dtype=np.float32)
        candidate_prior[2, 3] = 0.8
        model.set_graph_prior(graph_prior)
        model.set_path_candidate_prior(candidate_prior)

        out = model(torch.randn(2, 6, 4), return_diagnostics=True)
        diag = out["diagnostics"]

        self.assertAlmostEqual(float(model.prior_adjacency[1, 0]), 1.0, places=6)
        self.assertAlmostEqual(float(model.path_candidate_prior[2, 3]), 0.8, places=6)
        self.assertIn("path_candidate_prior_adjacency", diag)
        self.assertIn("rpf_prior_adjacency", diag)
        self.assertAlmostEqual(float(diag["path_candidate_prior_adjacency"][2, 3]), 0.8, places=6)
        self.assertAlmostEqual(float(diag["rpf_prior_adjacency"][2, 3]), 0.8, places=6)
        self.assertAlmostEqual(float(diag["rpf_prior_adjacency"][1, 0]), 0.0, places=6)

    def test_candidate_prior_admission_preserves_graph_prior_and_gates_overlay(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=1,
                max_paths=4,
                prior_strength=1.0,
                prior_coverage_fraction=1.0,
                use_candidate_prior_admission=True,
                candidate_prior_admission_floor=0.0,
                candidate_prior_admission_threshold=0.50,
                candidate_prior_admission_temperature=0.01,
                candidate_prior_admission_support_mode="relative_evidence",
                candidate_prior_admission_scale=1.0,
            )
        )
        graph_prior = np.zeros((4, 4), dtype=np.float32)
        graph_prior[1, 0] = 1.0
        candidate_prior = np.zeros((4, 4), dtype=np.float32)
        candidate_prior[2, 3] = 0.8
        candidate_prior[3, 2] = 0.8
        path_evidence = np.zeros((4, 4), dtype=np.float32)
        path_evidence[2, 3] = 1.0
        model.set_graph_prior(graph_prior)
        model.set_path_candidate_prior(candidate_prior)
        model.set_path_evidence(path_evidence)

        out = model(torch.randn(2, 6, 4), return_diagnostics=True)
        diag = out["diagnostics"]

        rpf_prior = diag["rpf_prior_adjacency"]
        self.assertEqual(tuple(rpf_prior.shape), (2, 4, 4))
        self.assertIn("candidate_prior_admission_gate", diag)
        self.assertIn("candidate_prior_overlay_adjacency", diag)
        self.assertAlmostEqual(float(rpf_prior[:, 1, 0].min()), 1.0, places=6)
        self.assertGreater(float(rpf_prior[:, 2, 3].mean()), 0.79)
        self.assertLess(float(rpf_prior[:, 3, 2].max()), 1.0e-3)
        self.assertGreater(float(diag["candidate_prior_admission_support"][:, 2, 3].mean()), 0.99)
        self.assertLess(float(diag["candidate_prior_admission_support"][:, 3, 2].max()), 1.0e-6)

    def test_candidate_prior_admission_can_use_feature_prior_without_path_coverage(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=1,
                max_paths=4,
                prior_strength=1.0,
                prior_coverage_fraction=1.0,
                use_candidate_prior_admission=True,
                candidate_prior_admission_floor=0.0,
                candidate_prior_admission_threshold=0.50,
                candidate_prior_admission_temperature=0.01,
                candidate_prior_admission_support_mode="absolute",
                candidate_prior_admission_scale=1.0,
                candidate_prior_admission_target="feature",
            )
        )
        graph_prior = np.zeros((4, 4), dtype=np.float32)
        graph_prior[1, 0] = 1.0
        candidate_prior = np.zeros((4, 4), dtype=np.float32)
        candidate_prior[2, 3] = 0.8
        path_evidence = np.zeros((4, 4), dtype=np.float32)
        path_evidence[2, 3] = 1.0
        model.set_graph_prior(graph_prior)
        model.set_path_candidate_prior(candidate_prior)
        model.set_path_evidence(path_evidence)

        out = model(torch.randn(2, 6, 4), return_diagnostics=True)
        diag = out["diagnostics"]

        self.assertIn("rpf_feature_prior_adjacency", diag)
        self.assertAlmostEqual(float(diag["rpf_prior_adjacency"][:, 1, 0].min()), 1.0, places=6)
        self.assertAlmostEqual(float(diag["rpf_prior_adjacency"][:, 2, 3].max()), 0.0, places=6)
        self.assertGreater(float(diag["rpf_feature_prior_adjacency"][:, 2, 3].mean()), 0.79)

    def test_candidate_prior_admission_min_support_hard_rejects_weak_candidates(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=1,
                max_paths=4,
                prior_strength=1.0,
                prior_coverage_fraction=1.0,
                use_candidate_prior_admission=True,
                candidate_prior_admission_floor=0.0,
                candidate_prior_admission_threshold=0.50,
                candidate_prior_admission_temperature=0.05,
                candidate_prior_admission_support_mode="absolute",
                candidate_prior_admission_scale=1.0,
                candidate_prior_admission_min_support=0.60,
                candidate_prior_admission_target="proposal_feature",
            )
        )
        graph_prior = np.zeros((4, 4), dtype=np.float32)
        graph_prior[1, 0] = 1.0
        candidate_prior = np.zeros((4, 4), dtype=np.float32)
        candidate_prior[2, 3] = 0.8
        candidate_prior[3, 2] = 0.8
        path_evidence = np.zeros((4, 4), dtype=np.float32)
        path_evidence[2, 3] = 0.70
        path_evidence[3, 2] = 0.40
        model.set_graph_prior(graph_prior)
        model.set_path_candidate_prior(candidate_prior)
        model.set_path_evidence(path_evidence)

        out = model(torch.randn(2, 6, 4), return_diagnostics=True)
        diag = out["diagnostics"]

        self.assertIn("candidate_prior_admission_mask", diag)
        self.assertIn("rpf_candidate_proposal_adjacency", diag)
        self.assertGreater(float(diag["rpf_candidate_proposal_adjacency"][:, 2, 3].mean()), 0.75)
        self.assertAlmostEqual(float(diag["rpf_candidate_proposal_adjacency"][:, 3, 2].max()), 0.0, places=6)
        self.assertTrue(bool(diag["candidate_prior_admission_mask"][:, 2, 3].all().item()))
        self.assertFalse(bool(diag["candidate_prior_admission_mask"][:, 3, 2].any().item()))

    def test_candidate_prior_admission_raises_support_floor_for_protected_classes(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                dropout=0.0,
                graph_top_k=1,
                max_paths=4,
                prior_strength=1.0,
                prior_coverage_fraction=1.0,
                use_class_conditioned_evidence=True,
                use_candidate_prior_admission=True,
                candidate_prior_admission_floor=0.0,
                candidate_prior_admission_threshold=0.50,
                candidate_prior_admission_temperature=0.05,
                candidate_prior_admission_support_mode="absolute",
                candidate_prior_admission_scale=1.0,
                candidate_prior_admission_min_support=0.50,
                candidate_prior_admission_protected_min_support=0.70,
                candidate_prior_admission_target="proposal_feature",
            )
        )
        assert model.class_evidence_router is not None
        router_head = model.class_evidence_router[-1]
        assert isinstance(router_head, torch.nn.Linear)
        torch.nn.init.zeros_(router_head.weight)
        torch.nn.init.zeros_(router_head.bias)
        model.set_candidate_protected_classes([1])

        graph_prior = np.zeros((4, 4), dtype=np.float32)
        graph_prior[1, 0] = 1.0
        candidate_prior = np.zeros((4, 4), dtype=np.float32)
        candidate_prior[2, 3] = 0.8
        candidate_prior[3, 2] = 0.8
        class_evidence = np.zeros((2, 4, 4), dtype=np.float32)
        class_evidence[:, 2, 3] = 0.58
        class_evidence[:, 3, 2] = 0.80
        model.set_graph_prior(graph_prior)
        model.set_path_candidate_prior(candidate_prior)
        model.set_class_path_evidence(class_evidence)

        out = model(torch.randn(2, 6, 4), return_diagnostics=True)
        diag = out["diagnostics"]

        self.assertIn("candidate_protected_class_mass", diag)
        self.assertIn("candidate_prior_admission_mask", diag)
        self.assertAlmostEqual(float(diag["candidate_protected_class_mass"].mean()), 0.5, places=6)
        self.assertAlmostEqual(float(diag["rpf_candidate_proposal_adjacency"][:, 2, 3].max()), 0.0, places=6)
        self.assertGreater(float(diag["rpf_candidate_proposal_adjacency"][:, 3, 2].mean()), 0.75)
        self.assertFalse(bool(diag["candidate_prior_admission_mask"][:, 2, 3].any().item()))
        self.assertTrue(bool(diag["candidate_prior_admission_mask"][:, 3, 2].all().item()))

    def test_candidate_prior_admission_uses_weighted_protected_class_mass(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                dropout=0.0,
                graph_top_k=1,
                max_paths=4,
                prior_strength=1.0,
                prior_coverage_fraction=1.0,
                use_class_conditioned_evidence=True,
                use_candidate_prior_admission=True,
                candidate_prior_admission_floor=0.0,
                candidate_prior_admission_threshold=0.50,
                candidate_prior_admission_temperature=0.05,
                candidate_prior_admission_support_mode="absolute",
                candidate_prior_admission_scale=1.0,
                candidate_prior_admission_min_support=0.50,
                candidate_prior_admission_protected_min_support=0.70,
                candidate_prior_admission_target="proposal_feature",
            )
        )
        assert model.class_evidence_router is not None
        router_head = model.class_evidence_router[-1]
        assert isinstance(router_head, torch.nn.Linear)
        torch.nn.init.zeros_(router_head.weight)
        with torch.no_grad():
            router_head.bias.copy_(torch.tensor([-8.0, 8.0]))
        model.set_candidate_protected_class_weights([0.0, 0.50])

        graph_prior = np.zeros((4, 4), dtype=np.float32)
        graph_prior[1, 0] = 1.0
        candidate_prior = np.zeros((4, 4), dtype=np.float32)
        candidate_prior[2, 3] = 0.8
        class_evidence = np.zeros((2, 4, 4), dtype=np.float32)
        class_evidence[:, 2, 3] = 0.58
        model.set_graph_prior(graph_prior)
        model.set_path_candidate_prior(candidate_prior)
        model.set_class_path_evidence(class_evidence)

        out = model(torch.randn(2, 6, 4), return_diagnostics=True)
        diag = out["diagnostics"]

        self.assertAlmostEqual(float(diag["candidate_protected_class_mass"].mean()), 0.50, places=5)
        self.assertFalse(bool(diag["candidate_prior_admission_mask"][:, 2, 3].any().item()))
        self.assertAlmostEqual(float(diag["rpf_candidate_proposal_adjacency"][:, 2, 3].max()), 0.0, places=6)

    def test_path_evidence_matrix_is_used_as_rpf_path_feature(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=2,
            use_reliability=True,
            use_path_fusion=True,
            use_task_salience=True,
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.90, 0.10],
                    [0.20, 0.0, 0.30],
                    [0.40, 0.50, 0.0],
                ]
            ],
            dtype=torch.float32,
        )
        path_evidence = torch.zeros(3, 3)
        path_evidence[0, 1] = 0.75

        _fused, diag = fusion(node_states, adjacency, path_evidence=path_evidence)

        pairs = list(zip(diag["path_source"][0].tolist(), diag["path_target"][0].tolist()))
        edge_pos = pairs.index((1, 0))
        self.assertAlmostEqual(float(diag["path_salience_weight"][0, edge_pos]), 0.75, places=6)

    def test_sample_path_evidence_matrix_is_used_as_rpf_path_feature(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=2,
            use_reliability=True,
            use_path_fusion=True,
            use_task_salience=True,
        )
        node_states = torch.randn(2, 3, 4)
        adjacency = torch.tensor(
            [
                [[0.0, 0.90, 0.10], [0.20, 0.0, 0.30], [0.40, 0.50, 0.0]],
                [[0.0, 0.90, 0.10], [0.20, 0.0, 0.30], [0.40, 0.50, 0.0]],
            ],
            dtype=torch.float32,
        )
        path_evidence = torch.zeros(2, 3, 3)
        path_evidence[0, 0, 1] = 0.25
        path_evidence[1, 0, 1] = 0.85

        _fused, diag = fusion(node_states, adjacency, path_evidence=path_evidence)

        pairs0 = list(zip(diag["path_source"][0].tolist(), diag["path_target"][0].tolist()))
        pairs1 = list(zip(diag["path_source"][1].tolist(), diag["path_target"][1].tolist()))
        edge_pos0 = pairs0.index((1, 0))
        edge_pos1 = pairs1.index((1, 0))
        self.assertAlmostEqual(float(diag["path_salience_weight"][0, edge_pos0]), 0.25, places=6)
        self.assertAlmostEqual(float(diag["path_salience_weight"][1, edge_pos1]), 0.85, places=6)

    def test_path_proposal_consistency_downweights_unsupported_dynamic_paths(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=1,
            use_reliability=False,
            use_path_fusion=True,
            use_task_salience=True,
            use_path_proposal_consistency=True,
            path_proposal_consistency_strength=1.0,
            path_proposal_consistency_threshold=0.50,
            path_proposal_consistency_temperature=0.02,
            path_proposal_consistency_floor=0.01,
            path_proposal_consistency_support_mode="salience",
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.60
        path_evidence = torch.zeros(3, 3)
        path_evidence[2, 0] = 1.0

        _fused, diag = fusion(node_states, adjacency, path_evidence=path_evidence)

        self.assertEqual(int(diag["path_target"][0, 0]), 2)
        self.assertEqual(int(diag["path_source"][0, 0]), 0)
        self.assertGreater(float(diag["path_proposal_consistency_support"][0, 0]), 0.95)
        self.assertGreater(float(diag["path_proposal_consistency_gate"][0, 0]), 0.95)

    def test_path_proposal_consistency_can_apply_only_to_protected_samples(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=1,
            use_reliability=False,
            use_path_fusion=True,
            use_task_salience=False,
            use_path_proposal_consistency=True,
            path_proposal_consistency_strength=0.0,
            path_proposal_consistency_protected_strength=1.0,
            path_proposal_consistency_threshold=0.50,
            path_proposal_consistency_temperature=0.02,
            path_proposal_consistency_floor=0.01,
            path_proposal_consistency_support_mode="prior",
        )
        node_states = torch.randn(2, 3, 4)
        adjacency = torch.zeros(2, 3, 3)
        adjacency[:, 1, 0] = 0.90
        adjacency[:, 2, 0] = 0.60
        prior = torch.zeros(3, 3)
        prior[2, 0] = 1.0
        protected_mass = torch.tensor([0.0, 1.0])

        _fused, diag = fusion(
            node_states,
            adjacency,
            prior_adjacency=prior,
            proposal_protected_mass=protected_mass,
        )

        self.assertEqual(int(diag["path_target"][0, 0]), 1)
        self.assertEqual(int(diag["path_source"][0, 0]), 0)
        self.assertEqual(int(diag["path_target"][1, 0]), 2)
        self.assertEqual(int(diag["path_source"][1, 0]), 0)
        self.assertAlmostEqual(float(diag["path_proposal_consistency_effective_strength"][0]), 0.0, places=6)
        self.assertAlmostEqual(float(diag["path_proposal_consistency_effective_strength"][1]), 1.0, places=6)

    def test_path_proposal_relative_evidence_rescales_sample_support(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=1,
            use_reliability=False,
            use_path_fusion=True,
            use_task_salience=True,
            use_path_proposal_consistency=True,
            path_proposal_consistency_strength=1.0,
            path_proposal_consistency_threshold=0.50,
            path_proposal_consistency_temperature=0.02,
            path_proposal_consistency_floor=0.01,
            path_proposal_consistency_support_mode="relative_evidence",
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.60
        path_evidence = torch.zeros(3, 3)
        path_evidence[2, 0] = 0.05

        _fused, diag = fusion(node_states, adjacency, path_evidence=path_evidence)

        self.assertEqual(int(diag["path_target"][0, 0]), 2)
        self.assertEqual(int(diag["path_source"][0, 0]), 0)
        self.assertGreater(float(diag["path_proposal_consistency_support"][0, 0]), 0.95)

    def test_path_proposal_evidence_admit_rejects_prior_only_edges(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=1,
            use_reliability=False,
            use_path_fusion=True,
            use_task_salience=True,
            use_path_proposal_consistency=True,
            path_proposal_consistency_strength=1.0,
            path_proposal_consistency_threshold=0.50,
            path_proposal_consistency_temperature=0.02,
            path_proposal_consistency_floor=0.01,
            path_proposal_consistency_support_mode="evidence_admit",
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.60
        prior = torch.zeros(3, 3)
        prior[1, 0] = 1.0
        path_evidence = torch.zeros(3, 3)
        path_evidence[2, 0] = 0.05

        _fused, diag = fusion(node_states, adjacency, prior_adjacency=prior, path_evidence=path_evidence)

        self.assertEqual(int(diag["path_target"][0, 0]), 2)
        self.assertEqual(int(diag["path_source"][0, 0]), 0)
        self.assertGreater(float(diag["path_proposal_consistency_support"][0, 0]), 0.50)

    def test_path_proposal_retention_preserves_some_ungated_dynamic_paths(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=False,
            use_path_fusion=True,
            coverage_dedup_mode="hard",
            use_task_salience=True,
            use_path_proposal_consistency=True,
            path_proposal_consistency_strength=1.0,
            path_proposal_consistency_threshold=0.50,
            path_proposal_consistency_temperature=0.02,
            path_proposal_consistency_floor=0.01,
            path_proposal_consistency_support_mode="salience",
            path_proposal_retention_fraction=0.50,
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.60
        adjacency[0, 0, 2] = 0.40
        path_evidence = torch.zeros(3, 3)
        path_evidence[2, 0] = 1.0

        _fused, diag = fusion(node_states, adjacency, path_evidence=path_evidence)

        pairs = set(zip(diag["path_target"][0].tolist(), diag["path_source"][0].tolist()))
        self.assertIn((1, 0), pairs)
        self.assertIn((2, 0), pairs)

    def test_learned_path_admission_starts_neutral(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=5,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=4,
                use_task_salience=True,
                use_learned_path_admission=True,
                path_admission_strength=0.75,
            )
        )
        model.set_path_evidence(np.ones((5, 5), dtype=np.float32) - np.eye(5, dtype=np.float32))

        out = model(torch.randn(3, 6, 5), return_diagnostics=True)

        gate = out["diagnostics"]["path_admission_gate"]
        adjustment = out["diagnostics"]["path_admission_adjustment"]
        self.assertEqual(tuple(gate.shape), (3, 4))
        self.assertAlmostEqual(float(gate.mean()), 0.5, places=6)
        self.assertAlmostEqual(float(adjustment.abs().max()), 0.0, places=6)

    def test_path_prior_consistency_adjusts_only_prior_paths_by_dynamic_support(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=6,
            use_reliability=False,
            use_path_fusion=True,
            use_path_prior_consistency=True,
            path_prior_consistency_strength=0.50,
            path_prior_consistency_threshold=0.50,
            path_prior_consistency_temperature=0.02,
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.10
        adjacency[0, 0, 1] = 0.40
        prior = torch.zeros(3, 3)
        prior[1, 0] = 1.0
        prior[2, 0] = 1.0

        _fused, diag = fusion(node_states, adjacency, prior_adjacency=prior)

        pairs = list(zip(diag["path_target"][0].tolist(), diag["path_source"][0].tolist()))
        adjustment = diag["path_prior_consistency_adjustment"][0]
        support = diag["path_prior_consistency_support"][0]
        high_idx = pairs.index((1, 0))
        low_idx = pairs.index((2, 0))
        self.assertGreater(float(support[high_idx]), 0.50)
        self.assertLess(float(support[low_idx]), 0.50)
        self.assertGreater(float(adjustment[high_idx]), 0.0)
        self.assertLess(float(adjustment[low_idx]), 0.0)

    def test_path_prior_consistency_agreement_requires_salience_and_dynamic_support(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=False,
            use_path_fusion=True,
            use_task_salience=True,
            use_path_prior_consistency=True,
            path_prior_consistency_strength=0.50,
            path_prior_consistency_threshold=0.50,
            path_prior_consistency_temperature=0.02,
            path_prior_consistency_support_mode="agreement",
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.90
        prior = torch.zeros(3, 3)
        prior[1, 0] = 1.0
        prior[2, 0] = 1.0
        path_evidence = torch.zeros(3, 3)
        path_evidence[1, 0] = 0.90
        path_evidence[2, 0] = 0.10

        _fused, diag = fusion(node_states, adjacency, prior_adjacency=prior, path_evidence=path_evidence)

        pairs = list(zip(diag["path_target"][0].tolist(), diag["path_source"][0].tolist()))
        adjustment = diag["path_prior_consistency_adjustment"][0]
        support = diag["path_prior_consistency_support"][0]
        agreed_idx = pairs.index((1, 0))
        class_mismatch_idx = pairs.index((2, 0))
        self.assertGreater(float(support[agreed_idx]), 0.50)
        self.assertLess(float(support[class_mismatch_idx]), 0.50)
        self.assertGreater(float(adjustment[agreed_idx]), 0.0)
        self.assertLess(float(adjustment[class_mismatch_idx]), 0.0)

    def test_path_prior_consistency_class_blend_softens_weak_class_evidence(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=False,
            use_path_fusion=True,
            use_task_salience=True,
            use_path_prior_consistency=True,
            path_prior_consistency_strength=0.50,
            path_prior_consistency_threshold=0.50,
            path_prior_consistency_temperature=0.02,
            path_prior_consistency_support_mode="class_blend",
            path_prior_consistency_class_floor=0.25,
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.90
        prior = torch.zeros(3, 3)
        prior[1, 0] = 1.0
        prior[2, 0] = 1.0
        path_evidence = torch.zeros(3, 3)
        path_evidence[1, 0] = 0.90
        path_evidence[2, 0] = 0.10

        _fused, diag = fusion(node_states, adjacency, prior_adjacency=prior, path_evidence=path_evidence)

        pairs = list(zip(diag["path_target"][0].tolist(), diag["path_source"][0].tolist()))
        adjustment = diag["path_prior_consistency_adjustment"][0]
        support = diag["path_prior_consistency_support"][0]
        supported_idx = pairs.index((1, 0))
        weak_class_idx = pairs.index((2, 0))
        self.assertGreater(float(support[supported_idx]), 0.80)
        self.assertGreater(float(support[weak_class_idx]), 0.25)
        self.assertLess(float(support[weak_class_idx]), 0.50)
        self.assertGreater(float(adjustment[supported_idx]), 0.0)
        self.assertLess(float(adjustment[weak_class_idx]), 0.0)

    def test_path_evidence_consistency_adjusts_paths_without_prior_coverage(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=False,
            use_path_fusion=True,
            use_task_salience=True,
            use_path_evidence_consistency=True,
            path_evidence_consistency_strength=0.50,
            path_evidence_consistency_threshold=0.50,
            path_evidence_consistency_temperature=0.02,
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.90
        adjacency[0, 0, 1] = 0.70
        path_evidence = torch.zeros(3, 3)
        path_evidence[1, 0] = 0.90
        path_evidence[2, 0] = 0.10

        _fused, diag = fusion(node_states, adjacency, path_evidence=path_evidence)

        pairs = list(zip(diag["path_target"][0].tolist(), diag["path_source"][0].tolist()))
        support = diag["path_evidence_consistency_support"][0]
        gate = diag["path_evidence_consistency_gate"][0]
        adjustment = diag["path_evidence_consistency_adjustment"][0]
        prior_weight = diag["path_prior_weight"][0]
        high_idx = pairs.index((1, 0))
        low_idx = pairs.index((2, 0))
        self.assertGreater(float(support[high_idx]), 0.50)
        self.assertLess(float(support[low_idx]), 0.50)
        self.assertGreater(float(gate[high_idx]), 0.90)
        self.assertLess(float(gate[low_idx]), 0.10)
        self.assertGreater(float(adjustment[high_idx]), 0.0)
        self.assertLess(float(adjustment[low_idx]), 0.0)
        self.assertAlmostEqual(float(prior_weight.abs().max()), 0.0, places=6)
        zero_support = support.eq(0.0)
        if bool(zero_support.any().item()):
            self.assertAlmostEqual(float(adjustment[zero_support].abs().max()), 0.0, places=6)

    def test_relative_path_evidence_consistency_uses_selected_path_rank(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=False,
            use_path_fusion=True,
            use_task_salience=True,
            use_path_evidence_consistency=True,
            path_evidence_consistency_strength=0.50,
            path_evidence_consistency_threshold=0.50,
            path_evidence_consistency_temperature=0.02,
            path_evidence_consistency_support_mode="relative",
        )
        node_states = torch.randn(1, 3, 4)
        adjacency = torch.zeros(1, 3, 3)
        adjacency[0, 1, 0] = 0.90
        adjacency[0, 2, 0] = 0.90
        path_evidence = torch.zeros(3, 3)
        path_evidence[1, 0] = 0.09
        path_evidence[2, 0] = 0.01

        _fused, diag = fusion(node_states, adjacency, path_evidence=path_evidence)

        pairs = list(zip(diag["path_target"][0].tolist(), diag["path_source"][0].tolist()))
        support = diag["path_evidence_consistency_support"][0]
        adjustment = diag["path_evidence_consistency_adjustment"][0]
        high_idx = pairs.index((1, 0))
        low_idx = pairs.index((2, 0))
        self.assertAlmostEqual(float(support[high_idx]), 1.0, places=6)
        self.assertLess(float(support[low_idx]), 0.50)
        self.assertGreater(float(adjustment[high_idx]), 0.0)
        self.assertLess(float(adjustment[low_idx]), 0.0)

    def test_edge_family_router_builds_samplewise_rpf_prior(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=4,
                prior_coverage_fraction=0.25,
                use_edge_family_router=True,
                edge_family_count=3,
                edge_family_router_floor=0.05,
                edge_family_router_blend=1.0,
            )
        )
        base_prior = np.zeros((4, 4), dtype=np.float32)
        base_prior[1, 0] = 0.8
        model.set_graph_prior(base_prior)
        family_priors = np.zeros((3, 4, 4), dtype=np.float32)
        family_priors[0, 1, 0] = 0.8
        family_priors[1, 2, 0] = 0.7
        family_priors[2, 3, 1] = 0.9
        model.set_edge_family_priors(family_priors)

        out = model(torch.randn(5, 6, 4), return_diagnostics=True)

        weights = out["diagnostics"]["edge_family_router_weights"]
        routed = out["diagnostics"]["edge_family_routed_prior"]
        self.assertEqual(tuple(weights.shape), (5, 3))
        self.assertTrue(torch.allclose(weights.sum(dim=1), torch.ones(5), atol=1.0e-5))
        self.assertEqual(tuple(routed.shape), (5, 4, 4))
        self.assertGreater(float(routed[:, 2, 0].mean()), 0.0)

    def test_class_conditioned_evidence_router_outputs_logits(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=3,
                hidden_dim=6,
                graph_top_k=2,
                max_paths=3,
                use_task_salience=True,
                use_class_conditioned_evidence=True,
            )
        )
        class_evidence = torch.zeros(3, 4, 4)
        class_evidence[1, 0, 2] = 0.9
        model.set_class_path_evidence(class_evidence)

        out = model(torch.randn(2, 5, 4), return_diagnostics=True)

        self.assertEqual(tuple(out["evidence_router_logits"].shape), (2, 3))
        self.assertEqual(tuple(out["diagnostics"]["path_salience_weight"].shape), (2, 3))

    def test_class_evidence_router_reports_sample_admission_gate(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=3,
                hidden_dim=6,
                graph_top_k=2,
                max_paths=3,
                use_task_salience=True,
                use_class_conditioned_evidence=True,
                class_evidence_gate_threshold=1.0,
                class_evidence_gate_temperature=0.01,
            )
        )
        class_evidence = torch.ones(3, 4, 4)
        model.set_class_path_evidence(class_evidence)

        out = model(torch.randn(2, 5, 4), return_diagnostics=True)

        admission = out["diagnostics"]["class_evidence_admission"]
        self.assertEqual(tuple(admission.shape), (2,))
        self.assertLess(float(admission.max()), 0.01)

    def test_class_evidence_router_top_k_sharpens_fault_evidence(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=3,
                hidden_dim=6,
                graph_top_k=3,
                max_paths=6,
                use_task_salience=True,
                salience_coverage_fraction=0.50,
                use_class_conditioned_evidence=True,
                class_evidence_router_temperature=0.50,
                class_evidence_router_top_k=1,
            )
        )
        class_evidence = torch.zeros(3, 4, 4)
        class_evidence[1, 0, 2] = 1.0
        class_evidence[2, 0, 3] = 1.0
        model.set_class_path_evidence(class_evidence)
        router_linear = model.class_evidence_router[2]
        with torch.no_grad():
            router_linear.weight.zero_()
            router_linear.bias.copy_(torch.tensor([0.0, 4.0, 1.0]))

        out = model(torch.randn(2, 5, 4), return_diagnostics=True)

        gate = out["diagnostics"]["class_evidence_gate"]
        self.assertEqual(tuple(gate.shape), (2, 3))
        self.assertTrue(torch.allclose(gate[:, 1], torch.ones(2), atol=1.0e-6))
        self.assertTrue(torch.allclose(gate[:, [0, 2]], torch.zeros(2, 2), atol=1.0e-6))

    def test_edge_calibrator_reports_sample_gate_for_prior_edges(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=4,
                prior_strength=0.05,
                prior_coverage_fraction=0.25,
                use_edge_calibrator=True,
                edge_calibrator_floor=0.10,
                edge_calibrator_init_bias=2.0,
            )
        )
        prior = torch.zeros(4, 4)
        prior[0, 2] = 0.8
        prior[1, 3] = 0.6
        model.set_graph_prior(prior)

        out = model(torch.randn(3, 5, 4), return_diagnostics=True)

        gate = out["diagnostics"]["edge_calibrator_gate"]
        calibrated = out["diagnostics"]["calibrated_prior_adjacency"]
        self.assertIn("edge_calibrator_reg_loss", out)
        self.assertEqual(tuple(gate.shape), (3, 4, 4))
        self.assertEqual(tuple(calibrated.shape), (3, 4, 4))
        self.assertGreater(float(gate[:, 0, 2].mean()), 0.80)
        self.assertAlmostEqual(float(gate[:, 2, 0].max()), 0.0, places=6)

    def test_path_reliability_calibrator_is_zero_initialized_residual(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=2,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=4,
                use_path_reliability_calibrator=True,
            )
        )

        out = model(torch.randn(3, 5, 4), return_diagnostics=True)

        context = out["diagnostics"]["path_reliability_context"]
        self.assertEqual(tuple(context.shape), (3, 4))
        self.assertAlmostEqual(float(context.abs().max()), 0.0, places=6)

    def test_class_conditioned_prior_admission_filters_rpf_prior_edges(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=3,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=4,
                prior_strength=0.0,
                prior_coverage_fraction=0.50,
                use_class_conditioned_evidence=True,
                class_evidence_router_top_k=1,
                use_class_conditioned_prior_admission=True,
                class_prior_admission_floor=0.0,
            )
        )
        prior = torch.zeros(4, 4)
        prior[1, 0] = 1.0
        prior[2, 0] = 1.0
        model.set_graph_prior(prior)
        class_edges = torch.zeros(3, 4, 4)
        class_edges[1, 1, 0] = 1.0
        model.set_class_path_evidence(class_edges)
        assert model.class_evidence_router is not None
        with torch.no_grad():
            last = model.class_evidence_router[-1]
            last.weight.zero_()
            last.bias[:] = torch.tensor([-8.0, 8.0, -8.0])

        out = model(torch.randn(2, 5, 4), return_diagnostics=True)

        rpf_prior = out["diagnostics"]["rpf_prior_adjacency"]
        gate = out["diagnostics"]["class_prior_admission_gate"]
        self.assertEqual(tuple(rpf_prior.shape), (2, 4, 4))
        self.assertGreater(float(gate[:, 1, 0].mean()), 0.99)
        self.assertAlmostEqual(float(rpf_prior[:, 2, 0].max()), 0.0, places=6)
        self.assertGreater(float(rpf_prior[:, 1, 0].mean()), 0.99)

    def test_adaptive_prior_admission_falls_back_when_router_uncertain(self) -> None:
        model = MSGSERPFNet(
            MSGSERPFConfig(
                n_features=4,
                n_classes=3,
                hidden_dim=8,
                graph_top_k=2,
                max_paths=4,
                prior_strength=0.0,
                prior_coverage_fraction=0.50,
                use_class_conditioned_evidence=True,
                use_class_conditioned_prior_admission=True,
                class_prior_admission_floor=0.0,
                use_adaptive_prior_admission=True,
                adaptive_prior_admission_threshold=0.90,
                adaptive_prior_admission_temperature=0.02,
            )
        )
        prior = torch.zeros(4, 4)
        prior[1, 0] = 1.0
        prior[2, 0] = 1.0
        model.set_graph_prior(prior)
        class_edges = torch.zeros(3, 4, 4)
        class_edges[1, 1, 0] = 1.0
        model.set_class_path_evidence(class_edges)
        assert model.class_evidence_router is not None
        with torch.no_grad():
            last = model.class_evidence_router[-1]
            last.weight.zero_()
            last.bias.zero_()

        out = model(torch.randn(2, 5, 4), return_diagnostics=True)

        rpf_prior = out["diagnostics"]["rpf_prior_adjacency"]
        trust = out["diagnostics"]["class_prior_admission_trust"]
        self.assertLess(float(trust.max()), 0.01)
        self.assertGreater(float(rpf_prior[:, 2, 0].mean()), 0.99)
        self.assertGreater(float(rpf_prior[:, 1, 0].mean()), 0.99)

    def test_class_path_evidence_is_train_only_and_class_conditioned(self) -> None:
        x = np.zeros((8, 4, 3), dtype=np.float32)
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int64)
        x[y == 1, :, 2] = 3.0
        evidence, diag = compute_train_class_path_evidence(
            x,
            y,
            np.arange(3),
            n_classes=2,
            top_k=1,
        )

        self.assertEqual(tuple(evidence.shape), (2, 3, 3))
        self.assertTrue(diag["enabled"])
        self.assertGreater(float(evidence[1, 2, 0]), 0.0)
        self.assertEqual(int(diag["nonzero_features_by_class"]["1"]), 1)

    def test_lag_aware_class_path_evidence_is_directed(self) -> None:
        rng = np.random.default_rng(7)
        x = rng.normal(0.0, 0.03, size=(18, 6, 3)).astype(np.float32)
        y = np.array([0] * 9 + [1] * 9, dtype=np.int64)
        for row in np.flatnonzero(y == 1):
            driver = rng.normal(0.0, 1.0, size=6).astype(np.float32)
            x[row, :, 0] = driver + 2.0
            x[row, 0, 1] = 2.0
            x[row, 1:, 1] = driver[:-1] + 2.0

        evidence, diag = compute_train_class_path_evidence(
            x,
            y,
            np.arange(3),
            n_classes=2,
            top_k=2,
            mode="lag",
            max_lag=1,
        )

        self.assertEqual(diag["mode"], "lag")
        self.assertGreater(float(diag["mean_lag_support"]), 0.0)
        self.assertGreater(float(evidence[1, 1, 0]), float(evidence[1, 0, 1]) + 0.20)

    def test_algorithmic_edge_prior_detects_directed_lag_and_caps_edges(self) -> None:
        rng = np.random.default_rng(19)
        x = rng.normal(0.0, 0.02, size=(24, 6, 4)).astype(np.float32)
        y = np.array([0] * 12 + [1] * 12, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=6).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 0, 1] = rng.normal(0.0, 0.02)
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=5)

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(4),
            n_classes=2,
            mode="lag",
            top_k=1,
            max_lag=1,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "lag")
        self.assertGreater(float(prior[1, 0]), float(prior[0, 1]) + 0.20)
        self.assertLessEqual(int(np.max(np.count_nonzero(prior > 0.0, axis=1))), 1)
        self.assertLessEqual(int(np.max(np.count_nonzero(prior > 0.0, axis=0))), 1)

    def test_multiview_algorithmic_edge_prior_detects_fault_response_order(self) -> None:
        rng = np.random.default_rng(23)
        x = rng.normal(0.0, 0.01, size=(24, 6, 4)).astype(np.float32)
        y = np.array([0] * 12 + [1] * 12, dtype=np.int64)
        for row in range(12, 24):
            x[row, 1, 0] += 3.0
            x[row, 2, 0] += 2.0
            x[row, 3, 1] += 3.0
            x[row, 4, 1] += 2.0

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.array([0, 1, 1, 2]),
            n_classes=2,
            mode="multiview",
            top_k=2,
            group_top_k=2,
            max_lag=1,
            corr_weight=0.0,
            lag_weight=0.0,
            class_weight=0.0,
            residual_weight=0.0,
            response_weight=1.0,
            stability_weight=0.0,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "multiview")
        self.assertIn("fault_response", diag["components"])
        self.assertGreater(float(prior[1, 0]), float(prior[0, 1]) + 0.20)

    def test_edge_bank_algorithmic_prior_keeps_corroborated_lag_edges(self) -> None:
        rng = np.random.default_rng(29)
        x = rng.normal(0.0, 0.01, size=(32, 6, 4)).astype(np.float32)
        y = np.array([0] * 16 + [1] * 16, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=6).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=5)

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(4),
            n_classes=2,
            mode="edge_bank",
            top_k=2,
            max_lag=1,
            bank_min_votes=2,
            bank_single_view_scale=0.0,
            bank_global_budget_multiplier=1.0,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_bank")
        self.assertIn("lag", diag["components"])
        self.assertGreater(int(diag["edge_bank"]["corroborated_edges"]), 0)
        self.assertLessEqual(int(diag["matched_edges"]), 4)
        self.assertEqual(int(diag["edge_bank"]["global_budget"]), 4)
        self.assertGreater(float(prior[1, 0]), 0.0)
        top_sources = [record["sources"] for record in diag["top_edge_indices"] if record["target"] == 1 and record["source"] == 0]
        self.assertTrue(any(len(sources) >= 2 for sources in top_sources))

    def test_edge_pool_algorithmic_prior_keeps_weak_dynamic_candidates(self) -> None:
        rng = np.random.default_rng(31)
        x = rng.normal(0.0, 0.01, size=(28, 6, 4)).astype(np.float32)
        y = np.array([0] * 14 + [1] * 14, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=6).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=5)

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(4),
            n_classes=2,
            mode="edge_pool",
            top_k=1,
            max_lag=1,
            corr_weight=0.0,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=0.0,
            stability_weight=0.0,
            bank_min_votes=2,
            bank_single_view_scale=0.40,
            pool_multiplier=2.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_pool")
        self.assertIn("lag", diag["components"])
        self.assertGreater(int(diag["edge_pool"]["single_view_edges"]), 0)
        self.assertGreater(float(prior[1, 0]), 0.0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task"])
        self.assertEqual(tuple(diag["_edge_family_prior_matrices"].shape), (3, 4, 4))

    def test_edge_cert_pool_algorithmic_prior_keeps_mechanism_certified_edges(self) -> None:
        rng = np.random.default_rng(36)
        x = rng.normal(0.0, 0.01, size=(36, 8, 5)).astype(np.float32)
        y = np.array([0] * 18 + [1] * 18, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
            if y[row] == 1:
                x[row, 1, 0] += 2.5
                x[row, 2, 1] += 2.5

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(5),
            n_classes=2,
            mode="edge_cert_pool",
            top_k=2,
            max_lag=2,
            corr_weight=0.10,
            class_weight=0.40,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=0.50,
            stability_weight=0.50,
            bank_min_votes=2,
            bank_single_view_scale=0.30,
            pool_multiplier=2.0,
            pool_rank_weight=0.30,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_cert_pool")
        self.assertIn("edge_cert_pool", diag)
        self.assertGreater(float(prior[1, 0]), 0.0)
        self.assertGreaterEqual(int(diag["edge_cert_pool"]["dynamic_edges"]), 1)
        self.assertGreater(float(diag["edge_cert_pool"]["mean_certificate"]), 0.0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task"])
        self.assertEqual(tuple(diag["_edge_family_prior_matrices"].shape), (3, 5, 5))

    def test_edge_cert_overlay_preserves_edge_pool_backbone(self) -> None:
        rng = np.random.default_rng(38)
        x = rng.normal(0.0, 0.01, size=(36, 8, 5)).astype(np.float32)
        y = np.array([0] * 18 + [1] * 18, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
            if y[row] == 1:
                x[row, 1, 0] += 2.0
                x[row, 2, 1] += 2.0

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(5),
            n_classes=2,
            mode="edge_cert_overlay",
            top_k=2,
            max_lag=2,
            corr_weight=0.10,
            class_weight=0.40,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=0.50,
            stability_weight=0.50,
            bank_min_votes=2,
            bank_single_view_scale=0.30,
            pool_multiplier=2.0,
            pool_rank_weight=0.30,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_cert_overlay")
        self.assertTrue(diag["edge_pool"]["enabled"])
        self.assertTrue(diag["edge_cert_pool"]["enabled"])
        self.assertTrue(diag["edge_cert_overlay"]["enabled"])
        self.assertTrue(diag["edge_cert_overlay"]["graph_uses_base_prior"])
        self.assertEqual(
            int(diag["edge_cert_overlay"]["graph_edges"]),
            int(diag["edge_cert_overlay"]["base_edges"]),
        )
        self.assertGreaterEqual(
            int(diag["edge_cert_overlay"]["final_edges"]),
            int(diag["edge_cert_overlay"]["base_edges"]),
        )
        candidate_prior = diag.get("_path_candidate_prior_matrix")
        self.assertIsNotNone(candidate_prior)
        assert candidate_prior is not None
        self.assertEqual(
            int(np.count_nonzero(np.asarray(candidate_prior) > 0.0)),
            int(diag["edge_cert_overlay"]["path_candidate_edges"]),
        )
        self.assertEqual(int(diag["matched_edges"]), int(diag["edge_cert_overlay"]["base_edges"]))
        self.assertGreater(float(prior[1, 0]), 0.0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task"])

    def test_edge_canvas_algorithmic_prior_keeps_innovation_candidates(self) -> None:
        rng = np.random.default_rng(37)
        x = rng.normal(0.0, 0.005, size=(36, 8, 5)).astype(np.float32)
        y = np.array([0] * 18 + [1] * 18, dtype=np.int64)
        for row in range(x.shape[0]):
            source_delta = rng.normal(0.0, 1.0, size=7).astype(np.float32)
            target_delta = np.concatenate([[0.0], source_delta[:-1]]).astype(np.float32)
            x[row, 0, 0] = 0.0
            x[row, 1:, 0] = np.cumsum(source_delta)
            x[row, 0, 1] = 0.0
            x[row, 1:, 1] = np.cumsum(target_delta + rng.normal(0.0, 0.01, size=7))

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(5),
            n_classes=2,
            mode="edge_canvas",
            top_k=1,
            max_lag=1,
            corr_weight=0.0,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=0.0,
            stability_weight=0.0,
            bank_min_votes=2,
            bank_single_view_scale=0.40,
            pool_multiplier=2.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_canvas")
        self.assertIn("innovation", diag["components"])
        self.assertIn("directed_lag", diag["components"])
        self.assertGreater(int(diag["edge_canvas"]["dynamic_edges"]), 0)
        self.assertGreater(float(prior[1, 0]), 0.0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task"])
        family_priors = diag["_edge_family_prior_matrices"]
        self.assertEqual(tuple(family_priors.shape), (3, 5, 5))
        self.assertGreater(float(family_priors[1, 1, 0]), 0.0)

    def test_edge_universe_algorithmic_prior_preserves_family_candidates(self) -> None:
        rng = np.random.default_rng(41)
        x = rng.normal(0.0, 0.01, size=(40, 8, 5)).astype(np.float32)
        y = np.array([0] * 20 + [1] * 20, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
        for row in range(20, 40):
            x[row, 1, 0] += 3.0
            x[row, 2, 0] += 2.0
            x[row, 3, 2] += 3.0
            x[row, 4, 2] += 2.0

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(5),
            n_classes=2,
            mode="edge_universe",
            top_k=2,
            max_lag=1,
            corr_weight=0.0,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=1.0,
            stability_weight=0.0,
            bank_min_votes=2,
            bank_single_view_scale=0.50,
            pool_multiplier=2.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_universe")
        self.assertIn("lag", diag["components"])
        self.assertIn("fault_response", diag["components"])
        self.assertGreater(int(diag["edge_universe"]["family_edge_counts"]["dynamic"]), 0)
        self.assertGreater(int(diag["edge_universe"]["family_edge_counts"]["task"]), 0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task"])
        family_priors = diag["_edge_family_prior_matrices"]
        self.assertEqual(tuple(family_priors.shape), (3, 5, 5))
        self.assertGreater(float(np.sum(family_priors[1])), 0.0)
        self.assertGreater(float(np.sum(family_priors[2])), 0.0)

    def test_edge_lattice_algorithmic_prior_expands_group_mechanism_candidates(self) -> None:
        rng = np.random.default_rng(42)
        x = rng.normal(0.0, 0.01, size=(40, 8, 5)).astype(np.float32)
        y = np.array([0] * 20 + [1] * 20, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
        groups = np.array([0, 1, 1, 2, 3], dtype=np.int64)

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            groups,
            n_classes=2,
            mode="edge_lattice",
            top_k=2,
            group_top_k=2,
            max_lag=1,
            corr_weight=0.0,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=0.0,
            stability_weight=0.0,
            bank_min_votes=2,
            bank_single_view_scale=0.50,
            pool_multiplier=2.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_lattice")
        self.assertIn("lag", diag["components"])
        self.assertTrue(diag["edge_lattice"]["enabled"])
        self.assertGreater(int(diag["edge_lattice"]["expanded_only_edges"]), 0)
        self.assertGreater(float(prior[1, 0]), 0.0)
        self.assertGreater(float(prior[2, 0]), 0.0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task", "group_lattice"])
        family_priors = diag["_edge_family_prior_matrices"]
        self.assertEqual(tuple(family_priors.shape), (4, 5, 5))
        self.assertGreater(float(family_priors[3, 2, 0]), 0.0)

    def test_edge_dual_lattice_keeps_core_graph_and_wider_path_candidates(self) -> None:
        rng = np.random.default_rng(426)
        x = rng.normal(0.0, 0.01, size=(44, 8, 5)).astype(np.float32)
        y = np.array([0] * 22 + [1] * 22, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
        groups = np.array([0, 1, 1, 2, 3], dtype=np.int64)

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            groups,
            n_classes=2,
            mode="edge_dual_lattice",
            top_k=1,
            group_top_k=1,
            max_lag=1,
            corr_weight=0.0,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=0.0,
            stability_weight=0.0,
            bank_min_votes=2,
            bank_single_view_scale=0.50,
            pool_multiplier=2.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_dual_lattice")
        self.assertTrue(diag["edge_pool"]["enabled"])
        self.assertTrue(diag["edge_lattice"]["enabled"])
        self.assertTrue(diag["edge_dual_lattice"]["graph_uses_core_prior"])
        self.assertEqual(int(np.count_nonzero(prior > 0.0)), int(diag["edge_dual_lattice"]["core_edges"]))
        self.assertGreater(int(diag["edge_dual_lattice"]["expanded_candidate_edges"]), 0)
        candidate_prior = diag.get("_path_candidate_prior_matrix")
        self.assertIsNotNone(candidate_prior)
        assert candidate_prior is not None
        self.assertGreater(
            int(np.count_nonzero(np.asarray(candidate_prior) > 0.0)),
            int(np.count_nonzero(prior > 0.0)),
        )
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task", "group_lattice"])

    def test_edge_guarded_lattice_uses_mechanism_sieve_for_path_candidates(self) -> None:
        rng = np.random.default_rng(426)
        x = rng.normal(0.0, 0.01, size=(44, 8, 5)).astype(np.float32)
        y = np.array([0] * 22 + [1] * 22, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
        for row in range(22, 44):
            x[row, 1, 0] += 3.0
            x[row, 2, 0] += 2.0
            x[row, 3, 2] += 3.0
            x[row, 4, 2] += 2.0
        groups = np.array([0, 1, 1, 2, 3], dtype=np.int64)

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            groups,
            n_classes=2,
            mode="edge_guarded_lattice",
            top_k=1,
            group_top_k=1,
            max_lag=1,
            corr_weight=0.0,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=1.0,
            stability_weight=1.0,
            bank_min_votes=2,
            bank_single_view_scale=0.50,
            pool_multiplier=2.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_guarded_lattice")
        self.assertTrue(diag["edge_pool"]["enabled"])
        self.assertTrue(diag["edge_sieve"]["enabled"])
        self.assertEqual(diag["edge_guarded_lattice"]["guarded_source"], "edge_sieve")
        self.assertTrue(diag["edge_guarded_lattice"]["graph_uses_core_prior"])
        self.assertEqual(int(np.count_nonzero(prior > 0.0)), int(diag["edge_guarded_lattice"]["core_edges"]))
        self.assertGreater(int(diag["edge_guarded_lattice"]["expanded_candidate_edges"]), 0)
        candidate_prior = diag.get("_path_candidate_prior_matrix")
        self.assertIsNotNone(candidate_prior)
        assert candidate_prior is not None
        self.assertGreater(
            int(np.count_nonzero(np.asarray(candidate_prior) > 0.0)),
            int(np.count_nonzero(prior > 0.0)),
        )
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task"])

    def test_edge_lattice_algorithmic_prior_expands_unique_groups_by_affinity(self) -> None:
        rng = np.random.default_rng(421)
        x = rng.normal(0.0, 0.01, size=(44, 8, 6)).astype(np.float32)
        y = np.array([0] * 22 + [1] * 22, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
            x[row, :, 2] = x[row, :, 1] + rng.normal(0.0, 0.005, size=8)

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(6),
            n_classes=2,
            mode="edge_lattice",
            top_k=2,
            group_top_k=0,
            max_lag=1,
            corr_weight=0.15,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=0.0,
            stability_weight=0.0,
            bank_min_votes=2,
            bank_single_view_scale=0.50,
            pool_multiplier=2.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        lattice = diag["edge_lattice"]["group_lattice"]
        self.assertTrue(lattice["affinity_enabled"])
        self.assertGreater(int(lattice["affinity_expanded_edges"]), 0)
        self.assertGreater(int(diag["edge_lattice"]["expanded_only_edges"]), 0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task", "group_lattice"])

    def test_edge_sieve_algorithmic_prior_keeps_stable_mechanism_edges(self) -> None:
        rng = np.random.default_rng(43)
        x = rng.normal(0.0, 0.01, size=(48, 8, 5)).astype(np.float32)
        y = np.array([0] * 24 + [1] * 24, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
        for row in range(24, 48):
            x[row, 1, 0] += 2.5
            x[row, 2, 0] += 1.5
            x[row, 3, 2] += 2.5
            x[row, 4, 2] += 1.5

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(5),
            n_classes=2,
            mode="edge_sieve",
            top_k=2,
            max_lag=1,
            corr_weight=0.0,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=1.0,
            stability_weight=1.0,
            bank_min_votes=2,
            bank_single_view_scale=0.30,
            pool_multiplier=3.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_sieve")
        self.assertIn("stability", diag["components"])
        self.assertGreater(int(diag["edge_sieve"]["stability_guarded_edges"]), 0)
        self.assertGreater(float(prior[1, 0]), 0.0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task"])
        family_priors = diag["_edge_family_prior_matrices"]
        self.assertEqual(tuple(family_priors.shape), (3, 5, 5))
        self.assertGreater(float(np.sum(family_priors[1])), 0.0)

    def test_edge_overlay_preserves_base_edges_and_adds_sieve_candidates(self) -> None:
        rng = np.random.default_rng(47)
        x = rng.normal(0.0, 0.01, size=(48, 8, 5)).astype(np.float32)
        y = np.array([0] * 24 + [1] * 24, dtype=np.int64)
        for row in range(x.shape[0]):
            driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 0] = driver
            x[row, 1:, 1] = driver[:-1] + rng.normal(0.0, 0.01, size=7)
            second_driver = rng.normal(0.0, 1.0, size=8).astype(np.float32)
            x[row, :, 3] = second_driver
            x[row, 1:, 4] = second_driver[:-1] + rng.normal(0.0, 0.01, size=7)
        for row in range(24, 48):
            x[row, 1, 0] += 2.5
            x[row, 2, 0] += 1.5
            x[row, 3, 2] += 2.5
            x[row, 4, 2] += 1.5

        prior, diag = compute_train_algorithmic_edge_prior(
            x,
            y,
            np.arange(5),
            n_classes=2,
            mode="edge_overlay",
            top_k=1,
            max_lag=1,
            corr_weight=0.0,
            class_weight=0.0,
            lag_weight=1.0,
            residual_weight=0.0,
            response_weight=1.0,
            stability_weight=1.0,
            bank_min_votes=2,
            bank_single_view_scale=0.30,
            pool_multiplier=3.0,
            pool_rank_weight=0.25,
        )

        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["mode"], "edge_overlay")
        self.assertTrue(diag["edge_pool"]["enabled"])
        self.assertTrue(diag["edge_sieve"]["enabled"])
        self.assertGreaterEqual(int(diag["edge_overlay"]["final_edges"]), int(diag["edge_overlay"]["base_edges"]))
        self.assertGreater(float(prior[1, 0]), 0.0)
        self.assertEqual(diag["edge_family_prior_names"], ["structural", "dynamic", "task"])

    def test_corroborated_prior_combination_dampens_external_only_edges(self) -> None:
        algorithmic = np.zeros((4, 4), dtype=np.float32)
        external = np.zeros((4, 4), dtype=np.float32)
        algorithmic[1, 0] = 0.60
        algorithmic[2, 0] = 0.50
        external[1, 0] = 0.70
        external[3, 2] = 0.80

        combined, diag = combine_algorithmic_and_external_priors(
            external,
            algorithmic,
            mode="corroborated_max",
            external_isolated_scale=0.25,
            overlap_boost=0.20,
        )

        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["overlap_edges"], 1)
        self.assertEqual(diag["external_only_edges"], 1)
        assert combined is not None
        self.assertGreater(float(combined[1, 0]), 0.70)
        self.assertAlmostEqual(float(combined[3, 2]), 0.20, places=5)
        self.assertAlmostEqual(float(combined[2, 0]), 0.50, places=5)

    def test_anchor_subgraph_combination_focuses_algorithmic_prior_near_external_endpoints(self) -> None:
        algorithmic = np.zeros((5, 5), dtype=np.float32)
        external = np.zeros((5, 5), dtype=np.float32)
        algorithmic[1, 0] = 0.60
        algorithmic[2, 0] = 0.50
        algorithmic[4, 3] = 0.80
        external[1, 0] = 0.70

        combined, diag = combine_algorithmic_and_external_priors(
            external,
            algorithmic,
            mode="anchored_subgraph",
            external_isolated_scale=0.25,
            overlap_boost=0.20,
            nonanchor_algorithmic_scale=0.25,
        )

        self.assertEqual(diag["mode"], "anchored_subgraph")
        self.assertEqual(diag["anchor_node_count"], 2)
        self.assertEqual(diag["anchor_algorithmic_edge_count"], 2)
        self.assertEqual(diag["nonanchor_algorithmic_edge_count"], 1)
        assert combined is not None
        self.assertGreater(float(combined[1, 0]), 0.70)
        self.assertAlmostEqual(float(combined[2, 0]), 0.50, places=5)
        self.assertAlmostEqual(float(combined[4, 3]), 0.20, places=5)

    def test_tri_source_combination_calibrates_external_edges_by_data_support(self) -> None:
        algorithmic = np.zeros((5, 5), dtype=np.float32)
        external = np.zeros((5, 5), dtype=np.float32)
        algorithmic[1, 0] = 0.60
        algorithmic[2, 0] = 0.50
        external[1, 0] = 0.70
        external[4, 3] = 0.80

        combined, diag = combine_algorithmic_and_external_priors(
            external,
            algorithmic,
            mode="tri_source_calibrated",
            external_isolated_scale=1.0,
            overlap_boost=0.10,
        )

        self.assertEqual(diag["mode"], "tri_source_calibrated")
        self.assertEqual(diag["overlap_edges"], 1)
        self.assertEqual(diag["external_data_unsupported_edges"], 1)
        assert combined is not None
        self.assertGreater(float(combined[1, 0]), 0.70)
        self.assertLess(float(combined[4, 3]), 0.20)
        self.assertAlmostEqual(float(combined[2, 0]), 0.50, places=5)

    def test_fault_family_class_path_evidence_records_neighbors(self) -> None:
        x = np.zeros((18, 4, 4), dtype=np.float32)
        y = np.array([0] * 6 + [1] * 6 + [2] * 6, dtype=np.int64)
        x[y == 0, :, 0] = 3.0
        x[y == 1, :, 0] = 2.8
        x[y == 2, :, 3] = 3.0

        evidence, diag = compute_train_class_path_evidence(
            x,
            y,
            np.arange(4),
            n_classes=3,
            top_k=1,
            family_k=1,
            family_weight=0.5,
        )

        self.assertEqual(tuple(evidence.shape), (3, 4, 4))
        self.assertTrue(diag["family_enabled"])
        self.assertEqual(int(diag["family_neighbor_count_by_class"]["1"]), 1)
        self.assertEqual(int(diag["family_neighbors_by_class"]["1"][0]["class"]), 2)

    def test_explicit_focus_class_evidence_downweights_nonfocus_classes(self) -> None:
        x = np.zeros((12, 4, 3), dtype=np.float32)
        y = np.array([0] * 4 + [1] * 4 + [2] * 4, dtype=np.int64)
        x[y == 0, :, 0] = 3.0
        x[y == 1, :, 1] = 3.0
        x[y == 2, :, 2] = 3.0

        evidence, diag = compute_train_class_path_evidence(
            x,
            y,
            np.arange(3),
            n_classes=3,
            top_k=1,
            focus_mode="explicit",
            focus_classes=[1],
            focus_nonfocus_weight=0.0,
        )

        self.assertTrue(diag["focus_enabled"])
        self.assertEqual(diag["focus_classes"], [1])
        self.assertGreater(float(np.max(evidence[1])), 0.0)
        self.assertAlmostEqual(float(np.max(evidence[0])), 0.0, places=6)
        self.assertAlmostEqual(float(np.max(evidence[2])), 0.0, places=6)

    def test_low_train_separation_focus_selects_hard_training_class(self) -> None:
        rng = np.random.default_rng(29)
        x = rng.normal(0.0, 0.05, size=(18, 4, 3)).astype(np.float32)
        y = np.array([0] * 6 + [1] * 6 + [2] * 6, dtype=np.int64)
        x[y == 0, :, 0] += 1.00
        x[y == 1, :, 0] += 1.05
        x[y == 2, :, 2] += 5.00

        _evidence, diag = compute_train_class_path_evidence(
            x,
            y,
            np.arange(3),
            n_classes=3,
            top_k=1,
            focus_mode="low_train_separation",
            focus_k=1,
        )

        self.assertTrue(diag["focus_enabled"])
        self.assertIn(int(diag["focus_classes"][0]), {0, 1})
        self.assertLess(
            float(diag["train_separation_by_class"][str(diag["focus_classes"][0])]),
            float(diag["train_separation_by_class"]["2"]),
        )

    def test_class_evidence_quality_certificate_filters_only_focus_classes(self) -> None:
        evidence = np.ones((3, 3, 3), dtype=np.float32)
        for cls in range(3):
            np.fill_diagonal(evidence[cls], 0.0)
        stability = np.ones_like(evidence, dtype=np.float32)
        stability[1, 0, 2] = 0.0
        stability[1, 2, 0] = 1.0

        filtered, diag = apply_class_evidence_quality_certificate(
            evidence,
            stability,
            focus_classes=[1],
            floor=0.20,
            threshold=0.50,
            temperature=0.02,
        )

        assert filtered is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["certified_classes"], [1])
        self.assertAlmostEqual(float(filtered[0, 0, 2]), 1.0, places=6)
        self.assertLess(float(filtered[1, 0, 2]), 0.25)
        self.assertGreater(float(filtered[1, 2, 0]), 0.95)
        self.assertLess(float(diag["class_retained_mass"]["1"]), 1.0)
        self.assertAlmostEqual(float(diag["class_retained_mass"]["0"]), 1.0, places=6)

    def test_path_family_quality_certificate_keeps_direct_and_group_supported_edges(self) -> None:
        evidence = np.ones((2, 4, 4), dtype=np.float32)
        for cls in range(2):
            np.fill_diagonal(evidence[cls], 0.0)
        family_support = np.zeros((4, 4), dtype=np.float32)
        family_support[1, 0] = 1.0
        groups = np.array([0, 1, 1, 2], dtype=np.int64)

        filtered, diag = apply_path_family_quality_certificate(
            evidence,
            family_support,
            groups,
            focus_classes=[1],
            floor=0.10,
            threshold=0.40,
            temperature=0.02,
            direct_weight=1.0,
            group_weight=0.50,
        )

        assert filtered is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["certified_classes"], [1])
        self.assertAlmostEqual(float(filtered[0, 3, 2]), 1.0, places=6)
        self.assertGreater(float(filtered[1, 1, 0]), 0.95)
        self.assertGreater(float(filtered[1, 2, 0]), 0.50)
        self.assertLess(float(filtered[1, 3, 0]), 0.15)
        self.assertLess(float(diag["class_retained_mass"]["1"]), 1.0)

    def test_path_family_quality_certificate_reports_proposal_protection_weights(self) -> None:
        evidence = np.ones((3, 4, 4), dtype=np.float32)
        for cls in range(3):
            np.fill_diagonal(evidence[cls], 0.0)
        family_support = np.zeros((4, 4), dtype=np.float32)
        family_support[1, 0] = 1.0

        filtered, diag = apply_path_family_quality_certificate(
            evidence,
            family_support,
            np.arange(4),
            focus_classes=[1, 2],
            floor=0.10,
            threshold=0.40,
            temperature=0.02,
            direct_weight=1.0,
            group_weight=0.0,
        )

        assert filtered is not None
        weights = diag["class_proposal_protection_weight"]
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(float(weights[0]), 0.0, places=6)
        self.assertGreater(float(weights[1]), 0.0)
        self.assertGreater(float(weights[2]), 0.0)
        self.assertLess(float(diag["class_active_gate_mean"]["1"]), 1.0)
        self.assertGreater(float(diag["class_protection_risk"]["1"]), 0.0)

    def test_path_family_quality_certificate_uses_class_specific_fault_family_support(self) -> None:
        evidence = np.zeros((3, 4, 4), dtype=np.float32)
        evidence[0, 1, 0] = 1.0
        evidence[1, 1, 0] = 0.9
        evidence[1, 2, 3] = 0.8
        evidence[2, 3, 2] = 1.0
        support = np.zeros((3, 4, 4), dtype=np.float32)
        support[1, 2, 3] = 1.0

        filtered, diag = apply_path_family_quality_certificate(
            evidence,
            support,
            np.arange(4),
            focus_classes=[1],
            mode="focus_fault_family",
            floor=0.05,
            threshold=0.40,
            temperature=0.02,
            direct_weight=1.0,
            group_weight=0.0,
            family_k=1,
            family_weight=0.70,
        )

        assert filtered is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["certified_classes"], [1])
        self.assertEqual(int(diag["family_k"]), 1)
        self.assertAlmostEqual(float(filtered[0, 1, 0]), 1.0, places=6)
        self.assertGreater(float(filtered[1, 2, 3]), 0.75)
        self.assertGreater(float(filtered[1, 1, 0]), 0.60)
        self.assertAlmostEqual(float(filtered[2, 3, 2]), 1.0, places=6)
        self.assertTrue(diag["family_neighbors_by_class"]["1"])

    def test_stable_class_edge_overlay_adds_stable_focus_edges(self) -> None:
        prior = np.zeros((4, 4), dtype=np.float32)
        prior[1, 0] = 0.80
        stable_global = np.zeros((4, 4), dtype=np.float32)
        stable_global[2, 0] = 0.60
        stable_class = np.zeros((3, 4, 4), dtype=np.float32)
        stable_class[1, 3, 0] = 0.90
        stable_class[2, 0, 3] = 0.95

        merged, diag = apply_stable_class_edge_overlay(
            prior,
            stable_global,
            stable_class,
            np.arange(4),
            focus_classes=[1],
            scale=0.50,
            top_k=2,
            group_top_k=0,
            focus_weight=1.25,
            nonfocus_weight=0.0,
        )

        assert merged is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["focus_classes"], [1])
        self.assertGreater(float(merged[1, 0]), 0.75)
        self.assertGreater(float(merged[3, 0]), 0.45)
        self.assertGreaterEqual(int(diag["new_edges"]), 1)
        self.assertAlmostEqual(float(merged[0, 3]), 0.0, places=6)

    def test_graph_prior_core_certificate_compresses_wide_candidate_prior(self) -> None:
        prior = np.zeros((4, 4), dtype=np.float32)
        prior[1, 0] = 1.0
        prior[2, 0] = 0.9
        prior[3, 0] = 0.8
        evidence = np.zeros((2, 4, 4), dtype=np.float32)
        evidence[1, 1, 0] = 1.0
        groups = np.array([0, 1, 1, 2], dtype=np.int64)

        core, diag = apply_graph_prior_core_certificate(
            prior,
            evidence,
            groups,
            focus_classes=[1],
            floor=0.05,
            threshold=0.30,
            temperature=0.02,
            top_k=2,
            group_top_k=2,
            group_weight=0.60,
            prior_weight=0.10,
        )

        assert core is not None
        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["status"], "ok")
        self.assertLess(int(diag["output_edges"]), int(diag["input_edges"]))
        self.assertGreater(float(core[1, 0]), 0.0)
        self.assertGreater(float(core[2, 0]), 0.0)
        self.assertEqual(float(core[3, 0]), 0.0)
        self.assertGreaterEqual(int(diag["supported_edges"]), 2)

    def test_prior_edge_calibration_filters_low_support_edges(self) -> None:
        x = np.zeros((12, 5, 3), dtype=np.float32)
        ramp = np.linspace(0.0, 1.0, 5, dtype=np.float32)
        for i in range(12):
            x[i, :, 0] = ramp + i * 0.01
            x[i, :, 1] = ramp + i * 0.01
            x[i, :, 2] = 1.0
        prior = np.zeros((3, 3), dtype=np.float32)
        prior[1, 0] = 0.8
        prior[2, 0] = 0.8

        calibrated, diag = calibrate_prior_adjacency_from_windows(
            prior,
            x,
            max_lag=1,
            min_support=0.95,
            strength=1.0,
        )

        self.assertTrue(diag["enabled"])
        self.assertGreater(float(calibrated[1, 0]), 0.0)
        self.assertEqual(float(calibrated[2, 0]), 0.0)

    def test_path_coverage_excludes_global_path_duplicates(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            coverage_mode="target_group",
            coverage_dedup_mode="hard",
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.90, 0.50, 0.40],
                    [0.80, 0.0, 0.45, 0.35],
                    [0.70, 0.30, 0.0, 0.20],
                    [0.60, 0.25, 0.15, 0.0],
                ]
            ],
            dtype=torch.float32,
        )
        _fused, diag = fusion(
            node_states,
            adjacency,
            feature_group_ids=torch.arange(4),
        )

        pairs = list(zip(diag["path_source"][0].tolist(), diag["path_target"][0].tolist()))
        self.assertEqual(len(pairs), 4)
        self.assertEqual(len(set(pairs)), 4)
        self.assertAlmostEqual(float(diag["path_duplicate_rate"][0]), 0.0, places=6)

    def test_prior_coverage_admits_weak_prior_edge_as_candidate(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            coverage_mode="target_group",
            coverage_dedup_mode="hard",
            prior_coverage_fraction=0.25,
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.95, 0.80, 0.01],
                    [0.20, 0.0, 0.94, 0.79],
                    [0.30, 0.40, 0.0, 0.93],
                    [0.92, 0.50, 0.60, 0.0],
                ]
            ],
            dtype=torch.float32,
        )
        prior = torch.zeros(4, 4, dtype=torch.float32)
        prior[0, 3] = 0.85

        _fused, diag = fusion(
            node_states,
            adjacency,
            prior_adjacency=prior,
            feature_group_ids=torch.arange(4),
        )

        pairs = list(zip(diag["path_source"][0].tolist(), diag["path_target"][0].tolist()))
        self.assertIn((3, 0), pairs)
        edge_pos = pairs.index((3, 0))
        self.assertAlmostEqual(float(diag["path_prior_weight"][0, edge_pos]), 0.85, places=6)

    def test_salience_coverage_admits_class_evidence_edge_without_static_prior(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            coverage_mode="target_group",
            coverage_dedup_mode="hard",
            use_task_salience=True,
            salience_coverage_fraction=0.25,
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.95, 0.80, 0.01],
                    [0.20, 0.0, 0.94, 0.79],
                    [0.30, 0.40, 0.0, 0.93],
                    [0.92, 0.50, 0.60, 0.0],
                ]
            ],
            dtype=torch.float32,
        )
        path_evidence = torch.zeros(1, 4, 4, dtype=torch.float32)
        path_evidence[0, 0, 3] = 1.0

        _fused, diag = fusion(
            node_states,
            adjacency,
            path_evidence=path_evidence,
            feature_group_ids=torch.arange(4),
        )

        pairs = list(zip(diag["path_source"][0].tolist(), diag["path_target"][0].tolist()))
        self.assertIn((3, 0), pairs)
        edge_pos = pairs.index((3, 0))
        self.assertAlmostEqual(float(diag["path_salience_weight"][0, edge_pos]), 1.0, places=6)
        self.assertAlmostEqual(float(diag["path_prior_weight"][0, edge_pos]), 0.0, places=6)

    def test_soft_redundancy_penalty_keeps_auditable_duplicates(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            coverage_mode="target_group",
            coverage_dedup_mode="soft",
            coverage_redundancy_penalty=0.01,
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.99, 0.05, 0.04],
                    [0.98, 0.0, 0.03, 0.02],
                    [0.97, 0.01, 0.0, 0.01],
                    [0.96, 0.01, 0.01, 0.0],
                ]
            ],
            dtype=torch.float32,
        )
        _fused, diag = fusion(
            node_states,
            adjacency,
            feature_group_ids=torch.arange(4),
        )

        pairs = list(zip(diag["path_source"][0].tolist(), diag["path_target"][0].tolist()))
        self.assertLess(len(set(pairs)), len(pairs))
        self.assertGreater(float(diag["path_duplicate_rate"][0]), 0.0)

    def test_exact_path_dedup_replaces_soft_duplicate_candidates(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            coverage_mode="target_group",
            coverage_dedup_mode="soft",
            coverage_redundancy_penalty=0.01,
            deduplicate_exact_paths=True,
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.99, 0.05, 0.04],
                    [0.98, 0.0, 0.03, 0.02],
                    [0.97, 0.01, 0.0, 0.01],
                    [0.96, 0.01, 0.01, 0.0],
                ]
            ],
            dtype=torch.float32,
        )
        _fused, diag = fusion(
            node_states,
            adjacency,
            feature_group_ids=torch.arange(4),
        )

        pairs = list(zip(diag["path_source"][0].tolist(), diag["path_target"][0].tolist()))
        self.assertEqual(len(set(pairs)), len(pairs))
        self.assertAlmostEqual(float(diag["path_duplicate_rate"][0]), 0.0, places=6)

    def test_inclusive_group_pair_coverage_can_use_same_family_stat_edges(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            coverage_mode="group_pair_inclusive",
            coverage_dedup_mode="hard",
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.99, 0.10, 0.05],
                    [0.98, 0.0, 0.09, 0.04],
                    [0.08, 0.07, 0.0, 0.06],
                    [0.05, 0.04, 0.03, 0.0],
                ]
            ],
            dtype=torch.float32,
        )
        _fused, diag = fusion(
            node_states,
            adjacency,
            feature_group_ids=torch.tensor([0, 0, 1, 1], dtype=torch.long),
        )

        pairs = list(zip(diag["path_source"][0].tolist(), diag["path_target"][0].tolist()))
        self.assertEqual(len(pairs), 4)
        self.assertEqual(len(set(pairs)), 4)
        self.assertIn((0, 1), pairs)

    def test_multihop_path_fusion_reports_bridge_paths(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            use_multihop_paths=True,
            multihop_path_fraction=0.25,
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.90, 0.10, 0.05],
                    [0.05, 0.0, 0.95, 0.05],
                    [0.05, 0.05, 0.0, 0.90],
                    [0.80, 0.05, 0.05, 0.0],
                ]
            ],
            dtype=torch.float32,
        )

        _fused, diag = fusion(node_states, adjacency)

        self.assertEqual(tuple(diag["path_weights"].shape), (1, 4))
        self.assertEqual(tuple(diag["path_bridge"].shape), (1, 4))
        self.assertIn(2, diag["path_hop_count"][0].tolist())
        self.assertTrue(any(int(v) >= 0 for v in diag["path_bridge"][0].tolist()))

    def test_context_router_is_reported_as_path_quality_signal(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=3,
            use_reliability=True,
            use_path_fusion=True,
            use_context_router=True,
        )
        node_states = torch.randn(2, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.90, 0.10, 0.05],
                    [0.20, 0.0, 0.80, 0.05],
                    [0.10, 0.30, 0.0, 0.70],
                    [0.60, 0.05, 0.05, 0.0],
                ],
                [
                    [0.0, 0.20, 0.85, 0.05],
                    [0.70, 0.0, 0.10, 0.10],
                    [0.05, 0.65, 0.0, 0.20],
                    [0.10, 0.10, 0.75, 0.0],
                ],
            ],
            dtype=torch.float32,
        )

        _fused, diag = fusion(node_states, adjacency)

        self.assertEqual(tuple(diag["path_context_importance"].shape), (2, 3))
        self.assertGreaterEqual(float(diag["path_context_importance"].detach().abs().mean()), 0.0)

    def test_path_target_mask_excludes_order_anchor_as_target(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            coverage_mode="group_pair_inclusive",
            coverage_dedup_mode="hard",
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.95, 0.94, 0.93],
                    [0.90, 0.0, 0.20, 0.10],
                    [0.89, 0.30, 0.0, 0.10],
                    [0.88, 0.20, 0.10, 0.0],
                ]
            ],
            dtype=torch.float32,
        )

        _fused, diag = fusion(
            node_states,
            adjacency,
            feature_group_ids=torch.arange(4),
            target_allowed_mask=torch.tensor([False, True, True, True]),
        )

        self.assertNotIn(0, diag["path_target"][0].tolist())

    def test_path_role_masks_exclude_order_anchor_from_all_path_nodes(self) -> None:
        fusion = ReliablePathFusion(
            hidden_dim=4,
            max_paths=4,
            use_reliability=True,
            use_path_fusion=True,
            use_multihop_paths=True,
            multihop_path_fraction=0.25,
        )
        node_states = torch.randn(1, 4, 4)
        adjacency = torch.tensor(
            [
                [
                    [0.0, 0.95, 0.94, 0.93],
                    [0.90, 0.0, 0.80, 0.70],
                    [0.89, 0.82, 0.0, 0.75],
                    [0.88, 0.78, 0.76, 0.0],
                ]
            ],
            dtype=torch.float32,
        )
        mask = torch.tensor([False, True, True, True])

        _fused, diag = fusion(
            node_states,
            adjacency,
            target_allowed_mask=mask,
            source_allowed_mask=mask,
            bridge_allowed_mask=mask,
        )

        self.assertNotIn(0, diag["path_target"][0].tolist())
        self.assertNotIn(0, diag["path_source"][0].tolist())
        self.assertNotIn(0, [value for value in diag["path_bridge"][0].tolist() if int(value) >= 0])

    def test_auto_path_budget_is_explicit(self) -> None:
        self.assertEqual(resolve_path_budget(4, 17, auto_path_budget=False), 4)
        self.assertEqual(resolve_path_budget(4, 17, auto_path_budget=True), 24)
        self.assertEqual(resolve_path_budget(32, 17, auto_path_budget=True), 32)

    def test_health_index_targets_use_capped_rul(self) -> None:
        task = ReadyTask(
            dataset="cmapss",
            target="degradation_stage_id",
            task="toy_health",
            x=pd.DataFrame({"record_id": ["a", "b", "c"], "sensor": [1.0, 2.0, 3.0]}),
            meta=pd.DataFrame({"rul": [200.0, 50.0, 0.0], "degradation_stage_id": [0, 1, 2]}),
            labels=np.asarray([0, 1, 2]),
            feature_cols=["sensor"],
            group_cols=[],
            order_col=None,
            ready_dir=Path("."),
        )

        targets = build_health_index_targets(task, rul_cap=100.0)

        self.assertIsNotNone(targets)
        self.assertTrue(np.allclose(targets, [0.0, 0.5, 1.0]))

        rul_targets = build_rul_targets(task)
        self.assertIsNotNone(rul_targets)
        self.assertTrue(np.allclose(rul_targets, [200.0, 50.0, 0.0]))

    def test_capped_rul_targets_match_direct_rul_head_scale(self) -> None:
        task = ReadyTask(
            dataset="cmapss",
            target="rul",
            task="toy_rul",
            x=pd.DataFrame({"record_id": ["a", "b", "c"], "sensor": [1.0, 2.0, 3.0]}),
            meta=pd.DataFrame({"rul": [200.0, 50.0, 0.0], "degradation_stage_id": [0, 1, 2]}),
            labels=np.asarray([0, 1, 2]),
            feature_cols=["sensor"],
            group_cols=[],
            order_col=None,
            ready_dir=Path("."),
        )

        targets = build_capped_rul_targets(task, rul_cap=100.0)
        restored = predict_rul_from_normalized(targets, rul_cap=100.0)

        self.assertIsNotNone(targets)
        self.assertTrue(np.allclose(targets, [1.0, 0.5, 0.0]))
        self.assertTrue(np.allclose(restored, [100.0, 50.0, 0.0]))

    def test_cmapss_terminal_rul_indices_select_last_cycle_per_test_unit(self) -> None:
        task = ReadyTask(
            dataset="cmapss",
            target="rul",
            task="toy_rul",
            x=pd.DataFrame({"record_id": [f"r{i}" for i in range(5)], "sensor": np.arange(5, dtype=float)}),
            meta=pd.DataFrame(
                {
                    "subset": ["FD001", "FD001", "FD001", "FD001", "FD002"],
                    "unit": [1, 1, 2, 2, 1],
                    "cycle": [1, 3, 2, 5, 4],
                    "rul": [10.0, 8.0, 9.0, 6.0, 7.0],
                    "degradation_stage_id": [0, 1, 0, 1, 1],
                }
            ),
            labels=np.asarray([0, 1, 0, 1, 1]),
            feature_cols=["sensor"],
            group_cols=[],
            order_col="cycle",
            ready_dir=Path("."),
        )

        selected = select_cmapss_terminal_rul_indices(task, np.arange(5, dtype=np.int64))

        self.assertEqual(selected.tolist(), [1, 3, 4])

    def test_rul_prediction_records_support_subset_metrics(self) -> None:
        meta = pd.DataFrame(
            {
                "record_id": ["a", "b", "c"],
                "subset": ["FD001", "FD001", "FD002"],
                "split_role": ["test", "test", "test"],
                "unit": [1, 2, 1],
                "cycle": [10, 20, 30],
            }
        )

        records = build_rul_prediction_records(
            meta,
            np.asarray([0, 1, 2], dtype=np.int64),
            np.asarray([100.0, 50.0, 30.0], dtype=np.float32),
            np.asarray([90.0, 55.0, 35.0], dtype=np.float32),
            prediction_source="direct_rul_head",
        )
        summary = summarize_rul_by_subset(records)

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["subset"], "FD001")
        self.assertEqual(records[0]["prediction_source"], "direct_rul_head")
        self.assertTrue(summary["enabled"])
        by_subset = {row["subset"]: row for row in summary["rows"]}
        self.assertEqual(by_subset["FD001"]["n_units"], 2)
        self.assertAlmostEqual(float(by_subset["FD002"]["rul_mae"]), 5.0)

    def test_rul_regression_metrics_report_original_task_scores(self) -> None:
        metrics = rul_regression_metrics(
            np.asarray([100.0, 50.0, 20.0], dtype=np.float32),
            np.asarray([90.0, 55.0, 20.0], dtype=np.float32),
        )

        self.assertIsNotNone(metrics)
        self.assertAlmostEqual(float(metrics["rul_mae"]), 5.0)
        self.assertAlmostEqual(float(metrics["rul_rmse"]), np.sqrt((100.0 + 25.0) / 3.0))
        self.assertGreater(float(metrics["rul_score"]), 0.0)

    def test_cmapss_rul_target_keeps_stage_labels_as_auxiliary_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "cmapss"
            root.mkdir(parents=True)
            pd.DataFrame(
                {
                    "record_id": ["r0", "r1", "r2"],
                    "subset_id": [1, 1, 1],
                    "unit": [1, 1, 2],
                    "cycle": [1, 2, 1],
                    "sensor_01": [10.0, 11.0, 12.0],
                }
            ).to_csv(root / "X_process_features.csv", index=False)
            pd.DataFrame(
                {
                    "record_id": ["r0", "r1", "r2"],
                    "subset": ["FD001", "FD001", "FD001"],
                    "split_role": ["train", "train", "test"],
                    "unit": [1, 1, 2],
                    "cycle": [1, 2, 1],
                    "rul": [125.0, 90.0, 80.0],
                    "degradation_stage_id": [0, 1, 1],
                }
            ).to_csv(root / "y_labels.csv", index=False)

            task = load_ready_task(Path(tmp), "cmapss", target="rul")

        self.assertEqual(task.target, "rul")
        self.assertEqual(task.task, "cmapss_original_rul_regression")
        self.assertTrue(np.array_equal(task.labels, np.asarray([0, 1, 1])))
        self.assertIn("cycle", task.feature_cols)

    def test_regime_prototype_residuals_use_train_only_healthy_baselines(self) -> None:
        labels = np.asarray([0, 1, 0, 1, 0, 1], dtype=np.int64)
        task = ReadyTask(
            dataset="cmapss",
            target="degradation_stage_id",
            task="toy_regime_residuals",
            x=pd.DataFrame(
                {
                    "record_id": [f"r{i}" for i in range(6)],
                    "op_setting_1": [0.0, 0.0, 1.0, 1.0, 0.0, 1.0],
                    "cycle": [1, 2, 1, 2, 3, 3],
                    "sensor_a": [10.0, 14.0, 100.0, 106.0, 12.0, 104.0],
                    "sensor_b": [20.0, 25.0, 200.0, 207.0, 23.0, 205.0],
                }
            ),
            meta=pd.DataFrame({"label": labels}),
            labels=labels,
            feature_cols=["op_setting_1", "cycle", "sensor_a", "sensor_b"],
            group_cols=[],
            order_col="cycle",
            ready_dir=Path("."),
        )

        residual_task, diag = apply_regime_prototype_residuals(
            task,
            train_idx=np.asarray([0, 1, 2, 3], dtype=np.int64),
            y_internal=labels,
            n_regimes=2,
            healthy_stage_max=0,
            seed=7,
        )

        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["n_residual_cols"], 2)
        self.assertEqual(diag["regime_cols"], ["op_setting_1"])
        self.assertTrue(np.allclose(residual_task.x["op_setting_1"], task.x["op_setting_1"]))
        self.assertTrue(np.allclose(residual_task.x["cycle"], task.x["cycle"]))
        self.assertTrue(np.allclose(residual_task.x["sensor_a"], [0.0, 4.0, 0.0, 6.0, 2.0, 4.0]))
        self.assertTrue(np.allclose(residual_task.x["sensor_b"], [0.0, 5.0, 0.0, 7.0, 3.0, 5.0]))

    def test_causal_windows_do_not_cross_run_boundaries(self) -> None:
        x = pd.DataFrame(
            {
                "record_id": [f"r{i}" for i in range(6)],
                "sensor_a": [1, 2, 3, 10, 11, 12],
                "sensor_b": [5, 6, 7, 15, 16, 17],
            }
        )
        meta = pd.DataFrame(
            {
                "run_id": ["a", "a", "a", "b", "b", "b"],
                "sample_index": [0, 1, 2, 0, 1, 2],
                "label": [0, 0, 1, 0, 1, 1],
            }
        )
        task = ReadyTask(
            dataset="toy",
            target="label",
            task="toy",
            x=x,
            meta=meta,
            labels=meta["label"].to_numpy(),
            feature_cols=["sensor_a", "sensor_b"],
            group_cols=["run_id"],
            order_col="sample_index",
            ready_dir=Path("."),
        )

        windows = build_causal_windows(task, window_size=3)

        self.assertEqual(tuple(windows.shape), (6, 3, 2))
        self.assertTrue(np.allclose(windows[3, :, 0], [10, 10, 10]))
        self.assertTrue(np.allclose(windows[2, :, 0], [1, 2, 3]))

    def test_cmapss_split_keeps_validation_units_disjoint(self) -> None:
        rows = []
        labels = []
        for unit in range(1, 7):
            for cycle in range(1, 10):
                rows.append({"split_role": "train", "subset": "FD001", "unit": unit, "cycle": cycle})
                labels.append((cycle - 1) // 3)
        for cycle in range(1, 10):
            rows.append({"split_role": "test", "subset": "FD001", "unit": 99, "cycle": cycle})
            labels.append((cycle - 1) // 3)
        meta = pd.DataFrame(rows)
        x = pd.DataFrame(
            {
                "record_id": [f"r{i}" for i in range(len(meta))],
                "cycle": meta["cycle"],
                "sensor_01": np.asarray(labels, dtype=float),
                "sensor_02": np.arange(len(meta), dtype=float),
            }
        )
        task = ReadyTask(
            dataset="cmapss",
            target="degradation_stage_id",
            task="cmapss",
            x=x,
            meta=meta,
            labels=np.asarray(labels, dtype=np.int64),
            feature_cols=["cycle", "sensor_01", "sensor_02"],
            group_cols=["subset", "split_role", "unit"],
            order_col="cycle",
            ready_dir=Path("."),
        )

        split = build_split(task, seed=3, val_fraction=0.25)

        train_units = set(meta.iloc[split.train_idx]["unit"].astype(int))
        val_units = set(meta.iloc[split.val_idx]["unit"].astype(int))
        test_units = set(meta.iloc[split.test_idx]["unit"].astype(int))
        self.assertTrue(split.split_protocol.startswith("official_test_grouped_unit_validation"))
        self.assertTrue(train_units.isdisjoint(val_units))
        self.assertEqual(test_units, {99})
        self.assertTrue(set(np.unique(split.y_internal[split.val_idx])).issubset({0, 1, 2}))

    def test_tep_split_uses_tail_block_per_source_file(self) -> None:
        rows = []
        labels = []
        for cls, source_file in enumerate(["d00.dat", "d01.dat"]):
            for sample_index in range(10):
                rows.append(
                    {
                        "split_role": "train",
                        "source_split": "train",
                        "source_file": source_file,
                        "sample_index": sample_index,
                    }
                )
                labels.append(cls)
        for cls, source_file in enumerate(["d00_te.dat", "d01_te.dat"]):
            for sample_index in range(4):
                rows.append(
                    {
                        "split_role": "test",
                        "source_split": "test",
                        "source_file": source_file,
                        "sample_index": sample_index,
                    }
                )
                labels.append(cls)
        meta = pd.DataFrame(rows)
        x = pd.DataFrame(
            {
                "record_id": [f"r{i}" for i in range(len(meta))],
                "xmeas_01": np.arange(len(meta), dtype=float),
                "xmeas_02": np.asarray(labels, dtype=float),
            }
        )
        task = ReadyTask(
            dataset="tep",
            target="event_quality_class_id",
            task="tep",
            x=x,
            meta=meta,
            labels=np.asarray(labels, dtype=np.int64),
            feature_cols=["xmeas_01", "xmeas_02"],
            group_cols=["source_split", "source_file"],
            order_col="sample_index",
            ready_dir=Path("."),
        )

        split = build_split(task, seed=5, val_fraction=0.20)

        self.assertTrue(split.split_protocol.startswith("official_test_blocked_source_validation"))
        train_meta = meta.iloc[split.train_idx]
        val_meta = meta.iloc[split.val_idx]
        self.assertEqual(set(val_meta["sample_index"].astype(int)), {8, 9})
        self.assertEqual(set(train_meta["sample_index"].astype(int)), set(range(8)))
        self.assertEqual(set(np.unique(split.y_internal[split.val_idx])), {0, 1})

    def test_train_group_salience_uses_train_labels(self) -> None:
        x = pd.DataFrame(
            {
                "record_id": [f"r{i}" for i in range(8)],
                "FS1_mean": [0, 0, 1, 1, 5, 5, 6, 6],
                "FS1_std": [0, 0, 1, 1, 5, 5, 6, 6],
                "TS1_mean": [1, 2, 1, 2, 1, 2, 1, 2],
            }
        )
        labels = np.asarray([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int64)
        task = ReadyTask(
            dataset="toy",
            target="label",
            task="toy",
            x=x,
            meta=pd.DataFrame({"label": labels}),
            labels=labels,
            feature_cols=["FS1_mean", "FS1_std", "TS1_mean"],
            group_cols=[],
            order_col=None,
            ready_dir=Path("."),
        )
        groups = infer_feature_group_ids(task.feature_cols)

        salience, diag = compute_train_group_salience(task, np.arange(8), labels, groups)

        self.assertTrue(diag["enabled"])
        self.assertGreater(float(salience[0]), float(salience[2]))
        self.assertEqual(float(salience[0]), float(salience[1]))

    def test_lifecycle_salience_builds_train_only_path_evidence(self) -> None:
        cycles = np.asarray([1, 2, 3, 4, 5, 6, 1, 2, 3, 4], dtype=float)
        labels = np.asarray([0, 0, 1, 1, 2, 2, 0, 0, 1, 1], dtype=np.int64)
        x = pd.DataFrame(
            {
                "record_id": [f"r{i}" for i in range(len(cycles))],
                "cycle": cycles,
                "sensor_drift": cycles * 2.0,
                "sensor_noise": [1, 2, 1, 2, 1, 2, 2, 1, 2, 1],
            }
        )
        task = ReadyTask(
            dataset="cmapss",
            target="degradation_stage_id",
            task="cmapss",
            x=x,
            meta=pd.DataFrame({"cycle": cycles, "label": labels}),
            labels=labels,
            feature_cols=["cycle", "sensor_drift", "sensor_noise"],
            group_cols=[],
            order_col="cycle",
            ready_dir=Path("."),
        )
        groups = infer_feature_group_ids(task.feature_cols)

        salience, diag = compute_train_group_salience(
            task,
            np.arange(8),
            labels,
            groups,
            mode="class_lifecycle",
            lifecycle_weight=0.5,
        )

        self.assertEqual(diag["mode"], "class_lifecycle")
        self.assertTrue(diag["lifecycle_enabled"])
        self.assertGreater(float(salience[1]), float(salience[2]))
        self.assertEqual(tuple(diag["path_evidence_matrix"].shape), (3, 3))
        self.assertGreater(float(diag["path_evidence_mean"]), 0.0)

    def test_stable_path_evidence_keeps_cross_split_edges(self) -> None:
        rng = np.random.default_rng(17)
        labels = np.asarray([0, 1] * 24, dtype=np.int64)
        x = rng.normal(scale=0.05, size=(len(labels), 5, 4)).astype(np.float32)
        x[:, :, 0] += labels[:, None] * 2.0
        x[:, :, 1] += labels[:, None] * 1.5
        x[:6, :, 2] += labels[:6, None] * 4.0
        groups = np.arange(4, dtype=np.int64)

        evidence, diag = compute_train_stable_path_evidence(
            x,
            labels,
            groups,
            n_classes=2,
            split_count=4,
            min_vote_fraction=0.75,
            top_k=2,
            mode="static_lag",
            max_lag=2,
            lag_weight=0.25,
        )

        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["used_splits"], 4)
        self.assertEqual(tuple(evidence.shape), (4, 4))
        self.assertGreater(float(evidence[0, 1]), 0.0)
        self.assertGreater(float(evidence[0, 1]), float(evidence[0, 3]))
        self.assertGreater(float(diag["density"]), 0.0)

    def test_ordinal_emd_loss_penalizes_far_stage_errors_more(self) -> None:
        target = torch.tensor([1], dtype=torch.long)
        near_logits = torch.tensor([[0.1, 3.0, 2.0, -1.0]], dtype=torch.float32)
        far_logits = torch.tensor([[3.0, -1.0, -1.0, 3.0]], dtype=torch.float32)

        near = ordinal_emd_loss(near_logits, target)
        far = ordinal_emd_loss(far_logits, target)

        self.assertGreater(float(far), float(near))

    def test_ordinal_boundary_loss_penalizes_boundary_crossing_errors(self) -> None:
        target = torch.tensor([2], dtype=torch.long)
        near_logits = torch.tensor([[-1.0, 0.5, 2.5, 1.5]], dtype=torch.float32)
        far_logits = torch.tensor([[2.5, 1.5, -0.5, -1.0]], dtype=torch.float32)

        near = ordinal_boundary_bce_loss(near_logits, target, boundary_focus=0.5)
        far = ordinal_boundary_bce_loss(far_logits, target, boundary_focus=0.5)

        self.assertGreater(float(far), float(near))

    def test_supervised_focal_loss_supports_label_smoothing_and_backward(self) -> None:
        logits = torch.tensor(
            [[2.0, -0.5, 0.1], [-0.2, 0.4, 1.8]],
            dtype=torch.float32,
            requires_grad=True,
        )
        target = torch.tensor([0, 2], dtype=torch.long)
        weights = torch.tensor([1.0, 1.2, 0.8], dtype=torch.float32)

        loss = supervised_classification_loss(
            logits,
            target,
            class_weights=weights,
            focal_gamma=1.5,
            label_smoothing=0.05,
        )
        loss.backward()

        self.assertTrue(torch.isfinite(loss).item())
        self.assertIsNotNone(logits.grad)
        assert logits.grad is not None
        self.assertEqual(tuple(logits.grad.shape), tuple(logits.shape))

    def test_prototype_posterior_fusion_accepts_validation_gain(self) -> None:
        x_train = np.array(
            [
                [[0.0, 0.1], [0.0, 0.0], [0.1, 0.0]],
                [[0.1, 0.0], [0.0, 0.1], [0.0, 0.0]],
                [[4.9, 5.0], [5.0, 5.1], [5.1, 5.0]],
                [[5.0, 4.9], [5.1, 5.0], [5.0, 5.1]],
            ],
            dtype=np.float32,
        )
        y_train = np.array([0, 0, 1, 1], dtype=np.int64)
        x_val = np.array(
            [
                [[0.0, 0.0], [0.1, 0.0], [0.0, 0.1]],
                [[5.0, 5.0], [5.1, 5.0], [5.0, 5.1]],
            ],
            dtype=np.float32,
        )
        y_val = np.array([0, 1], dtype=np.int64)
        x_test = np.array([[[5.1, 5.0], [5.0, 5.0], [5.0, 5.1]]], dtype=np.float32)
        base_val = np.array([[0.55, 0.45], [0.55, 0.45]], dtype=np.float64)
        base_test = np.array([[0.55, 0.45]], dtype=np.float64)

        fused_val, fused_test, diag = apply_prototype_posterior_fusion(
            x_train,
            y_train,
            x_val,
            y_val,
            x_test,
            base_val,
            base_test,
            n_classes=2,
            max_blend=1.0,
            blend_steps=3,
            temperature_grid=[0.25, 1.0],
        )

        self.assertTrue(diag["accepted"])
        self.assertGreater(diag["selected_blend"], 0.0)
        self.assertGreater(diag["selected_val_macro_f1"], diag["base_val_macro_f1"])
        self.assertEqual(int(np.argmax(fused_val[1])), 1)
        self.assertEqual(int(np.argmax(fused_test[0])), 1)

    def test_one_class_posterior_fusion_accepts_normality_gain(self) -> None:
        x_train = np.array(
            [
                [[0.0, 0.0], [0.1, 0.0], [0.0, 0.1]],
                [[0.1, 0.0], [0.0, 0.1], [0.1, 0.0]],
                [[4.0, 4.1], [4.2, 4.0], [4.1, 4.2]],
                [[5.0, 4.8], [5.1, 4.9], [5.2, 5.0]],
            ],
            dtype=np.float32,
        )
        y_train = np.array([0, 0, 1, 1], dtype=np.int64)
        x_val = np.array(
            [
                [[0.0, 0.1], [0.1, 0.0], [0.0, 0.0]],
                [[5.1, 5.0], [5.0, 5.1], [5.2, 5.0]],
            ],
            dtype=np.float32,
        )
        y_val = np.array([0, 1], dtype=np.int64)
        x_test = np.array([[[5.0, 4.9], [5.2, 5.1], [5.1, 5.0]]], dtype=np.float32)
        base_val = np.array([[0.55, 0.45], [0.55, 0.45]], dtype=np.float64)
        base_test = np.array([[0.55, 0.45]], dtype=np.float64)

        fused_val, fused_test, diag = apply_one_class_posterior_fusion(
            x_train,
            y_train,
            x_val,
            y_val,
            x_test,
            base_val,
            base_test,
            n_classes=2,
            max_blend=1.0,
            blend_steps=3,
            temperature_grid=[0.25, 1.0],
            threshold_grid=[0.0, 1.0],
        )

        self.assertTrue(diag["accepted"])
        self.assertGreater(diag["selected_blend"], 0.0)
        self.assertGreater(diag["selected_val_macro_f1"], diag["base_val_macro_f1"])
        self.assertEqual(int(np.argmax(fused_val[1])), 1)
        self.assertEqual(int(np.argmax(fused_test[0])), 1)

    def test_ordinal_threshold_posterior_calibration_accepts_stage_boundary_gain(self) -> None:
        y_val = np.array([0, 1, 2], dtype=np.int64)
        base_val = np.array(
            [
                [0.49, 0.50, 0.01],
                [0.20, 0.60, 0.20],
                [0.01, 0.50, 0.49],
            ],
            dtype=np.float64,
        )
        base_test = np.array([[0.01, 0.50, 0.49]], dtype=np.float64)

        fused_val, fused_test, diag = apply_ordinal_threshold_posterior_calibration(
            y_val,
            base_val,
            base_test,
            n_classes=3,
            max_blend=1.0,
            blend_steps=3,
            smoothing=0.01,
        )

        self.assertTrue(diag["accepted"])
        self.assertGreater(diag["selected_blend"], 0.0)
        self.assertGreater(diag["selected_val_macro_f1"], diag["base_val_macro_f1"])
        self.assertEqual(int(np.argmax(fused_val[0])), 0)
        self.assertEqual(int(np.argmax(fused_test[0])), 2)

    def test_knowledge_prior_group_expansion_covers_stat_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ready_dir = Path(tmp)
            graph_dir = ready_dir / "knowledge_model"
            graph_dir.mkdir(parents=True)
            (graph_dir / "knowledge_graph.json").write_text(
                json.dumps(
                    {
                        "edges": [
                            {
                                "source": "FS1_mean",
                                "target": "PS1_mean",
                                "reliability": 0.50,
                                "evidence_source": "component_physics_prior",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            task = ReadyTask(
                dataset="toy",
                target="label",
                task="toy",
                x=pd.DataFrame(),
                meta=pd.DataFrame(),
                labels=np.asarray([], dtype=np.int64),
                feature_cols=["FS1_mean", "FS1_std", "PS1_mean", "PS1_std"],
                group_cols=[],
                order_col=None,
                ready_dir=ready_dir,
            )

            exact_prior, exact_diag = load_knowledge_graph_prior(task, mode="expert")
            expanded_prior, expanded_diag = load_knowledge_graph_prior(
                task,
                mode="expert",
                group_expansion=True,
                group_expansion_strength=0.5,
            )

        self.assertEqual(exact_diag["matched_edges"], 1)
        self.assertEqual(exact_diag["expanded_edges"], 0)
        self.assertAlmostEqual(float(exact_prior[2, 0]), 0.50)
        self.assertAlmostEqual(float(exact_prior[3, 1]), 0.0)
        self.assertGreater(expanded_diag["expanded_edges"], 0)
        self.assertAlmostEqual(float(expanded_prior[2, 0]), 0.50)
        self.assertAlmostEqual(float(expanded_prior[3, 1]), 0.25)

    def test_knowledge_prior_exports_expert_and_llm_family_priors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ready_dir = Path(tmp)
            graph_dir = ready_dir / "knowledge_model"
            graph_dir.mkdir(parents=True)
            (graph_dir / "knowledge_graph.json").write_text(
                json.dumps(
                    {
                        "edges": [
                            {
                                "source": "sensor_a",
                                "target": "sensor_b",
                                "reliability": 0.80,
                                "evidence_source": "domain_expert_prior",
                            },
                            {
                                "source": "sensor_c",
                                "target": "sensor_b",
                                "reliability": 0.60,
                                "evidence_source": "llm_semantic_prior",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            task = ReadyTask(
                dataset="toy",
                target="label",
                task="toy",
                x=pd.DataFrame(),
                meta=pd.DataFrame(),
                labels=np.asarray([], dtype=np.int64),
                feature_cols=["sensor_a", "sensor_b", "sensor_c"],
                group_cols=[],
                order_col=None,
                ready_dir=ready_dir,
            )

            prior, diag = load_knowledge_graph_prior(task, mode="expert_llm")

        self.assertIsNotNone(prior)
        self.assertEqual(diag["source_family_counts"], {"expert": 1, "llm": 1})
        self.assertEqual(diag["_external_family_prior_names"], ["expert", "llm"])
        family_priors = diag["_external_family_prior_matrices"]
        self.assertEqual(tuple(family_priors.shape), (2, 3, 3))
        self.assertGreater(float(family_priors[0, 1, 0]), 0.0)
        self.assertGreater(float(family_priors[1, 1, 2]), 0.0)

    def test_llm_expert_graph_dynamic_corrections_adjust_loaded_prior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ready_dir = Path(tmp)
            graph_dir = ready_dir / "knowledge_model"
            graph_dir.mkdir(parents=True)
            (graph_dir / "knowledge_graph.json").write_text(
                json.dumps(
                    {
                        "edges": [
                            {
                                "edge_id": "expert_down",
                                "source": "sensor_a",
                                "target": "sensor_b",
                                "reliability": 0.80,
                                "evidence_source": "domain_expert_prior",
                            },
                            {
                                "edge_id": "expert_remove",
                                "source": "sensor_c",
                                "target": "sensor_b",
                                "reliability": 0.70,
                                "evidence_source": "domain_expert_prior",
                            },
                            {
                                "source": "sensor_a",
                                "target": "sensor_c",
                                "reliability": 0.30,
                                "evidence_source": "llm_expert_graph_dynamic_correction",
                                "correction_operation": "revise",
                                "corrects_edge_id": "expert_down",
                            },
                        ],
                        "llm_expert_graph_correction_metadata": {
                            "llm_expert_graph_dynamic_correction": {
                                "metadata_only_corrections": [
                                    {
                                        "source": "sensor_c",
                                        "target": "sensor_b",
                                        "reliability": 0.10,
                                        "evidence_source": "llm_expert_graph_dynamic_correction",
                                        "correction_operation": "remove",
                                        "corrects_edge_id": "expert_remove",
                                    }
                                ]
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            task = ReadyTask(
                dataset="toy",
                target="label",
                task="toy",
                x=pd.DataFrame(),
                meta=pd.DataFrame(),
                labels=np.asarray([], dtype=np.int64),
                feature_cols=["sensor_a", "sensor_b", "sensor_c"],
                group_cols=[],
                order_col=None,
                ready_dir=ready_dir,
            )

            prior, diag = load_knowledge_graph_prior(task, mode="expert_llm")

        self.assertIsNotNone(prior)
        self.assertAlmostEqual(float(prior[1, 0]), 0.30)
        self.assertAlmostEqual(float(prior[1, 2]), 0.0)
        self.assertAlmostEqual(float(prior[2, 0]), 0.30)
        correction_diag = diag["llm_expert_graph_dynamic_corrections"]
        self.assertTrue(correction_diag["enabled"])
        self.assertEqual(correction_diag["n_actionable_corrections"], 2)
        self.assertEqual(correction_diag["applied"]["revise"], 1)
        self.assertEqual(correction_diag["applied"]["remove"], 1)

    def test_llm_condition_verifier_metadata_loads_without_graph_prior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ready_dir = Path(tmp)
            graph_dir = ready_dir / "knowledge_model"
            graph_dir.mkdir(parents=True)
            (graph_dir / "knowledge_graph.json").write_text(
                json.dumps(
                    {
                        "edges": [
                            {
                                "edge_id": "expert_ab",
                                "source": "sensor_a",
                                "target": "sensor_b",
                                "reliability": 0.80,
                                "evidence_source": "domain_expert_prior",
                            }
                        ],
                        "llm_expert_condition_verifier_metadata": {
                            "llm_expert_condition_verifier": {
                                "condition_verifications": [
                                    {
                                        "expert_edge_id": "expert_ab",
                                        "source": "sensor_a",
                                        "target": "sensor_b",
                                        "condition_activation": "activate",
                                        "reliability": 0.60,
                                    }
                                ]
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            task = ReadyTask(
                dataset="toy",
                target="label",
                task="toy",
                x=pd.DataFrame(),
                meta=pd.DataFrame(),
                labels=np.asarray([], dtype=np.int64),
                feature_cols=["sensor_a", "sensor_b"],
                group_cols=[],
                order_col=None,
                ready_dir=ready_dir,
            )

            prior, diag = load_knowledge_graph_prior(task, mode="none")

        self.assertIsNone(prior)
        self.assertFalse(diag["enabled"])
        self.assertEqual(diag["status"], "metadata_only")
        self.assertEqual(diag["matched_edges"], 0)
        verifier_diag = diag["llm_expert_condition_verifier"]
        self.assertTrue(verifier_diag["enabled"])
        self.assertEqual(verifier_diag["n_actionable_verifications"], 1)
        self.assertEqual(verifier_diag["matched"]["activate"], 1)
        activate = diag["_llm_expert_condition_activate_matrix"]
        suppress = diag["_llm_expert_condition_suppress_matrix"]
        self.assertAlmostEqual(float(activate[1, 0]), 1.0)
        self.assertAlmostEqual(float(suppress[1, 0]), 0.0)

    def test_llm_condition_verifier_candidate_gate_creates_supported_expert_overlay(self) -> None:
        adjusted, diag = apply_llm_expert_condition_verifier_to_candidate_prior(
            None,
            condition_activate_matrix=None,
            condition_suppress_matrix=None,
            condition_records=[
                {
                    "expert_edge_id": "expert_ab",
                    "source": "sensor_a",
                    "target": "sensor_b",
                    "condition_activation": "activate",
                    "reliability": 0.80,
                    "class_scope": "all",
                }
            ],
            data_support_matrix=np.asarray(
                [
                    [0.0, 0.0],
                    [0.70, 0.0],
                ],
                dtype=np.float32,
            ),
            feature_cols=["sensor_a", "sensor_b"],
            class_labels=[0, 1],
            weight=0.50,
            min_data_support=0.05,
            floor=0.10,
        )

        self.assertTrue(diag["enabled"])
        self.assertTrue(diag["created_from_verifier"])
        self.assertEqual(diag["verified_expert_candidate_edges"], 1)
        self.assertGreater(float(adjusted[1, 0]), 0.0)
        self.assertAlmostEqual(float(adjusted[0, 1]), 0.0, places=6)

    def test_llm_condition_verifier_candidate_gate_rejects_unsupported_expert_overlay(self) -> None:
        adjusted, diag = apply_llm_expert_condition_verifier_to_candidate_prior(
            None,
            condition_activate_matrix=None,
            condition_suppress_matrix=None,
            condition_records=[
                {
                    "expert_edge_id": "expert_ab",
                    "source": "sensor_a",
                    "target": "sensor_b",
                    "condition_activation": "activate",
                    "reliability": 0.80,
                    "class_scope": "all",
                }
            ],
            data_support_matrix=np.zeros((2, 2), dtype=np.float32),
            feature_cols=["sensor_a", "sensor_b"],
            class_labels=[0, 1],
            weight=0.50,
            min_data_support=0.05,
            floor=0.10,
        )

        self.assertIsNone(adjusted)
        self.assertFalse(diag["enabled"])
        self.assertEqual(diag["status"], "no_data_supported_verified_expert_or_candidate_overlap")

    def test_validation_gain_admission_decision_accepts_only_nonnegative_gain(self) -> None:
        accepted = validation_gain_admission_decision(
            candidate_metric=0.81,
            baseline_metric=0.80,
            min_gain=0.0,
        )
        rejected = validation_gain_admission_decision(
            candidate_metric=0.79,
            baseline_metric=0.80,
            min_gain=0.0,
        )

        self.assertTrue(accepted["admitted"])
        self.assertEqual(accepted["selected"], "candidate")
        self.assertFalse(rejected["admitted"])
        self.assertEqual(rejected["selected"], "baseline")
        self.assertLess(rejected["validation_gain"], 0.0)

    def test_external_family_calibration_filters_and_scales_candidate_edges(self) -> None:
        algorithmic = np.zeros((4, 4), dtype=np.float32)
        algorithmic[1, 0] = 0.80
        algorithmic[2, 0] = 0.70
        families = np.zeros((2, 4, 4), dtype=np.float32)
        families[0, 1, 0] = 0.90
        families[0, 3, 2] = 0.90
        families[1, 2, 0] = 0.80

        calibrated, names, diag = _calibrate_external_edge_family_priors(
            families,
            ["expert", "llm"],
            algorithmic,
            floor=0.10,
            min_support=0.20,
        )
        candidate, candidate_diag = _aggregate_external_candidate_prior(
            calibrated,
            names,
            expert_scale=1.0,
            llm_scale=0.40,
            default_scale=0.85,
        )

        self.assertTrue(diag["enabled"])
        self.assertEqual(diag["family_edges"]["expert"], 1)
        self.assertEqual(diag["family_edges"]["llm"], 1)
        self.assertAlmostEqual(float(diag["family_retained_fraction"]["expert"]), 0.5)
        self.assertTrue(candidate_diag["enabled"])
        assert candidate is not None
        self.assertAlmostEqual(float(candidate[1, 0]), 1.0, places=6)
        self.assertAlmostEqual(float(candidate[2, 0]), 0.40, places=6)
        self.assertAlmostEqual(float(candidate[3, 2]), 0.0, places=6)

    def test_tiny_training_run_produces_metrics(self) -> None:
        rng = np.random.default_rng(7)
        rows = 30
        labels = np.asarray([0, 1, 2] * 10, dtype=np.int64)
        x = pd.DataFrame(
            {
                "record_id": [f"toy_{i}" for i in range(rows)],
                "run_id": ["r0"] * 15 + ["r1"] * 15,
                "sample_index": list(range(15)) * 2,
                "sensor_a": rng.normal(size=rows) + labels,
                "sensor_b": rng.normal(size=rows) - labels,
                "sensor_c": rng.normal(size=rows),
            }
        )
        meta = pd.DataFrame(
            {
                "run_id": x["run_id"],
                "sample_index": x["sample_index"],
                "label": labels,
            }
        )
        task = ReadyTask(
            dataset="toy",
            target="label",
            task="toy_multiclass",
            x=x,
            meta=meta,
            labels=labels,
            feature_cols=["sensor_a", "sensor_b", "sensor_c"],
            group_cols=[],
            order_col="sample_index",
            ready_dir=Path("."),
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_ready_task(
                task,
                output_dir=Path(tmp),
                variant="full",
                seed=11,
                window_size=4,
                hidden_dim=8,
                epochs=1,
                batch_size=8,
                learning_rate=0.001,
                max_rows_per_split=12,
                forecast_weight=0.0,
                graph_weight=0.0,
                focal_loss_gamma=0.0,
                label_smoothing=0.0,
                ordinal_loss_weight=0.0,
                path_entropy_weight=0.0,
                graph_top_k=2,
                max_paths=4,
                evidence_prior_mode="none",
                prior_strength=0.0,
                prior_min_reliability=0.0,
                algorithmic_edge_prior_mode="hybrid",
                algorithmic_edge_prior_top_k=1,
                algorithmic_edge_prior_max_lag=1,
                algorithmic_edge_prior_strength=0.05,
                dropout=0.0,
                use_task_salience=True,
                salience_selection_strength=0.0,
                use_stable_path_evidence=True,
                stable_path_evidence_splits=2,
                stable_path_evidence_min_vote_fraction=0.50,
                stable_path_evidence_top_k=2,
                stable_path_evidence_max_lag=1,
            )

        self.assertEqual(result["status"], "ok")
        self.assertIn("macro_f1", result["test_metrics"])
        self.assertGreater(result["efficiency"]["parameters"], 0)
        self.assertEqual(result["path_budget"]["requested_max_paths"], 4)
        self.assertEqual(result["path_budget"]["actual_max_paths"], 4)
        self.assertTrue(result["task_salience"]["enabled"])
        self.assertTrue(result["stable_path_evidence"]["enabled"])
        self.assertTrue(result["path_budget"]["use_stable_path_evidence"])
        self.assertTrue(result["algorithmic_edge_prior"]["enabled"])
        self.assertEqual(result["path_budget"]["algorithmic_edge_prior_mode"], "hybrid")
        self.assertAlmostEqual(float(result["diagnostics"]["config"]["prior_strength"]), 0.05)

        with tempfile.TemporaryDirectory() as tmp:
            candidate_only = run_ready_task(
                task,
                output_dir=Path(tmp),
                variant="full",
                seed=12,
                window_size=4,
                hidden_dim=8,
                epochs=1,
                batch_size=8,
                learning_rate=0.001,
                max_rows_per_split=12,
                forecast_weight=0.0,
                graph_weight=0.0,
                focal_loss_gamma=0.0,
                label_smoothing=0.0,
                ordinal_loss_weight=0.0,
                path_entropy_weight=0.0,
                graph_top_k=2,
                max_paths=4,
                evidence_prior_mode="none",
                prior_strength=0.0,
                prior_min_reliability=0.0,
                algorithmic_edge_prior_mode="hybrid",
                algorithmic_edge_prior_top_k=1,
                algorithmic_edge_prior_max_lag=1,
                algorithmic_edge_prior_strength=0.05,
                algorithmic_edge_prior_candidate_only=True,
                dropout=0.0,
            )

        self.assertEqual(candidate_only["status"], "ok")
        self.assertTrue(candidate_only["algorithmic_edge_prior"]["enabled"])
        self.assertTrue(candidate_only["path_budget"]["algorithmic_edge_prior_candidate_only"])
        self.assertTrue(candidate_only["evidence_prior"]["algorithmic_candidate_only"])
        self.assertEqual(candidate_only["prior_algorithmic_combination"]["mode"], "candidate_only")
        self.assertAlmostEqual(float(candidate_only["diagnostics"]["config"]["prior_strength"]), 0.0)

        with tempfile.TemporaryDirectory() as tmp:
            ready_dir = Path(tmp) / "ready"
            graph_dir = ready_dir / "knowledge_model"
            graph_dir.mkdir(parents=True)
            (graph_dir / "knowledge_graph.json").write_text(
                json.dumps(
                    {
                        "edges": [
                            {
                                "source": "sensor_a",
                                "target": "sensor_b",
                                "reliability": 0.80,
                                "evidence_source": "domain_expert_prior",
                            },
                            {
                                "source": "sensor_c",
                                "target": "sensor_b",
                                "reliability": 0.70,
                                "evidence_source": "llm_semantic_prior",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            task_with_prior = ReadyTask(
                dataset="toy",
                target="label",
                task="toy_multiclass",
                x=x,
                meta=meta,
                labels=labels,
                feature_cols=["sensor_a", "sensor_b", "sensor_c"],
                group_cols=[],
                order_col="sample_index",
                ready_dir=ready_dir,
            )
            external_candidate = run_ready_task(
                task_with_prior,
                output_dir=Path(tmp) / "out",
                variant="full",
                seed=13,
                window_size=4,
                hidden_dim=8,
                epochs=1,
                batch_size=8,
                learning_rate=0.001,
                max_rows_per_split=12,
                forecast_weight=0.0,
                graph_weight=0.0,
                focal_loss_gamma=0.0,
                label_smoothing=0.0,
                ordinal_loss_weight=0.0,
                path_entropy_weight=0.0,
                graph_top_k=2,
                max_paths=4,
                evidence_prior_mode="expert_llm",
                prior_strength=0.0,
                prior_min_reliability=0.0,
                algorithmic_edge_prior_mode="hybrid",
                algorithmic_edge_prior_top_k=1,
                algorithmic_edge_prior_max_lag=1,
                algorithmic_edge_prior_strength=0.05,
                external_edge_candidate_only=True,
                external_candidate_families="llm",
                external_candidate_llm_scale=0.40,
                use_candidate_prior_admission=True,
                candidate_prior_admission_target="proposal_feature",
                candidate_coverage_fraction=0.25,
                dropout=0.0,
            )

        self.assertEqual(external_candidate["status"], "ok")
        self.assertTrue(external_candidate["evidence_prior"]["external_edge_candidate_only"])
        self.assertEqual(external_candidate["evidence_prior"]["external_family_split"]["candidate_family_names"], ["llm"])
        self.assertGreater(int(external_candidate["evidence_prior"]["external_core_edge_count"]), 0)
        self.assertTrue(external_candidate["evidence_prior"]["external_path_candidate_merge"]["enabled"])
        self.assertEqual(external_candidate["prior_algorithmic_combination"]["mode"], "external_candidate_only")
        self.assertTrue(external_candidate["diagnostics"]["config"]["path_candidate_prior_enabled"])
        self.assertAlmostEqual(float(external_candidate["diagnostics"]["config"]["prior_strength"]), 0.05)


if __name__ == "__main__":
    unittest.main()
