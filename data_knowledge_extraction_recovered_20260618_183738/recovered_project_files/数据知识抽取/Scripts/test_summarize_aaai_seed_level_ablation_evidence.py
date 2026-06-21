from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_aaai_seed_level_ablation_evidence import (
    build_seed_level_ablation_evidence,
    render_markdown,
    write_seed_level_ablation_evidence,
)


class SummarizeAaaiSeedLevelAblationEvidenceTest(unittest.TestCase):
    def test_build_report_collects_seed_level_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_seed_level_ablation_evidence(Path(tmp))

        self.assertIn(report["status"], {"partial", "missing"})
        self.assertGreaterEqual(report["rows_total"], 10)
        self.assertGreaterEqual(report["complete_seed_level_rows"], 5)
        variants = {row["variant"] for row in report["rows"]}
        self.assertIn("skab_strong_anchor", variants)
        self.assertIn("residual_gated_lagged", variants)
        self.assertIn("expert_candidate_data_gate", variants)
        self.assertIn("expert_llm_candidate_data_gate_no_complexity", variants)
        for row in report["rows"]:
            self.assertGreaterEqual(row["n_seeds"], 1)
            if row["n_seeds"] >= 3:
                self.assertGreaterEqual(len(row["artifact_paths"]), 3)

    def test_markdown_mentions_remaining_design_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            markdown = render_markdown(build_seed_level_ablation_evidence(Path(tmp)))

        self.assertIn("# AAAI Seed-Level Ablation Evidence", markdown)
        self.assertIn("No-tail-safety", markdown)
        self.assertIn("No-counterfactual-guard", markdown)
        self.assertIn("source-family scale", markdown)

    def test_write_outputs_json_markdown_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            written = write_seed_level_ablation_evidence(output_dir)

            self.assertEqual(set(written), {output_dir / "aaai_seed_level_ablation_evidence.json", output_dir / "aaai_seed_level_ablation_evidence.md"})
            payload = json.loads((output_dir / "aaai_seed_level_ablation_evidence.json").read_text(encoding="utf-8"))
            self.assertGreater(payload["complete_seed_level_rows"], 0)
            self.assertTrue((output_dir / payload["artifact_root"]).exists())


if __name__ == "__main__":
    unittest.main()
