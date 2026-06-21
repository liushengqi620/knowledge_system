from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from steel_realtime_deployment_package import build_deployment_package


class SteelRealtimeDeploymentPackageTests(unittest.TestCase):
    def test_build_deployment_package_writes_operator_launch_assets(self) -> None:
        root = Path(__file__).parent.parent
        output_dir = root / "knowledge_exports" / "steel_realtime_system_v1"
        package_dir = root / "knowledge_exports" / f"_test_steel_deploy_{uuid.uuid4().hex}"
        try:
            summary = build_deployment_package(output_dir=output_dir, package_dir=package_dir)

            self.assertEqual(summary["status"], "ok")
            expected = [
                "DEPLOYMENT_README.md",
                "start_lightweight_server.ps1",
                "start_fastapi_server.ps1",
                "run_acceptance.ps1",
                "post_sample_event.ps1",
                "environment.example.ps1",
            ]
            for name in expected:
                self.assertTrue((package_dir / name).is_file(), name)

            readme = (package_dir / "DEPLOYMENT_README.md").read_text(encoding="utf-8")
            self.assertIn("钢铁全流程生产异常预警溯源系统", readme)
            self.assertIn("SSE", readme)
            self.assertIn("POST /api/assistant/path-question", readme)
            self.assertIn("连铸段模型分析范围", readme)

            combined = "\n".join(path.read_text(encoding="utf-8") for path in package_dir.glob("*.*"))
            self.assertNotIn("宝钢", combined)
            self.assertIn("steel_realtime_system.py", combined)
            self.assertIn("verify_steel_realtime_system.py", combined)
            self.assertIn("sample_realtime_event.json", combined)
        finally:
            shutil.rmtree(package_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
