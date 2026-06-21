from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aaai_goal_completion_audit import build_goal_completion_audit, build_goal_completion_report, render_markdown


class AaaiGoalCompletionAuditTest(unittest.TestCase):
    def test_report_tracks_satisfied_goal_items_after_matched_controls(self) -> None:
        report = build_goal_completion_report(Path("knowledge_exports") / "aaai_latex_draft")

        requirement_ids = {item["id"] for item in report["requirements"]}
        self.assertIn("figures_1_to_3", requirement_ids)
        self.assertIn("reproducible_algorithm", requirement_ids)
        self.assertIn("gate_attention_distinction", requirement_ids)
        self.assertIn("protocol_trustworthiness", requirement_ids)
        self.assertIn("strong_baseline_alignment", requirement_ids)
        self.assertIn("efficiency_experiments", requirement_ids)
        self.assertIn("bilingual_manuscripts", requirement_ids)
        self.assertIn("official_leaderboard_sota", requirement_ids)
        self.assertIn("official_aaai_template", requirement_ids)
        self.assertIn("final_aaai_claim", requirement_ids)

        status_by_id = {item["id"]: item["status"] for item in report["requirements"]}
        self.assertEqual("satisfied", status_by_id["figures_1_to_3"])
        self.assertEqual("satisfied", status_by_id["reproducible_algorithm"])
        self.assertEqual("satisfied", status_by_id["gate_attention_distinction"])
        self.assertEqual("satisfied", status_by_id["protocol_trustworthiness"])
        self.assertEqual("satisfied", status_by_id["strong_baseline_alignment"])
        self.assertEqual("satisfied", status_by_id["efficiency_experiments"])
        self.assertEqual("satisfied", status_by_id["bilingual_manuscripts"])
        self.assertEqual("partial", status_by_id["official_leaderboard_sota"])
        self.assertEqual("satisfied", status_by_id["official_aaai_template"])
        self.assertEqual("not_ready", status_by_id["final_aaai_claim"])

        self.assertEqual("not_complete", report["overall_status"])
        blocker_text = "\n".join(report["remaining_blockers"])
        self.assertIn("exact native split/preprocessing/metric/budget/baseline reproductions", blocker_text)
        self.assertNotIn("official AAAI LaTeX compile log", blocker_text)

    def test_markdown_is_submission_safe_and_explains_imagegen_route(self) -> None:
        report = build_goal_completion_report(Path("knowledge_exports") / "aaai_latex_draft")
        markdown = render_markdown(report)

        self.assertIn("# AAAI Goal Completion Audit", markdown)
        self.assertIn("deterministic vector/PDF route", markdown)
        self.assertIn("imagegen bitmap was not used", markdown)
        self.assertIn("PatchTST", markdown)
        self.assertIn("Anomaly Transformer", markdown)
        self.assertIn("Graph WaveNet", markdown)
        self.assertIn("Chinese UTF-8 reading draft", markdown)
        self.assertIn("three-seed measured parameter", markdown)
        self.assertIn("official_sota_not_admissible", markdown)
        self.assertIn("not_complete", markdown)
        self.assertIn("official_external_score=false", markdown)
        self.assertNotIn("camera" + "-ready", markdown)
        self.assertNotIn("SOTA-candidate", markdown)
        self.assertNotRegex(markdown, r"sk-[A-Za-z0-9]{12,}")

    def test_build_goal_completion_audit_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = build_goal_completion_audit(output_dir)

            json_path = output_dir / "aaai_goal_completion_audit.json"
            markdown_path = output_dir / "aaai_goal_completion_audit.md"
            self.assertEqual(set(written), {json_path, markdown_path})
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertEqual("not_complete", payload["overall_status"])
            self.assertIn("AAAI Goal Completion Audit", markdown)


if __name__ == "__main__":
    unittest.main()
