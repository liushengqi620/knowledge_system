from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from steel_realtime_system import (
    _fs_path,
    build_realtime_system_app,
    load_realtime_seed,
    response_for_path,
    response_for_post,
)


class SteelRealtimeSystemTests(unittest.TestCase):
    def test_build_realtime_system_app_exports_industrial_realtime_ui(self) -> None:
        root = Path(__file__).parent.parent
        source_dir = root / "knowledge_exports" / "baosteel_three_level_system_v1"
        output_dir = root / "knowledge_exports" / f"_test_steel_realtime_{uuid.uuid4().hex}"
        try:
            summary = build_realtime_system_app(source_dir=source_dir, output_dir=output_dir, max_events=12)
            output_root = _fs_path(output_dir)

            html = (output_root / "index.html").read_text(encoding="utf-8")
            seed = json.loads((output_root / "realtime_seed.json").read_text(encoding="utf-8"))

            self.assertEqual(summary["status"], "ok")
            self.assertTrue(seed["events"])
            self.assertNotIn("宝钢", html)
            self.assertIn("钢铁全流程生产异常预警溯源系统", html)
            self.assertIn("Vben Admin", html)
            self.assertIn("realtime-stream", html)
            self.assertIn("steel-process-map", html)
            self.assertIn("粗炼", html)
            self.assertIn("精炼", html)
            self.assertIn("连铸段模型分析范围", html)
            self.assertIn("ask-path-llm", html)
            self.assertIn("showPathDetail", html)
            self.assertIn("showNodeTooltip", html)
        finally:
            shutil.rmtree(_fs_path(output_dir), ignore_errors=True)

    def test_realtime_api_serves_seed_and_next_event(self) -> None:
        root = Path(__file__).parent.parent
        source_dir = root / "knowledge_exports" / "baosteel_three_level_system_v1"
        output_dir = root / "knowledge_exports" / f"_test_steel_realtime_api_{uuid.uuid4().hex}"
        try:
            build_realtime_system_app(source_dir=source_dir, output_dir=output_dir, max_events=5)
            seed = load_realtime_seed(output_dir)
            status, content_type, payload = response_for_path(output_dir, "/api/realtime/next", "cursor=0")

            self.assertEqual(status, 200)
            self.assertIn("application/json", content_type)
            self.assertEqual(payload["cursor"], 1)
            self.assertEqual(payload["event"]["event_id"], seed["events"][0]["event_id"])
            self.assertIn("process_status", payload["event"])
        finally:
            shutil.rmtree(_fs_path(output_dir), ignore_errors=True)

    def test_quality_code_model_artifact_endpoints(self) -> None:
        root = Path(__file__).parent.parent
        source_dir = root / "knowledge_exports" / "baosteel_three_level_system_v1"
        output_dir = root / "knowledge_exports" / f"_test_quality_model_api_{uuid.uuid4().hex}"
        try:
            build_realtime_system_app(source_dir=source_dir, output_dir=output_dir, max_events=5)

            status, content_type, summary = response_for_path(
                output_dir,
                "/api/model/cascade/summary",
                "",
            )
            self.assertEqual(status, 200)
            self.assertIn("application/json", content_type)
            self.assertEqual(summary["status"], "available")
            self.assertEqual(summary["dataset"]["n_rows"], 80326)
            self.assertIn("binary_test", summary["metrics"])
            self.assertTrue(summary["pipeline"])

            status, content_type, evidence = response_for_path(
                output_dir,
                "/api/model/traceability/evidence",
                "limit=2&only_abnormal=true",
            )
            self.assertEqual(status, 200)
            self.assertIn("application/json", content_type)
            self.assertLessEqual(len(evidence["rows"]), 2)
            self.assertTrue(evidence["rows"])
            self.assertIn("main_label_text", evidence["rows"][0])
        finally:
            shutil.rmtree(_fs_path(output_dir), ignore_errors=True)

    def test_case_ingest_candidate_validation(self) -> None:
        root = Path(__file__).parent.parent
        source_dir = root / "knowledge_exports" / "baosteel_three_level_system_v1"
        output_dir = root / "knowledge_exports" / f"_test_kg_candidate_validation_{uuid.uuid4().hex}"
        try:
            build_realtime_system_app(source_dir=source_dir, output_dir=output_dir, max_events=5)
            seed = load_realtime_seed(output_dir)
            event_id = seed["events"][0]["event_id"]
            status, content_type, candidate = response_for_post(
                output_dir,
                "/api/kg/case-ingest",
                {"event_id": event_id, "path_index": 0, "feedback": "现场确认后形成复盘知识候选。"},
            )
            self.assertEqual(status, 200)
            self.assertIn("application/json", content_type)
            self.assertTrue(candidate["candidate_entities"])

            status, content_type, validation = response_for_post(
                output_dir,
                "/api/knowledge/candidates/validate",
                candidate,
            )
            self.assertEqual(status, 200)
            self.assertIn("application/json", content_type)
            self.assertIn("summary", validation)
            self.assertTrue(validation["entity_results"])
            self.assertIn(validation["status"], {
                "candidate_conflict",
                "candidate_review_required",
                "candidate_duplicate_or_alias",
                "candidate_publish_ready_after_review",
            })
        finally:
            shutil.rmtree(_fs_path(output_dir), ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
