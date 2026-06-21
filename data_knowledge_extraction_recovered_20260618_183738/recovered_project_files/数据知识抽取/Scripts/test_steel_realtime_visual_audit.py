from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from verify_steel_realtime_visual import build_visual_report


class SteelRealtimeVisualAuditTests(unittest.TestCase):
    def test_visual_audit_covers_process_scope_and_path_interactions(self) -> None:
        root = Path(__file__).parent.parent
        output_dir = root / "knowledge_exports" / "steel_realtime_system_v1"

        report = build_visual_report(output_dir=output_dir)

        self.assertEqual(report["status"], "pass")
        checks = {row["name"]: row for row in report["checks"]}
        expected_checks = [
            "HTML has full-process digital twin section",
            "HTML declares continuous-casting evidence boundary",
            "HTML renders process scope nodes",
            "HTML renders interactive trace path nodes",
            "HTML supports node hover tooltip",
            "HTML supports path click detail",
            "HTML exposes path assistant Q&A",
            "industrial SVG asset is valid",
            "industrial SVG contains multi-stage steel process shapes",
            "industrial SVG uses industrial accent palette",
            "Vben digital twin component declares scope boundary",
            "Vben trace graph component supports path selection",
        ]
        for name in expected_checks:
            self.assertIn(name, checks)
            self.assertEqual(checks[name]["status"], "pass", name)

    def test_visual_audit_writes_report_file(self) -> None:
        root = Path(__file__).parent.parent
        source_dir = root / "knowledge_exports" / "steel_realtime_system_v1"
        output_dir = root / "knowledge_exports" / f"_test_visual_audit_{uuid.uuid4().hex}"
        try:
            shutil.copytree(source_dir, output_dir)

            report = build_visual_report(output_dir=output_dir, write_report=True)

            report_path = output_dir / "visual_acceptance_report.json"
            self.assertTrue(report_path.is_file())
            saved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], report["status"])
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
