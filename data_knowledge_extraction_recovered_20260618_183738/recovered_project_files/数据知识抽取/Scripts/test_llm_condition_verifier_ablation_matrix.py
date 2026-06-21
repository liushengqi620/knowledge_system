from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from llm_condition_verifier_ablation_matrix import (
    build_command,
    llm_condition_variant_specs,
    render_report,
)


class LLMConditionVerifierAblationMatrixTest(unittest.TestCase):
    def test_variant_matrix_contains_a0_to_a5(self) -> None:
        specs = llm_condition_variant_specs()

        self.assertEqual([spec.name for spec in specs], [
            "a0_algorithmic_only",
            "a1_expert_candidate_gate",
            "a2_independent_llm_candidate",
            "a3_llm_expert_graph_correction",
            "a4_llm_expert_condition_verifier",
            "a5_weak_class_condition_verifier",
        ])

    def test_main_verifier_command_uses_metadata_only_gate_flags(self) -> None:
        specs = {spec.name: spec for spec in llm_condition_variant_specs()}
        command = build_command(
            specs["a4_llm_expert_condition_verifier"],
            output_root=Path("runs"),
            ready_root=Path("ready_probe"),
            seeds="42",
            device="cpu",
            profile="smoke",
            python_executable="python",
        )

        self.assertIn("--ready-root", command)
        self.assertIn("ready_probe", command)
        self.assertIn("--use-llm-expert-condition-verifier", command)
        self.assertIn("--llm-condition-verifier-min-data-support", command)
        joined = " ".join(command)
        self.assertIn("--evidence-prior-mode none", joined)
        self.assertIn("--llm-condition-verifier-target candidate_gate", joined)
        self.assertNotIn("--external-edge-candidate-only", command)
        self.assertNotIn("--external-candidate-families", command)

    def test_independent_llm_control_uses_llm_family_only(self) -> None:
        specs = {spec.name: spec for spec in llm_condition_variant_specs()}
        command = build_command(
            specs["a2_independent_llm_candidate"],
            output_root=Path("runs"),
            seeds="42",
            device="cpu",
            profile="smoke",
            python_executable="python",
        )

        joined = " ".join(command)
        self.assertIn("--evidence-prior-mode llm", joined)
        self.assertIn("--external-candidate-families llm", joined)
        self.assertNotIn("--use-llm-expert-condition-verifier", command)

    def test_render_report_names_main_branch(self) -> None:
        specs = llm_condition_variant_specs()
        commands = {
            spec.name: build_command(
                spec,
                output_root=Path("runs"),
                seeds="42",
                device="cpu",
                profile="smoke",
                python_executable="python",
            )
            for spec in specs
        }
        summary = [
            {
                "variant": "a4_llm_expert_condition_verifier",
                "status": "missing",
                "n_runs": 0,
                "test_macro_f1_mean": 0.0,
                "test_macro_f1_std": 0.0,
                "mean_val_gain_vs_baseline": 0.0,
                "mean_test_gain_vs_baseline": 0.0,
                "low_tail_val_f1_gain": 0.0,
                "reject_reasons": ["no_runs"],
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            report = render_report(
                specs=specs,
                commands=commands,
                summary=summary,
                output_root=Path(tmp),
                ready_root=None,
            )

        self.assertIn("LLM Expert-Condition Verifier Ablation Matrix", report)
        self.assertIn("a4_llm_expert_condition_verifier", report)
        self.assertIn("main paper branch", report)


if __name__ == "__main__":
    unittest.main()
