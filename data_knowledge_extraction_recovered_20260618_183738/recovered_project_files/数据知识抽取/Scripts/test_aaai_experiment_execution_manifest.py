import json
import os
import shutil
import unittest
from importlib import import_module
from pathlib import Path


def load_builder():
    try:
        module = import_module("aaai_experiment_execution_manifest")
    except ModuleNotFoundError as exc:
        raise AssertionError("aaai_experiment_execution_manifest module is missing") from exc
    return module.build_execution_manifest


def _module():
    return import_module("aaai_experiment_execution_manifest")


def _exists(path: Path) -> bool:
    return os.path.exists(_module()._fs_path(path))


def _size(path: Path) -> int:
    return os.path.getsize(_module()._fs_path(path))


def _read_text(path: Path) -> str:
    with open(_module()._fs_path(path), "r", encoding="utf-8") as fh:
        return fh.read()


class AaaiExperimentExecutionManifestTest(unittest.TestCase):
    def setUp(self):
        self.output_dir = Path("knowledge_exports") / "_tmp_aaai_execution_manifest_test"
        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_manifest_writes_json_and_markdown(self):
        written = load_builder()(self.output_dir)

        expected = {
            self.output_dir / "aaai_experiment_execution_manifest.json",
            self.output_dir / "aaai_experiment_execution_manifest.md",
        }
        self.assertEqual(set(written), expected)
        for path in expected:
            self.assertTrue(_exists(path), path)
            self.assertGreater(_size(path), 1000, path)

    def test_manifest_covers_protocols_and_global_admission_rule(self):
        load_builder()(self.output_dir)
        manifest = json.loads(_read_text(self.output_dir / "aaai_experiment_execution_manifest.json"))

        self.assertEqual(manifest["version"], "aaai-claim-boundary-v1")
        self.assertEqual(manifest["seeds"], [42, 43, 44])
        self.assertEqual(manifest["global_admission_rule"]["tau_R_grid"], [0.55, 0.60, 0.65, 0.70])
        self.assertEqual(manifest["global_admission_rule"]["tau_q_grid"], [0.50, 0.60, 0.70])
        self.assertTrue(manifest["global_admission_rule"]["same_equation_across_datasets"])
        self.assertTrue(manifest["global_admission_rule"]["validation_only_selection"])
        self.assertIn("No test-set threshold or route tuning", manifest["global_admission_rule"]["invariants"])

        datasets = {dataset["name"]: dataset for dataset in manifest["datasets"]}
        self.assertEqual(set(datasets), {"TEP", "SKAB", "Hydraulic", "C-MAPSS"})
        for dataset in datasets.values():
            for required_key in ["split", "window_or_label", "primary_metric", "thresholding", "budget"]:
                self.assertIn(required_key, dataset)
        self.assertIn("48-step", datasets["SKAB"]["window_or_label"])
        self.assertIn("40 epochs", datasets["SKAB"]["budget"])
        self.assertIn("original remaining useful life regression", datasets["C-MAPSS"]["window_or_label"])
        self.assertIn("RUL RMSE", datasets["C-MAPSS"]["primary_metric"])
        self.assertNotIn("degradation-stage labels from RUL windows", datasets["C-MAPSS"]["window_or_label"])

    def test_official_source_adapted_controls_are_scored_but_not_official(self):
        load_builder()(self.output_dir)
        manifest = json.loads(_read_text(self.output_dir / "aaai_experiment_execution_manifest.json"))
        baselines = {baseline["name"]: baseline for baseline in manifest["baseline_obligations"]}

        for expected_name in ["PatchTST", "Anomaly Transformer", "Graph WaveNet"]:
            self.assertIn(expected_name, baselines)
            self.assertEqual("materialized_official_source_adapted_control", baselines[expected_name]["status"])
            self.assertIn("score_artifact", baselines[expected_name])
            self.assertFalse(baselines[expected_name]["official_external_score"])
            self.assertIn("official_external_score_false", baselines[expected_name]["checks"])
            self.assertIn("no_public_leaderboard_claim", baselines[expected_name]["checks"])
            self.assertIn("Scripts/", baselines[expected_name]["command_template"])
            self.assertIn("42,43,44", baselines[expected_name]["command_template"])

        for expected_name in [
            "TCN",
            "GRU",
            "FT-Transformer",
            "TranAD",
            "GDN",
            "MTAD-GAT",
            "C-MAPSS Ridge/HistGB/ExtraTrees",
            "C-MAPSS GRU/TCN RUL",
        ]:
            self.assertIn(expected_name, baselines)
            self.assertIn(baselines[expected_name]["status"], {"materialized_matched_protocol", "materialized_style_baseline"})

    def test_manifest_covers_gating_and_systematic_ablation_obligations(self):
        load_builder()(self.output_dir)
        manifest = json.loads(_read_text(self.output_dir / "aaai_experiment_execution_manifest.json"))

        gating = {item["name"]: item for item in manifest["reliability_gate_obligations"]}
        self.assertEqual(
            set(gating),
            {"ordinary gate", "attention gate", "validation-only gate", "complete reliability admission"},
        )
        self.assertEqual(gating["complete reliability admission"]["must_control"], ["G_k", "H_k", "C_k", "S_k", "B_k"])

        ablations = [item["name"] for item in manifest["systematic_ablation_plan"]]
        self.assertEqual(
            ablations,
            [
                "Anchor only",
                "Unfiltered evidence",
                "Expert only",
                "LLM only",
                "Lag/residual only",
                "Graph only",
                "No counterfactual guard",
                "No tail safety",
                "No complexity penalty",
                "Full model",
            ],
        )

    def test_markdown_report_preserves_claim_boundary_and_contains_no_secret_material(self):
        load_builder()(self.output_dir)
        report = _read_text(self.output_dir / "aaai_experiment_execution_manifest.md")

        for expected_fragment in [
            "# AAAI Experiment Execution Manifest",
            "Pending items are not completed result claims",
            "No test-set threshold or route tuning",
            "PatchTST",
            "Anomaly Transformer",
            "Graph WaveNet",
            "ordinary gate",
            "complete reliability admission",
            "Anchor only",
            "No complexity penalty",
        ]:
            self.assertIn(expected_fragment, report)
        self.assertNotIn("sk-", report)
        self.assertNotIn("SOTA-candidate", report)
        self.assertNotIn("camera-ready", report)


if __name__ == "__main__":
    unittest.main()
