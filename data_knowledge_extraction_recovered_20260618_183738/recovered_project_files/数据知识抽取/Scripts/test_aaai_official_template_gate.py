from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aaai_official_template_gate import build_official_template_gate, discover_template_assets, render_markdown


class AaaiOfficialTemplateGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_handle = tempfile.TemporaryDirectory()
        self.tmp_root = Path(self.tmp_handle.name)

    def tearDown(self) -> None:
        self.tmp_handle.cleanup()

    def test_missing_template_blocks_official_migration(self) -> None:
        missing_dir = self.tmp_root / "missing_template"

        report = discover_template_assets([missing_dir], source_probe_path=None)

        self.assertEqual(report["status"], "blocked_missing_official_template")
        self.assertFalse(report["official_template_detected_locally"])
        self.assertEqual(report["style_or_class_files"], [])
        self.assertFalse(report["official_source_blocked"])
        self.assertIn("Place the official AAAI author-kit files", " ".join(report["required_actions"]))
        self.assertIn("Do not describe", report["blocking_rule"])

    def test_source_probe_distinguishes_inaccessible_official_kit(self) -> None:
        probe_path = self.tmp_root / "source_probe.json"
        probe_path.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "output_path": probe_path.as_posix(),
                    "probe_results": [
                        {
                            "url": "https://aaai.org/authorkit27/",
                            "status_code": 403,
                            "content_type": "text/html; charset=UTF-8",
                            "location": "",
                            "error": "Forbidden",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        report = discover_template_assets([self.tmp_root / "missing_template"], source_probe_path=probe_path)

        self.assertEqual(report["status"], "blocked_official_source_inaccessible")
        self.assertTrue(report["official_source_blocked"])
        self.assertIn("retry from a browser", " ".join(report["required_actions"]))

    def test_current_author_kit_success_takes_precedence_over_old_year_failure(self) -> None:
        probe_path = self.tmp_root / "source_probe.json"
        probe_path.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "probe_results": [
                        {
                            "url": "https://aaai.org/authorkit27/",
                            "status_code": 200,
                            "content_type": "application/zip",
                            "location": "",
                            "error": "",
                        },
                        {
                            "url": "https://aaai.org/authorkit26/",
                            "status_code": 404,
                            "content_type": "text/html; charset=UTF-8",
                            "location": "",
                            "error": "Not Found",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        report = discover_template_assets([self.tmp_root / "missing_template"], source_probe_path=probe_path)

        self.assertEqual(report["status"], "blocked_missing_official_template")
        self.assertFalse(report["official_source_blocked"])

    def test_detected_style_file_enables_migration_gate(self) -> None:
        template_dir = self.tmp_root / "template"
        template_dir.mkdir(parents=True)
        (template_dir / "aaai2027.sty").write_text("% official style placeholder for test\n", encoding="utf-8")
        (template_dir / "aaai2027.bst").write_text("% bibliography style placeholder for test\n", encoding="utf-8")
        (template_dir / "aaai2027-sample.tex").write_text("% sample placeholder for test\n", encoding="utf-8")

        report = discover_template_assets([template_dir], source_probe_path=None)

        self.assertEqual(report["status"], "ready_for_official_migration")
        self.assertTrue(report["official_template_detected_locally"])
        self.assertTrue(any(path.endswith("aaai2027.sty") for path in report["style_or_class_files"]))
        self.assertTrue(any(path.endswith("aaai2027.bst") for path in report["bibliography_style_files"]))
        self.assertTrue(any(path.endswith("aaai2027-sample.tex") for path in report["sample_tex_files"]))
        self.assertEqual(report["required_actions"], [])

    def test_render_markdown_contains_gate_summary(self) -> None:
        report = discover_template_assets([self.tmp_root / "missing"], source_probe_path=None)
        markdown = render_markdown(report)

        self.assertIn("# Official AAAI Template Gate", markdown)
        self.assertIn("blocked_missing_official_template", markdown)
        self.assertIn("Scanned Directories", markdown)
        self.assertIn("Official Source Evidence", markdown)
        self.assertIn("Required Actions", markdown)
        self.assertNotIn("sk-", markdown)

    def test_build_official_template_gate_writes_json_and_markdown(self) -> None:
        output_dir = self.tmp_root / "out"

        written = build_official_template_gate(output_dir, [self.tmp_root / "missing"], source_probe_path=None)

        json_path = output_dir / "aaai_official_template_gate.json"
        markdown_path = output_dir / "aaai_official_template_gate.md"
        self.assertEqual(written, [json_path, markdown_path])
        self.assertTrue(json_path.exists())
        self.assertTrue(markdown_path.exists())
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "blocked_missing_official_template")
        self.assertIn("Official AAAI Template Gate", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
