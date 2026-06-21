from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_ms_gse_rpf_admission import _candidate_source_family, build_admission_report, render_markdown, write_report


def _write_run(
    root: Path,
    *,
    seed: int,
    val: float,
    test: float,
    bal: float,
    salience: float = 0.0,
    prior: str = "none",
    path_source: str = "PS2_mean",
    path_target: str = "FS2_max",
    val_per_class: dict[str, float] | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"ms_gse_rpf_hydraulic_valve_full_prior-{prior}_seed{seed}.json"
    payload = {
        "dataset": "hydraulic",
        "target": "valve",
        "variant": "full",
        "seed": seed,
        "n_rows_total": 2205,
        "val_metrics": {
            "macro_f1": val,
            "balanced_accuracy": val,
            "per_class": {
                str(cls): {"f1": float(score)}
                for cls, score in (val_per_class or {"0": val, "1": val, "2": val}).items()
            },
        },
        "primary_test_metrics": {"macro_f1": test, "balanced_accuracy": bal},
        "efficiency": {"test_inference_samples_per_second": 100.0 + seed, "parameters": 10},
        "diagnostics": {
            "test_diagnostics": {"mean_path_salience_weight": salience},
            "config": {"max_paths": 16},
        },
        "top_evidence_paths": [
            {"source": path_source, "target": path_target, "path": f"{path_source} -> {path_target}"},
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class SummarizeMSGserpfAdmissionTest(unittest.TestCase):
    def test_candidate_source_family_keeps_class_blend_algorithmic(self) -> None:
        self.assertEqual(_candidate_source_family("class_blend"), "algorithmic")
        self.assertEqual(_candidate_source_family("expert_llm_cal"), "llm")

    def test_selects_candidate_only_when_validation_improves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            candidate = root / "candidate"
            _write_run(baseline, seed=42, val=0.80, test=0.70, bal=0.71)
            _write_run(candidate, seed=42, val=0.85, test=0.82, bal=0.83, salience=0.8)
            _write_run(baseline, seed=43, val=0.80, test=0.75, bal=0.76)
            _write_run(candidate, seed=43, val=0.79, test=0.60, bal=0.61, salience=0.9)

            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("salience", candidate)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="prior-none",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
            )

        selected = {item["seed"]: item["selected_candidate"] for item in report["decisions"]}
        self.assertEqual(selected[42], "salience")
        self.assertEqual(selected[43], "baseline")
        self.assertEqual(report["selected_source_family_counts"]["algorithmic"], 1)
        self.assertEqual(report["selected_source_family_counts"]["baseline"], 1)
        self.assertAlmostEqual(report["summary"]["macro_f1_mean"], (0.82 + 0.75) / 2)
        self.assertEqual(report["admitted_runs"][0]["variant"], "full_admitted")
        markdown = render_markdown(report)
        self.assertIn("Validation Admission", markdown)
        self.assertIn("salience=0.8500", markdown)
        self.assertIn("selected source-family counts", markdown)

    def test_write_report_materializes_selected_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            candidate = root / "candidate"
            _write_run(baseline, seed=42, val=0.80, test=0.70, bal=0.71)
            _write_run(candidate, seed=42, val=0.85, test=0.82, bal=0.83, salience=0.8)
            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("salience", candidate)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="prior-none",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
            )
            written = write_report(report, root / "admission")
            selected = root / "admission" / "selected_runs" / "ms_gse_rpf_hydraulic_valve_full_admitted_prior-admitted_seed42.json"

            self.assertIn(selected, written)
            payload = json.loads(selected.read_text(encoding="utf-8"))

        self.assertEqual(payload["variant"], "full_admitted")
        self.assertEqual(payload["admission"]["selected_candidate"], "salience")

    def test_all_filename_filter_allows_different_prior_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            candidate = root / "candidate"
            _write_run(baseline, seed=42, val=0.80, test=0.70, bal=0.71, prior="none")
            _write_run(candidate, seed=42, val=0.86, test=0.83, bal=0.84, prior="expert")

            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("expert_prior", candidate)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="__all__",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
            )

        selected = {item["seed"]: item["selected_candidate"] for item in report["decisions"]}
        self.assertEqual(selected[42], "expert_prior")
        self.assertEqual(report["selected_source_family_counts"]["expert"], 1)
        self.assertIn("prior-expert", report["admitted_runs"][0]["admission"]["source_result_path"])

    def test_candidate_penalty_blocks_tiny_validation_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            candidate = root / "candidate"
            _write_run(baseline, seed=42, val=0.800, test=0.70, bal=0.71, prior="none")
            _write_run(candidate, seed=42, val=0.805, test=0.90, bal=0.91, prior="expert")

            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("expert_prior", candidate)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="__all__",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
                candidate_penalties={"expert_prior": 0.01},
            )

        decision = report["decisions"][0]
        self.assertEqual(decision["selected_candidate"], "baseline")
        expert = [item for item in decision["considered"] if item["candidate"] == "expert_prior"][0]
        self.assertAlmostEqual(expert["adjusted_val_metric"], 0.795)

    def test_stability_bonus_can_admit_more_stable_path_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            stable = root / "stable"
            unstable = root / "unstable"
            for seed in (42, 43):
                _write_run(baseline, seed=seed, val=0.800, test=0.70, bal=0.71, path_source=f"B{seed}", path_target="T")
                _write_run(stable, seed=seed, val=0.804, test=0.83, bal=0.84, path_source="PS2_mean", path_target="FS2_max")
                _write_run(unstable, seed=seed, val=0.805, test=0.82, bal=0.83, path_source=f"U{seed}", path_target="FS2_max")

            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("stable", stable), ("unstable", unstable)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="prior-none",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
                stability_bonus_weight=0.01,
            )

        self.assertGreater(report["candidate_stability_scores"]["stable"], report["candidate_stability_scores"]["unstable"])
        selected = {item["seed"]: item["selected_candidate"] for item in report["decisions"]}
        self.assertEqual(selected[42], "stable")
        self.assertEqual(selected[43], "stable")
        markdown = render_markdown(report)
        self.assertIn("stability bonus weight", markdown)

    def test_path_disruption_penalty_blocks_path_replacement_for_tiny_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            candidate = root / "candidate"
            for seed in (42, 43):
                _write_run(
                    baseline,
                    seed=seed,
                    val=0.800,
                    test=0.70,
                    bal=0.71,
                    path_source="shared_source",
                    path_target="shared_target",
                )
                _write_run(
                    candidate,
                    seed=seed,
                    val=0.805,
                    test=0.90,
                    bal=0.91,
                    path_source=f"candidate_source_{seed}",
                    path_target="candidate_target",
                )

            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("path_changer", candidate)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="prior-none",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
                path_disruption_penalty_weight=0.01,
            )

        self.assertEqual(report["candidate_baseline_path_jaccard"]["path_changer"], 0.0)
        selected = {item["seed"]: item["selected_candidate"] for item in report["decisions"]}
        self.assertEqual(selected[42], "baseline")
        self.assertEqual(selected[43], "baseline")
        candidate_row = [item for item in report["decisions"][0]["considered"] if item["candidate"] == "path_changer"][0]
        self.assertAlmostEqual(candidate_row["path_disruption_penalty"], 0.01)
        self.assertAlmostEqual(candidate_row["adjusted_val_metric"], 0.795)

    def test_candidate_certificate_can_require_baseline_path_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            candidate = root / "candidate"
            for seed in (42, 43):
                _write_run(
                    baseline,
                    seed=seed,
                    val=0.800,
                    test=0.70,
                    bal=0.71,
                    path_source="shared_source",
                    path_target="shared_target",
                    val_per_class={"0": 0.80, "1": 0.80, "2": 0.80},
                )
                _write_run(
                    candidate,
                    seed=seed,
                    val=0.830,
                    test=0.90,
                    bal=0.91,
                    path_source=f"candidate_source_{seed}",
                    path_target="candidate_target",
                    val_per_class={"0": 0.84, "1": 0.84, "2": 0.84},
                )

            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("path_changer", candidate)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="prior-none",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
                require_candidate_certificate=True,
                certificate_min_baseline_path_jaccard=0.20,
            )

        cert = report["candidate_certificates"]["path_changer"]
        self.assertFalse(cert["admitted"])
        self.assertIn("baseline_path_overlap_below_threshold", cert["reject_reasons"])
        selected = {item["seed"]: item["selected_candidate"] for item in report["decisions"]}
        self.assertEqual(selected[42], "baseline")
        markdown = render_markdown(report)
        self.assertIn("Path Jaccard", markdown)

    def test_candidate_certificate_blocks_low_tail_class_harm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            harmful = root / "harmful"
            for seed in (42, 43):
                _write_run(
                    baseline,
                    seed=seed,
                    val=0.800,
                    test=0.70,
                    bal=0.71,
                    val_per_class={"0": 0.80, "1": 0.80, "2": 0.80},
                )
                _write_run(
                    harmful,
                    seed=seed,
                    val=0.820,
                    test=0.90,
                    bal=0.91,
                    val_per_class={"0": 0.88, "1": 0.86, "2": 0.68},
                )

            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("harmful", harmful)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="prior-none",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
                require_candidate_certificate=True,
                certificate_max_low_tail_f1_drop=0.05,
            )

        self.assertFalse(report["candidate_certificates"]["harmful"]["admitted"])
        self.assertIn("low_tail_class_harm", report["candidate_certificates"]["harmful"]["reject_reasons"])
        selected = {item["seed"]: item["selected_candidate"] for item in report["decisions"]}
        self.assertEqual(selected[42], "baseline")
        self.assertEqual(selected[43], "baseline")
        markdown = render_markdown(report)
        self.assertIn("Candidate Certificates", markdown)
        self.assertIn("low_tail_class_harm", markdown)

    def test_candidate_certificate_allows_balanced_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            balanced = root / "balanced"
            for seed in (42, 43):
                _write_run(
                    baseline,
                    seed=seed,
                    val=0.800,
                    test=0.70,
                    bal=0.71,
                    val_per_class={"0": 0.80, "1": 0.80, "2": 0.80},
                )
                _write_run(
                    balanced,
                    seed=seed,
                    val=0.830,
                    test=0.90,
                    bal=0.91,
                    val_per_class={"0": 0.84, "1": 0.83, "2": 0.82},
                )

            report = build_admission_report(
                baseline_dir=baseline,
                candidates=[("balanced", balanced)],
                dataset="hydraulic",
                target="valve",
                variant="full",
                filename_contains="prior-none",
                n_rows_total=2205,
                min_val_gain=0.0,
                metric_key="macro_f1",
                require_candidate_certificate=True,
                certificate_max_low_tail_f1_drop=0.05,
            )

        self.assertTrue(report["candidate_certificates"]["balanced"]["admitted"])
        selected = {item["seed"]: item["selected_candidate"] for item in report["decisions"]}
        self.assertEqual(selected[42], "balanced")
        self.assertEqual(selected[43], "balanced")


if __name__ == "__main__":
    unittest.main()
