from __future__ import annotations

import unittest
from pathlib import Path

from verify_steel_realtime_system import build_report


class SteelRealtimeAcceptanceVerifierTests(unittest.TestCase):
    def test_acceptance_report_covers_realtime_system_contract(self) -> None:
        root = Path(__file__).parent.parent
        report = build_report(
            output_dir=root / "knowledge_exports" / "steel_realtime_system_v1",
            source_dir=root / "knowledge_exports" / "baosteel_three_level_system_v1",
        )

        self.assertEqual(report["status"], "pass")
        checks = {row["name"]: row for row in report["checks"]}
        self.assertIn("api manifest covers required routes", checks)
        self.assertIn("HTML supports SSE realtime stream", checks)
        self.assertIn("SSE route emits steel-event", checks)
        self.assertIn("POST realtime ingest returns 200", checks)
        self.assertIn("Vben module supports SSE EventSource", checks)
        self.assertIn("Vben module supports realtime ingest", checks)
        self.assertIn("Vben module includes traceability graph", checks)
        node_check = checks.get("Node/Vben runtime tools available") or checks.get("Node/Vben runtime tools unavailable")
        self.assertIsNotNone(node_check)
        self.assertIn(node_check["status"], {"pass", "warning"})
        self.assertGreater(report["summary"]["pass"], 20)
        self.assertEqual(report["summary"]["fail"], 0)


if __name__ == "__main__":
    unittest.main()
