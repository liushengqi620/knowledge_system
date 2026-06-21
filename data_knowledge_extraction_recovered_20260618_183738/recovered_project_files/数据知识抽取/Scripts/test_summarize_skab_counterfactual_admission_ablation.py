from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from Scripts.summarize_skab_counterfactual_admission_ablation import summarize


def _write_result(path: Path, *, macro: float, baseline: float, far: float, mode: str, changed: int) -> None:
    path.write_text(
        json.dumps(
            {
                "seed": 42,
                "macro_f1_delta": macro - baseline,
                "edge_policy": {"policy": "learned_reliability", "n_kept_edges": 2},
                "edge_counterfactual": {"mode": mode, "n_changed_edges": changed},
                "baseline": {"metrics": {"macro_f1": baseline}},
                "dynamic_llm_kg": {
                    "metrics": {"macro_f1": macro},
                    "protocol": {"binary": {"f1": 0.8, "far_percent": far, "mar_percent": 10.0}},
                },
                "dynamic_edges": [
                    {"source": "Current", "target": "Pressure", "lags": [1]},
                    {"source": "Pressure", "target": "Accelerometer1RMS", "lags": [2]},
                ],
            }
        ),
        encoding="utf-8",
    )


class SummarizeSkabCounterfactualAdmissionAblationTest(unittest.TestCase):
    def test_summarizes_no_cf_admission_and_post_admission_perturbations(self) -> None:
        root = Path.cwd() / "tmp_tests" / f"skab_cf_admission_{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        original = root / "original.json"
        reverse = root / "reverse.json"
        lag = root / "lag.json"
        _write_result(original, macro=0.90, baseline=0.88, far=7.0, mode="none", changed=0)
        _write_result(reverse, macro=0.86, baseline=0.88, far=12.0, mode="reverse_direction", changed=2)
        _write_result(lag, macro=0.89, baseline=0.88, far=8.0, mode="lag_shift", changed=2)

        report = summarize(
            original=original,
            perturbations=[("Reverse", reverse), ("LagShift", lag)],
        )

        self.assertIn("# SKAB Counterfactual Admission Ablation", report)
        self.assertIn("no-CF admission route", report)
        self.assertIn("post-admission perturbation", report)
        self.assertIn("CF_k", report)
        self.assertIn("0.9000", report)
        self.assertIn("-0.0400", report)
        self.assertIn("mean perturbation drop", report)
        self.assertIn("AAAI status: Partial", report)
        self.assertIn("not yet a pre-admission CF guard", report)


if __name__ == "__main__":
    unittest.main()
