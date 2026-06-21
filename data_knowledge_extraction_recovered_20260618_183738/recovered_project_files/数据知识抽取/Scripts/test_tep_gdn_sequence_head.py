from __future__ import annotations

import unittest

import numpy as np
import torch

from tep_sequence_heads import _build_sequence_module, train_sequence_model


class TepGDNSequenceHeadTest(unittest.TestCase):
    def test_gdn_sequence_module_outputs_class_logits(self) -> None:
        model = _build_sequence_module("gdn", n_features=4, n_classes=3, hidden_dim=8)

        logits = model(torch.randn(2, 6, 4))

        self.assertEqual(tuple(logits.shape), (2, 3))
        self.assertEqual(getattr(model, "model_family"), "gdn_style_sequence_graph")

    def test_mtad_gat_sequence_module_outputs_class_logits(self) -> None:
        model = _build_sequence_module("mtad_gat", n_features=5, n_classes=4, hidden_dim=8)

        logits = model(torch.randn(3, 7, 5))

        self.assertEqual(tuple(logits.shape), (3, 4))
        self.assertEqual(getattr(model, "model_family"), "mtad_gat_style_temporal_feature_attention")

    def test_patchtst_sequence_module_outputs_class_logits(self) -> None:
        model = _build_sequence_module("patchtst", n_features=6, n_classes=4, hidden_dim=16)

        logits = model(torch.randn(3, 10, 6))

        self.assertEqual(tuple(logits.shape), (3, 4))
        self.assertEqual(getattr(model, "model_family"), "patchtst_style_channel_independent_patch_transformer")

    def test_anomaly_transformer_sequence_module_outputs_class_logits(self) -> None:
        model = _build_sequence_module("anomaly_transformer", n_features=6, n_classes=4, hidden_dim=16)

        logits = model(torch.randn(3, 10, 6))

        self.assertEqual(tuple(logits.shape), (3, 4))
        self.assertEqual(getattr(model, "model_family"), "anomaly_transformer_style_association_discrepancy")

    def test_graph_wavenet_sequence_module_outputs_class_logits(self) -> None:
        model = _build_sequence_module("graph_wavenet", n_features=5, n_classes=4, hidden_dim=16)

        logits = model(torch.randn(3, 10, 5))

        self.assertEqual(tuple(logits.shape), (3, 4))
        self.assertEqual(getattr(model, "model_family"), "graph_wavenet_style_adaptive_dilated_graph_temporal")
        self.assertEqual(getattr(model, "graph_wavenet_adaptive_adjacency_shape"), [5, 5])

    def test_train_sequence_model_accepts_gdn_and_reports_graph_diagnostics(self) -> None:
        rng = np.random.default_rng(23)
        x_train = rng.normal(size=(12, 5, 4)).astype(np.float32)
        y_train = np.asarray([0, 1, 2] * 4, dtype=np.int64)
        x_val = rng.normal(size=(4, 5, 4)).astype(np.float32)
        x_test = rng.normal(size=(5, 5, 4)).astype(np.float32)

        val_proba, test_proba, diagnostics = train_sequence_model(
            x_train,
            y_train,
            x_val,
            x_test,
            model_name="gdn",
            n_classes=3,
            hidden_dim=8,
            epochs=1,
            batch_size=4,
            seed=23,
        )

        self.assertEqual(val_proba.shape, (4, 3))
        self.assertEqual(test_proba.shape, (5, 3))
        self.assertEqual(diagnostics["model_family"], "gdn_style_sequence_graph")
        self.assertEqual(diagnostics["gdn_adjacency_shape"], [4, 4])
        self.assertGreaterEqual(diagnostics["gdn_top_k"], 1)
        self.assertGreater(diagnostics["parameters"], 0)
        self.assertGreater(diagnostics["train_seconds"], 0.0)
        self.assertGreater(diagnostics["train_samples_per_second"], 0.0)
        self.assertGreater(diagnostics["test_inference_seconds"], 0.0)
        self.assertGreater(diagnostics["test_inference_samples_per_second"], 0.0)

    def test_train_sequence_model_accepts_patchtst_and_reports_family(self) -> None:
        rng = np.random.default_rng(24)
        x_train = rng.normal(size=(10, 9, 5)).astype(np.float32)
        y_train = np.asarray([0, 1] * 5, dtype=np.int64)
        x_val = rng.normal(size=(4, 9, 5)).astype(np.float32)
        x_test = rng.normal(size=(3, 9, 5)).astype(np.float32)

        val_proba, test_proba, diagnostics = train_sequence_model(
            x_train,
            y_train,
            x_val,
            x_test,
            model_name="patchtst",
            n_classes=2,
            hidden_dim=16,
            epochs=1,
            batch_size=4,
            seed=24,
        )

        self.assertEqual(val_proba.shape, (4, 2))
        self.assertEqual(test_proba.shape, (3, 2))
        self.assertEqual(diagnostics["model_family"], "patchtst_style_channel_independent_patch_transformer")
        self.assertGreater(diagnostics["parameters"], 0)

    def test_train_sequence_model_accepts_anomaly_transformer_and_reports_family(self) -> None:
        rng = np.random.default_rng(25)
        x_train = rng.normal(size=(10, 9, 5)).astype(np.float32)
        y_train = np.asarray([0, 1] * 5, dtype=np.int64)
        x_val = rng.normal(size=(4, 9, 5)).astype(np.float32)
        x_test = rng.normal(size=(3, 9, 5)).astype(np.float32)

        val_proba, test_proba, diagnostics = train_sequence_model(
            x_train,
            y_train,
            x_val,
            x_test,
            model_name="anomaly_transformer",
            n_classes=2,
            hidden_dim=16,
            epochs=1,
            batch_size=4,
            seed=25,
        )

        self.assertEqual(val_proba.shape, (4, 2))
        self.assertEqual(test_proba.shape, (3, 2))
        self.assertEqual(diagnostics["model_family"], "anomaly_transformer_style_association_discrepancy")
        self.assertGreater(diagnostics["parameters"], 0)

    def test_train_sequence_model_accepts_graph_wavenet_and_reports_family(self) -> None:
        rng = np.random.default_rng(26)
        x_train = rng.normal(size=(10, 9, 5)).astype(np.float32)
        y_train = np.asarray([0, 1] * 5, dtype=np.int64)
        x_val = rng.normal(size=(4, 9, 5)).astype(np.float32)
        x_test = rng.normal(size=(3, 9, 5)).astype(np.float32)

        val_proba, test_proba, diagnostics = train_sequence_model(
            x_train,
            y_train,
            x_val,
            x_test,
            model_name="graph_wavenet",
            n_classes=2,
            hidden_dim=16,
            epochs=1,
            batch_size=4,
            seed=26,
        )

        self.assertEqual(val_proba.shape, (4, 2))
        self.assertEqual(test_proba.shape, (3, 2))
        self.assertEqual(diagnostics["model_family"], "graph_wavenet_style_adaptive_dilated_graph_temporal")
        self.assertEqual(diagnostics["graph_wavenet_adaptive_adjacency_shape"], [5, 5])
        self.assertGreater(diagnostics["parameters"], 0)


if __name__ == "__main__":
    unittest.main()
