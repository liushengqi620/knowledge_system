from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_aaai_ablation_coverage import build_ablation_coverage_report, render_markdown, write_ablation_coverage


class SummarizeAaaiAblationCoverageTest(unittest.TestCase):
    def test_report_marks_ablation_coverage_as_complete(self) -> None:
        report = build_ablation_coverage_report()

        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["planned_ablation_count"], 10)
        self.assertEqual(report["missing_or_incomplete"], [])
        names = {item["name"] for item in report["items"]}
        self.assertIn("No counterfactual guard", names)
        self.assertIn("No tail safety", names)
        self.assertIn("Full model", names)
        status_by_name = {item["name"]: item["status"] for item in report["items"]}
        self.assertEqual(status_by_name["No counterfactual guard"], "seed_level_evidence")
        self.assertEqual(status_by_name["No tail safety"], "seed_level_policy_replay")
        self.assertEqual(status_by_name["No complexity penalty"], "seed_level_evidence")

    def test_markdown_exposes_completion_rule_and_missing_rows(self) -> None:
        markdown = render_markdown(build_ablation_coverage_report())

        self.assertIn("# AAAI Ablation Coverage Audit", markdown)
        self.assertIn("matched-protocol seed-level metrics", markdown)
        self.assertIn("No complexity penalty", markdown)
        self.assertIn("Missing-row execution plan", markdown)
        self.assertIn("Missing or Incomplete Rows", markdown)

    def test_write_ablation_coverage_outputs_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            written = write_ablation_coverage(output_dir)

            self.assertEqual(set(written), {output_dir / "aaai_ablation_coverage_audit.json", output_dir / "aaai_ablation_coverage_audit.md"})
            payload = json.loads((output_dir / "aaai_ablation_coverage_audit.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "complete")
            self.assertIn("AAAI Ablation Coverage Audit", (output_dir / "aaai_ablation_coverage_audit.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
