from __future__ import annotations

import json
import shutil
import threading
import unittest
import urllib.request
import uuid
from pathlib import Path

from steel_realtime_system import _fs_path, build_realtime_system_app, create_realtime_http_server


class SteelRealtimeHttpRuntimeTests(unittest.TestCase):
    def test_lightweight_http_server_serves_realtime_contract(self) -> None:
        root = Path(__file__).parent.parent
        source_dir = root / "knowledge_exports" / "baosteel_three_level_system_v1"
        output_dir = root / "knowledge_exports" / f"_test_steel_http_{uuid.uuid4().hex}"
        server = None
        try:
            build_realtime_system_app(source_dir=source_dir, output_dir=output_dir, max_events=5)
            server = create_realtime_http_server(output_dir, host="127.0.0.1", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            base = f"http://{host}:{port}"

            with urllib.request.urlopen(f"{base}/api/health", timeout=5) as response:
                health = json.loads(response.read().decode("utf-8"))
            self.assertEqual(health["status"], "ok")

            with urllib.request.urlopen(f"{base}/api/realtime/stream?cursor=0&limit=1", timeout=5) as response:
                self.assertIn("text/event-stream", response.headers.get("Content-Type", ""))
                sse = response.read().decode("utf-8")
            self.assertIn("event: steel-event", sse)

            event_id = json.loads((_fs_path(output_dir) / "realtime_seed.json").read_text(encoding="utf-8"))["events"][0]["event_id"]
            body = json.dumps(
                {"event_id": event_id, "question": "解释当前路径", "path_index": 0},
                ensure_ascii=False,
            ).encode("utf-8")
            request = urllib.request.Request(
                f"{base}/api/assistant/path-question",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                answer = json.loads(response.read().decode("utf-8"))
            self.assertEqual(answer["llm_role"], "assistant_only_not_causal_evidence")
            self.assertTrue(answer["answer"])

            ingest_body = json.dumps(
                {"event_id": event_id, "feedback": "现场复核确认，提交知识图谱候选。", "path_index": 0},
                ensure_ascii=False,
            ).encode("utf-8")
            ingest_request = urllib.request.Request(
                f"{base}/api/kg/case-ingest",
                data=ingest_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(ingest_request, timeout=5) as response:
                candidate = json.loads(response.read().decode("utf-8"))
            self.assertEqual(candidate["status"], "candidate_generated")
            self.assertEqual(candidate["merge_policy"], "manual_review_required")
            self.assertGreaterEqual(len(candidate["candidate_entities"]), 4)
            self.assertGreaterEqual(len(candidate["candidate_relations"]), 3)
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
            shutil.rmtree(_fs_path(output_dir), ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
