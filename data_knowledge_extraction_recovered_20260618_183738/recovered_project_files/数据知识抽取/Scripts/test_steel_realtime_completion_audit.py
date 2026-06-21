from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from verify_steel_realtime_completion import build_completion_audit


class SteelRealtimeCompletionAuditTests(unittest.TestCase):
    def test_completion_audit_maps_goal_requirements_to_evidence(self) -> None:
        root = Path(__file__).parent.parent
        output_dir = root / "knowledge_exports" / "steel_realtime_system_v1"

        report = build_completion_audit(output_dir=output_dir)

        self.assertEqual(report["status"], "pass")
        requirements = {row["id"]: row for row in report["requirements"]}
        expected = [
            "neutral_system_name",
            "no_specific_company_copy",
            "industrial_visual_design",
            "realtime_event_loop",
            "three_level_function_chain",
            "interactive_trace_graph",
            "continuous_casting_evidence_boundary",
            "llm_assistant_bounded_role",
            "vben_admin_module_and_preview",
            "deployment_and_acceptance_assets",
        ]
        for requirement_id in expected:
            self.assertIn(requirement_id, requirements)
            self.assertEqual(requirements[requirement_id]["status"], "pass", requirement_id)
            self.assertTrue(requirements[requirement_id]["evidence"], requirement_id)

        self.assertEqual(report["summary"]["fail"], 0)

    def test_completion_audit_writes_report_file(self) -> None:
        root = Path(__file__).parent.parent
        source_dir = root / "knowledge_exports" / "steel_realtime_system_v1"
        output_dir = root / "knowledge_exports" / f"_test_completion_audit_{uuid.uuid4().hex}"
        try:
            shutil.copytree(source_dir, output_dir)

            report = build_completion_audit(output_dir=output_dir, write_report=True)

            report_path = output_dir / "completion_audit_report.json"
            self.assertTrue(report_path.is_file())
            saved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], report["status"])
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
