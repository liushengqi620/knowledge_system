from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mechanism_gate_ablation_matrix import (
    build_command,
    filter_specs,
    render_report,
    skab_variant_specs,
    summarize_matrix,
    variant_has_expected_runs,
)


def _write_run(
    root: Path,
    *,
    seed: int,
    val: float,
    test: float,
    bal: float,
    val_per_class: dict[str, float] | None = None,
    source: str = "sensor_01",
    target: str = "sensor_02",
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": "skab",
        "target": "anomaly",
        "variant": "full",
        "seed": int(seed),
        "n_rows_total": 100,
        "val_metrics": {
            "macro_f1": float(val),
            "balanced_accuracy": float(val),
            "per_class": {
                str(cls): {"f1": float(score)}
                for cls, score in (val_per_class or {"0": val, "1": val}).items()
            },
        },
        "primary_test_metrics": {"macro_f1": float(test), "balanced_accuracy": float(bal)},
        "efficiency": {"test_inference_samples_per_second": 100.0, "parameters": 10},
        "diagnostics": {"config": {"max_paths": 8}, "test_diagnostics": {}},
        "top_evidence_paths": [
            {"source": source, "target": target, "path": f"{source} -> {target}", "group_path": f"{source} -> {target}"}
        ],
    }
    path = root / f"ms_gse_rpf_skab_anomaly_full_prior-none_seed{seed}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")


