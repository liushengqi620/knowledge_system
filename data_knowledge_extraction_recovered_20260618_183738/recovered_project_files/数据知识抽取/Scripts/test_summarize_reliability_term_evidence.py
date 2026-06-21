from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from summarize_reliability_term_evidence import summarize


class SummarizeReliabilityTermEvidenceTest(unittest.TestCase):
    def test_summarizes_reliability_terms_across_datasets(self) -> None:
        root = Path.cwd() / "tmp_tests" / f"reliability_terms_{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        learned_files: list[Path] = []
        for seed, base, routed in [(42, 0.80, 0.84), (43, 0.82, 0.85)]:
            path = root / f"learned_{seed}.json"
            path.write_text(
                json.dumps(
                    {
                        "seed": seed,
                        "baseline": {"metrics": {"macro_f1": base}},
                        "dynamic_llm_kg": {
                            "metrics": {"macro_f1": routed},
                            "protocol": {"binary": {"f1": 0.77, "far_percent": 4.0, "mar_percent": 5.0}},
                        },
                        "macro_f1_delta": routed - base,
                    }
                ),
                encoding="utf-8",
            )
            learned_files.append(path)

        original = root / "cf_original.json"
        reverse = root / "cf_reverse.json"
        for path, value, mode, changed in [
            (original, 0.90, "none", 0),
            (reverse, 0.87, "reverse_direction", 4),
        ]:
            path.write_text(
                json.dumps(
                    {
                        "dynamic_llm_kg": {
                            "metrics": {"macro_f1": value},
                            "protocol": {"binary": {"f1": 0.8, "far_percent": 1.0, "mar_percent": 2.0}},
                        },
                        "macro_f1_delta": 0.0,
                        "edge_counterfactual": {"mode": mode, "n_changed_edges": changed},
                    }
                ),
                encoding="utf-8",
            )

        cmapss = root / "cmapss.json"
        cmapss.write_text(
            json.dumps(
                {
                    "subset": "FD001",
                    "runs": [
                        {
                            "main": {"macro_f1": 0.70},
                            "ere_reliability_routing": {"macro_f1": 0.73},
                            "tail_guarded_ere_reliability_routing": {"macro_f1": 0.72},
                        },
                        {
                            "main": {"macro_f1": 0.80},
                            "ere_reliability_routing": {"macro_f1": 0.81},
                            "tail_guarded_ere_reliability_routing": {"macro_f1": 0.80},
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        kg = root / "kg.json"
        kg.write_text(
            json.dumps(
                {
                    "runs": [
                        {"mode": "original_full_msfg", "macro_f1": 0.86, "fusion": {"n_fused_edges": 12}},
                        {"mode": "full_pruned_kg", "macro_f1": 0.89, "fusion": {"n_fused_edges": 9}},
                    ]
                }
            ),
            encoding="utf-8",
        )

        report = summarize(
            learned_reliability_files=learned_files,
            counterfactual_files=[("Original", original), ("Reverse", reverse)],
            cmapss_files=[cmapss],
            pruned_kg_file=kg,
        )

        self.assertIn("Validation-benefit admission", report)
        self.assertIn("0.8100 +/- 0.0100", report)
        self.assertIn("0.8450 +/- 0.0050", report)
        self.assertIn("Counterfactual edge consistency", report)
        self.assertIn("-0.0300", report)
        self.assertIn("Low-tail non-degradation", report)
        self.assertIn("2/2", report)
        self.assertIn("Complexity/source pruning", report)
        self.assertIn("+0.0300", report)


if __name__ == "__main__":
    unittest.main()
