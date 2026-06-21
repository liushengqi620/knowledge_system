from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from summarize_aaai_missing_ablation_execution_plan import (
    build_execution_plan,
    render_markdown,
    write_execution_plan,
)


class MissingAblationExecutionPlanTest(unittest.TestCase):
    def test_plan_lists_exact_remaining_final_ablation_gaps(self) -> None:
        plan = build_execution_plan()
        names = [row["ablation"] for row in plan["rows"]]

        self.assertEqual(names, [])
        self.assertEqual(plan["status"], "complete")
        closed = {row["ablation"]: row["status"] for row in plan["closed_rows"]}
        self.assertEqual(closed["No counterfactual guard"], "complete_seed_level_evidence")
        self.assertEqual(closed["No tail safety"], "complete_policy_replay")
        self.assertEqual(closed["No complexity penalty"], "complete_seed_level_evidence")
        self.assertEqual(plan["seeds"], [42, 43, 44])
        self.assertIn("one-mechanism intervention", plan["completion_rule"])

    def test_markdown_contains_commands_metrics_and_guardrail(self) -> None:
        markdown = render_markdown(build_execution_plan())

        self.assertIn("# AAAI Missing Ablation Execution Plan", markdown)
        self.assertIn("verify each flag is supported by the local parser", markdown)
        self.assertIn("- Status: complete", markdown)
        self.assertIn("Closed Rows", markdown)
        self.assertIn("No counterfactual guard", markdown)
        self.assertIn("complete_policy_replay", markdown)
        self.assertIn("complete_seed_level_evidence", markdown)
        self.assertIn("42, 43, 44", markdown)

    def test_write_execution_plan_outputs_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_execution_plan(Path(tmpdir))

            self.assertEqual(len(paths), 2)
            for path in paths:
                self.assertTrue(path.exists(), path)
            self.assertTrue((Path(tmpdir) / "aaai_missing_ablation_execution_plan.json").exists())
            self.assertTrue((Path(tmpdir) / "aaai_missing_ablation_execution_plan.md").exists())


if __name__ == "__main__":
    unittest.main()