class MechanismGateAblationMatrixTest(unittest.TestCase):
    def test_build_command_contains_external_candidate_gate_flags(self) -> None:
        specs = {spec.name: spec for spec in skab_variant_specs()}
        command = build_command(
            specs["expert_candidate_data_gate"],
            output_root=Path("runs"),
            seeds="42",
            device="cpu",
            profile="smoke",
            python_executable="python",
        )

        self.assertIn("--external-edge-candidate-only", command)
        self.assertIn("--use-candidate-prior-admission", command)
        self.assertIn("--candidate-prior-admission-target", command)
        self.assertIn("coverage_feature", command)
        self.assertIn("--use-task-salience", command)

    def test_no_complexity_variant_disables_only_source_family_scaling(self) -> None:
        specs = {spec.name: spec for spec in skab_variant_specs()}
        guarded_command = build_command(
            specs["expert_llm_candidate_data_gate_complexity_guarded"],
            output_root=Path("runs"),
            seeds="42",
            device="cpu",
            profile="smoke",
            python_executable="python",
        )
        command = build_command(
            specs["expert_llm_candidate_data_gate_no_complexity"],
            output_root=Path("runs"),
            seeds="42",
            device="cpu",
            profile="smoke",
            python_executable="python",
        )

        self.assertIn("--evidence-prior-mode", command)
        self.assertIn("expert_llm", command)
        self.assertIn("--external-candidate-families", command)
        self.assertIn("expert,llm", command)
        self.assertIn("--external-family-min-data-support", command)
        self.assertIn("--disable-source-complexity-penalty", command)
        self.assertIn("--use-candidate-prior-admission", command)
        self.assertIn("--external-candidate-llm-scale", guarded_command)
        self.assertNotIn("--disable-source-complexity-penalty", guarded_command)

    def test_summarize_matrix_reports_source_complexity_ablation_state(self) -> None:
        specs = [
            spec
            for spec in skab_variant_specs()
            if spec.name in {"no_mechanism", "expert_llm_candidate_data_gate_no_complexity"}
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_run(root / "no_mechanism", seed=42, val=0.80, test=0.78, bal=0.79)
            _write_run(
                root / "expert_llm_candidate_data_gate_no_complexity",
                seed=42,
                val=0.82,
                test=0.81,
                bal=0.82,
            )
            run_path = next((root / "expert_llm_candidate_data_gate_no_complexity").glob("*.json"))
            payload = json.loads(run_path.read_text(encoding="utf-8"))
            payload["evidence_prior"] = {
                "external_candidate_prior": {
                    "candidate_edge_count": 3,
                    "family_edges": {"expert": 2, "llm": 1},
                    "source_complexity_penalty": {
                        "disabled_for_ablation": True,
                        "effective_scales": {"expert": 1.0, "llm": 1.0, "default": 1.0},
                    },
                }
            }
            run_path.write_text(json.dumps(payload), encoding="utf-8")

            summary = summarize_matrix(output_root=root, specs=specs, expected_seeds=[42])

        rows = {row["variant"]: row for row in summary}
        stats = rows["expert_llm_candidate_data_gate_no_complexity"]["source_complexity"]
        self.assertEqual(stats["mean_external_candidate_edges"], 3.0)
        self.assertEqual(stats["mean_external_source_families"], 2.0)
        self.assertEqual(stats["source_complexity_disabled_fraction"], 1.0)
        self.assertEqual(stats["mean_effective_llm_candidate_scale"], 1.0)

    def test_summarize_matrix_rejects_low_tail_harm(self) -> None:
        specs = [spec for spec in skab_variant_specs() if spec.name in {"no_mechanism", "expert_candidate_data_gate"}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_run(
                root / "no_mechanism",
                seed=42,
                val=0.80,
                test=0.78,
                bal=0.79,
                val_per_class={"0": 0.85, "1": 0.75},
            )
            _write_run(
                root / "expert_candidate_data_gate",
                seed=42,
                val=0.82,
                test=0.81,
                bal=0.82,
                val_per_class={"0": 0.92, "1": 0.60},
            )

            summary = summarize_matrix(
                output_root=root,
                specs=specs,
                expected_seeds=[42],
                max_low_tail_f1_drop=0.05,
            )

        rows = {row["variant"]: row for row in summary}
        self.assertEqual(rows["no_mechanism"]["status"], "baseline_complete")
        self.assertEqual(rows["expert_candidate_data_gate"]["status"], "rejected")
        self.assertIn("low_tail_class_harm", rows["expert_candidate_data_gate"]["reject_reasons"])

    def test_variant_has_expected_runs_requires_every_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_run(root / "no_mechanism", seed=42, val=0.80, test=0.78, bal=0.79)

            self.assertTrue(variant_has_expected_runs(root, "no_mechanism", [42]))
            self.assertFalse(variant_has_expected_runs(root, "no_mechanism", [42, 43]))

    def test_filter_specs_selects_explicit_variant_subset(self) -> None:
        selected = filter_specs(
            skab_variant_specs(),
            "no_mechanism,expert_llm_candidate_data_gate_complexity_guarded,expert_llm_candidate_data_gate_no_complexity",
        )

        self.assertEqual(
            [spec.name for spec in selected],
            [
                "no_mechanism",
                "expert_llm_candidate_data_gate_no_complexity",
                "expert_llm_candidate_data_gate_complexity_guarded",
            ],
        )

    def test_render_report_marks_missing_rows_as_not_evidence(self) -> None:
        specs = skab_variant_specs()[:2]
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
                "variant": "no_mechanism",
                "status": "missing",
                "n_runs": 0,
                "test_macro_f1_mean": 0.0,
                "test_macro_f1_std": 0.0,
                "mean_val_gain_vs_baseline": 0.0,
                "mean_test_gain_vs_baseline": 0.0,
                "low_tail_val_f1_gain": 0.0,
                "baseline_path_jaccard": 0.0,
                "source_complexity": {},
                "reject_reasons": ["no_runs"],
            }
        ]

        report = render_report(specs=specs, commands=commands, summary=summary, output_root=Path("runs"))

        self.assertIn("# Mechanism Gate Ablation Matrix", report)
        self.assertIn("Missing rows are not evidence", report)
        self.assertIn("Source burden", report)
        self.assertIn("raw_expert_graph", report)
        self.assertIn("no_runs", report)


if __name__ == "__main__":
    unittest.main()
