from __future__ import annotations

import importlib.util
import unittest

from steel_realtime_fastapi import create_app, get_api_route_spec


class SteelRealtimeFastApiTests(unittest.TestCase):
    def test_route_spec_covers_three_level_realtime_system(self) -> None:
        routes = {(row["method"], row["path"]) for row in get_api_route_spec()}

        self.assertIn(("GET", "/risk/events"), routes)
        self.assertIn(("GET", "/identify/events/{event_id}"), routes)
        self.assertIn(("GET", "/api/trace/events/{event_id}"), routes)
        self.assertIn(("GET", "/api/recommend/events/{event_id}"), routes)
        self.assertIn(("GET", "/api/knowledge/search"), routes)
        self.assertIn(("POST", "/api/knowledge/candidates/validate"), routes)
        self.assertIn(("POST", "/api/realtime/ingest"), routes)
        self.assertIn(("GET", "/api/model/cascade/summary"), routes)
        self.assertIn(("GET", "/api/model/cascade/predictions"), routes)
        self.assertIn(("GET", "/api/model/traceability/evidence"), routes)
        self.assertIn(("GET", "/assets/{asset_name}"), routes)

    def test_create_app_reports_missing_fastapi_clearly(self) -> None:
        if importlib.util.find_spec("fastapi") is not None:
            app = create_app(rebuild=False)
            self.assertIsNotNone(app)
            return

        with self.assertRaisesRegex(RuntimeError, "FastAPI is not installed"):
            create_app(rebuild=False)


if __name__ == "__main__":
    unittest.main()
