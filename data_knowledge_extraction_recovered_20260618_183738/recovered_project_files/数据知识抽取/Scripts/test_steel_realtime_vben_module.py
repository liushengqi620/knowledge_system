from __future__ import annotations

import json
import unittest
from pathlib import Path


class SteelRealtimeVbenModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).parent.parent
        self.module = self.root / "apps" / "steel-realtime-vben"

    def test_vben_module_files_exist(self) -> None:
        required = [
            "package.json",
            ".env.example",
            "README.md",
            "src/api/steelRealtime.ts",
            "src/types/steelRealtime.ts",
            "src/router/routes.ts",
            "src/views/steel-realtime/index.vue",
            "src/components/ProcessDigitalTwin.vue",
            "src/components/EventStreamPanel.vue",
            "src/components/TraceabilityPathGraph.vue",
        ]

        for rel_path in required:
            self.assertTrue((self.module / rel_path).is_file(), rel_path)

    def test_vben_module_covers_three_level_realtime_contract(self) -> None:
        api = (self.module / "src" / "api" / "steelRealtime.ts").read_text(encoding="utf-8")
        page = (self.module / "src" / "views" / "steel-realtime" / "index.vue").read_text(encoding="utf-8")
        process = (self.module / "src" / "components" / "ProcessDigitalTwin.vue").read_text(encoding="utf-8")
        graph = (self.module / "src" / "components" / "TraceabilityPathGraph.vue").read_text(encoding="utf-8")
        manifest = json.loads(
            (self.root / "knowledge_exports" / "steel_realtime_system_v1" / "api_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        route_paths = {row["path"] for row in manifest["api_routes"]}

        for endpoint in [
            "/api/seed",
            "/api/realtime/next",
            "/risk/events",
            "/identify/events/",
            "/api/events/",
            "/api/trace/events/",
            "/api/recommend/events/",
            "/api/knowledge/search",
            "/api/realtime/ingest",
        ]:
            self.assertIn(endpoint, api)

        self.assertIn("/risk/events", route_paths)
        self.assertIn("/identify/events/{event_id}", route_paths)
        self.assertIn("/api/trace/events/{event_id}", route_paths)
        self.assertIn("钢铁全流程质量异常管控系统", page)
        self.assertIn("生产总览", page)
        self.assertIn("告警台账", page)
        self.assertIn("处置闭环", page)
        self.assertIn("当前重点：连铸段", process)
        self.assertIn("根因溯源链路", graph)
        self.assertIn("TraceabilityPathGraph", page)
        self.assertIn("ingestRealtimeEvent", page)

    def test_vben_module_avoids_specific_company_name(self) -> None:
        forbidden = "宝钢"
        for path in self.module.rglob("*"):
            if path.is_file() and path.suffix in {".ts", ".vue", ".md", ".json", ".example"}:
                self.assertNotIn(forbidden, path.read_text(encoding="utf-8"), str(path))


if __name__ == "__main__":
    unittest.main()
